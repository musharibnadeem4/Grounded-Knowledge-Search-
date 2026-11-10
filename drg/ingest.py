"""ingest <corpus_dir>: parse manifest-listed PDFs, chunk within pages, embed, store in Chroma.

Everything informational goes to stderr; stdout stays empty.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from . import config


def log(msg):
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------- manifest
def read_manifest(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    return {r["doc_id"]: r for r in rows}


def match_files(corpus_dir, manifest):
    """Return ({doc_id: Path}, [skipped Path]). Case-insensitive match on the
    file stem; the manifest's doc_id spelling is always the one used."""
    by_lower = {}
    for p in sorted(Path(corpus_dir).glob("*.pdf")):
        by_lower.setdefault(p.stem.lower(), []).append(p)
    matched, used = {}, set()
    for doc_id in manifest:
        cands = by_lower.get(doc_id.lower(), [])
        if len(cands) == 1:
            matched[doc_id] = cands[0]
            used.add(cands[0])
        elif len(cands) > 1:
            log(f"WARN ambiguous case-insensitive match for {doc_id}: "
                f"{[c.name for c in cands]}; not ingesting")
        else:
            log(f"WARN manifest doc_id {doc_id} has no PDF")
    skipped = [p for ps in by_lower.values() for p in ps if p not in used]
    return matched, skipped


# ------------------------------------------------------------------------ parse
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cache_path(cache_dir, doc_id):
    return Path(cache_dir) / f"{doc_id}.jsonl"


def read_cache(cache_dir, doc_id, sha):
    """Return list of page texts if a cache with this sha256 exists, else None."""
    p = cache_path(cache_dir, doc_id)
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            meta = json.loads(f.readline())
            if meta.get("sha256") != sha:
                return None
            pages = [json.loads(line)["text"] for line in f if line.strip()]
        return pages if len(pages) == meta.get("n_pages") else None
    except (OSError, ValueError, KeyError):
        return None


def write_cache(cache_dir, doc_id, sha, pages):
    p = cache_path(cache_dir, doc_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps({"doc_id": doc_id, "sha256": sha, "n_pages": len(pages)}) + "\n")
        for i, t in enumerate(pages, 1):  # page = 1-based PDF index
            f.write(json.dumps({"page": i, "text": t}, ensure_ascii=False) + "\n")
    os.replace(tmp, p)


def parse_pdf(args):
    """Worker (top-level so it pickles on Windows): returns (doc_id, pages)."""
    doc_id, pdf_path = args
    import pdfplumber

    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception as e:  # keep the page slot so numbering stays right
                print(f"WARN {doc_id}: extract failed on page {len(pages) + 1}: {e}",
                      file=sys.stderr)
                pages.append("")
    return doc_id, pages


# ------------------------------------------------------------------------ chunk
_BOILERPLATE = re.compile(r"^\s*(table of contents|index)\s*$", re.I)


def clean_page(text):
    """Drop leading 'Table of Contents' / 'Index' lines.
    Returns (body_text, page_header); header = first two non-empty lines."""
    lines = text.splitlines()
    while True:
        i = next((k for k, l in enumerate(lines) if l.strip()), None)
        if i is not None and _BOILERPLATE.match(lines[i]):
            lines = lines[i + 1:]
        else:
            break
    body = "\n".join(lines).strip()
    header = "\n".join([l.strip() for l in lines if l.strip()][:2])
    return body, header


def load_tokenizer():
    from . import hf

    hf.prefer_offline(config.EMBED_MODEL)  # must precede the transformers import
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(config.EMBED_MODEL)
    tok.model_max_length = 10**9  # we window ourselves; silence length warning
    return tok


def chunk_text(text, tok, size=None, overlap=None, max_tokens=None):
    """Split one page into token windows. Returns list of chunk strings."""
    size = size or config.CHUNK_TOKENS
    overlap = config.CHUNK_OVERLAP if overlap is None else overlap
    max_tokens = max_tokens or config.MAX_CHUNK_TOKENS
    assert 0 <= overlap < size <= max_tokens
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    offs = enc["offset_mapping"]
    n = len(offs)
    out, start = [], 0
    while n:
        end = min(start + size, n)
        chunk = text[offs[start][0]:offs[end - 1][1]].strip()
        if chunk:
            n_tok = len(tok(chunk)["input_ids"])  # includes [CLS]/[SEP]
            assert n_tok <= max_tokens, f"chunk of {n_tok} tokens exceeds {max_tokens}"
            out.append(chunk)
        if end == n:
            break
        start = end - overlap
    return out


def chunk_id(doc_id, page, idx):
    return hashlib.sha1(f"{doc_id}|{page}|{idx}".encode("utf-8")).hexdigest()[:16]


def build_chunks(doc_id, row, pages, tok):
    ids, docs, metas = [], [], []
    for page_no, raw in enumerate(pages, 1):
        body, header = clean_page(raw)
        for idx, text in enumerate(chunk_text(body, tok)):
            cid = chunk_id(doc_id, page_no, idx)
            ids.append(cid)
            docs.append(text)
            metas.append({
                "doc_id": doc_id,
                "company": row.get("company", ""),
                "desk": row.get("desk", ""),
                "doc_type": row.get("doc_type", ""),
                "period": row.get("period", ""),
                "page": page_no,
                "page_header": header,
                "chunk_id": cid,
            })
    return ids, docs, metas


# ------------------------------------------------------------------------ index
def open_collection(index_dir):
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(index_dir), settings=Settings(anonymized_telemetry=False))
    return client.get_or_create_collection(
        config.COLLECTION, metadata={"hnsw:space": "cosine"})


def load_hashes(index_dir):
    p = Path(index_dir) / config.HASHES_FILE
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            log(f"WARN {p} unreadable; treating all docs as changed")
    return {}


def save_hashes(index_dir, hashes):
    p = Path(index_dir) / config.HASHES_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(hashes, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, p)


# ------------------------------------------------------------- context header (E1)
def context_prefix(meta):
    """Text prepended to a chunk before embedding when ingesting with --context-header."""
    return (f"{meta['company']} | {meta['doc_type']} | FY{meta['period']} | "
            f"p.{meta['page']} | {meta['page_header']}\n")


def embed_inputs(docs, metas, context_header):
    """The texts that get embedded. The stored document stays the original chunk text."""
    if not context_header:
        return list(docs)
    return [context_prefix(m) + d for d, m in zip(docs, metas)]


def read_index_meta(index_dir):
    """index_meta.json of an index, or None (indexes built before it existed)."""
    p = Path(index_dir) / config.INDEX_META_FILE
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return None
    return None


def write_index_meta(index_dir, context_header):
    import datetime as dt

    p = Path(index_dir) / config.INDEX_META_FILE
    meta = {"context_header": bool(context_header), "embed_model": config.EMBED_MODEL,
            "chunk_tokens": config.CHUNK_TOKENS, "chunk_overlap": config.CHUNK_OVERLAP,
            "max_chunk_tokens": config.MAX_CHUNK_TOKENS,
            "written": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    os.replace(tmp, p)


# ------------------------------------------------------------------------- main
def ingest(corpus_dir, manifest_path=None, cache_dir=None, index_dir=None, workers=None,
           context_header=True):
    manifest_path = Path(manifest_path or config.MANIFEST_PATH)
    cache_dir = Path(cache_dir or config.CACHE_DIR)
    index_dir = Path(index_dir or config.INDEX_DIR)
    # never mix chunk styles in one index
    existing = read_index_meta(index_dir)
    was_ch = existing["context_header"] if existing else False
    if (index_dir / config.HASHES_FILE).exists() and was_ch != bool(context_header):
        sys.exit(f"ingest: {index_dir} was built with context_header={was_ch}; refusing to add "
                 f"context_header={bool(context_header)} chunks to it. Use a new --index-dir.")
    t = {"parse": 0.0, "chunk": 0.0, "embed": 0.0, "write": 0.0}

    manifest = read_manifest(manifest_path)
    matched, skipped = match_files(corpus_dir, manifest)
    for p in skipped:
        log(f"SKIP unlisted PDF (not indexed): {p.name}")

    index_dir.mkdir(parents=True, exist_ok=True)
    hashes = load_hashes(index_dir)
    shas = {d: sha256_file(p) for d, p in matched.items()}
    todo = [d for d in matched if hashes.get(d) != shas[d]]
    unchanged = len(matched) - len(todo)
    log(f"{len(matched)} listed PDFs found, {unchanged} unchanged (skipped), "
        f"{len(todo)} to ingest, {len(skipped)} unlisted skipped")
    if not todo:
        log("nothing to do")
        return 0
    write_index_meta(index_dir, context_header)
    if context_header:
        log("context header ON: embedding '{company} | {doc_type} | FY{period} | p.{page} | "
            "{page_header}' + chunk; stored text stays the original")

    # parse (cache first, then the rest in parallel)
    t0 = time.perf_counter()
    parsed, to_parse = {}, []
    for d in todo:
        pages = read_cache(cache_dir, d, shas[d])
        if pages is None:
            to_parse.append(d)
        else:
            parsed[d] = pages
    log(f"parse: {len(parsed)} from cache, {len(to_parse)} to parse")
    if to_parse:
        workers = workers or min(len(to_parse), os.cpu_count() or 1)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(parse_pdf, (d, str(matched[d]))): d for d in to_parse}
            for n, fut in enumerate(as_completed(futs), 1):
                d = futs[fut]
                try:
                    _, pages = fut.result()
                except Exception as e:
                    log(f"ERROR parsing {d}: {e}; not ingesting")
                    continue
                write_cache(cache_dir, d, shas[d], pages)
                parsed[d] = pages
                log(f"  parsed {d} ({len(pages)} pages) [{n}/{len(to_parse)}]")
    t["parse"] = time.perf_counter() - t0

    # models / index
    tok = load_tokenizer()
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.EMBED_MODEL)
    coll = open_collection(index_dir)

    n_docs = n_pages = n_chunks = 0
    for d in todo:
        if d not in parsed:
            continue
        pages = parsed[d]

        t0 = time.perf_counter()
        ids, docs, metas = build_chunks(d, manifest[d], pages, tok)
        t["chunk"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        embs = (model.encode(embed_inputs(docs, metas, context_header),
                             batch_size=config.EMBED_BATCH,
                             normalize_embeddings=True, show_progress_bar=True,
                             convert_to_numpy=True).tolist() if docs else [])
        t["embed"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        coll.delete(where={"doc_id": d})  # no-op for a new doc
        step = config.CHROMA_BATCH
        for i in range(0, len(ids), step):
            coll.add(ids=ids[i:i + step], documents=docs[i:i + step],
                     embeddings=embs[i:i + step], metadatas=metas[i:i + step])
        hashes[d] = shas[d]
        save_hashes(index_dir, hashes)
        t["write"] += time.perf_counter() - t0

        n_docs += 1
        n_pages += len(pages)
        n_chunks += len(ids)
        log(f"ingested {d}: {len(pages)} pages, {len(ids)} chunks")

    log(f"DONE docs={n_docs} pages={n_pages} chunks={n_chunks}")
    log("elapsed s: " + " ".join(f"{k}={v:.1f}" for k, v in t.items()))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ingest", description=__doc__)
    ap.add_argument("corpus_dir")
    ap.add_argument("--manifest", default=str(config.MANIFEST_PATH))
    ap.add_argument("--cache-dir", default=str(config.CACHE_DIR))
    ap.add_argument("--index-dir", default=str(config.INDEX_DIR))
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--context-header", dest="context_header", action="store_true", default=True,
                    help="(default) embed '{company} | {doc_type} | FY{period} | p.{page} | "
                         "{page_header}' + chunk text (stored text unchanged)")
    ap.add_argument("--no-context-header", dest="context_header", action="store_false",
                    help="embed the plain chunk text only")
    a = ap.parse_args(argv)
    rc = ingest(a.corpus_dir, a.manifest, a.cache_dir, a.index_dir, a.workers,
                context_header=a.context_header)
    if rc == 0 and config.ONNX_ENCODER:
        # queries use the ONNX encoder (config.ONNX_ENCODER); build it now if this machine does not have it yet.
        # Failure only warns: retrieval falls back to sentence-transformers.
        from . import onnx_export
        onnx_export.ensure_onnx()
    return rc


if __name__ == "__main__":
    sys.exit(main())
