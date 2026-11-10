"""Tunable settings. Change chunk sizes here to run experiments."""
from pathlib import Path

# Chunking (token counts use the embedding model's tokenizer)
CHUNK_TOKENS = 200  # experiment R1: 350 -> 200 (the index must be rebuilt: ingest into a new --index-dir)
CHUNK_OVERLAP = 40  # was 50 with 350-token chunks
MAX_CHUNK_TOKENS = 500  # hard cap, counted with special tokens

# Embedding
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_BATCH = 64

# Paths (relative to the working directory)
MANIFEST_PATH = Path("manifest.csv")
CACHE_DIR = Path("cache") / "pages"
INDEX_DIR = Path("index")
HASHES_FILE = "hashes.json"  # lives inside INDEX_DIR
INDEX_META_FILE = "index_meta.json"  # how an index was built (e.g. context_header); inside INDEX_DIR
COLLECTION = "chunks"

# Chroma write batch size (its hard limit is ~5k)
CHROMA_BATCH = 2000

# Retrieval
# bge recommends a query instruction for retrieval; empty = embed the question as-is.
QUERY_PREFIX = ""  # OFF (X4 rejected); see EXPERIMENTS.md
# Parse company / year from the question and narrow the Chroma filter (never widens the role filter).
YEAR_COMPANY_FILTER = True  # kept experiment (e2); set False to disable

# Optional cross-encoder reranker. None = off. The reranker only reorders candidates that
# the same Chroma query / where filter already returned (access control is unchanged).
RERANKERS_ALLOWED = ("cross-encoder/ms-marco-MiniLM-L-6-v2", "BAAI/bge-reranker-base")
RERANKER = None  # OFF (e3a-e3c rejected); see EXPERIMENTS.md
RERANK_DEPTH = 50  # candidates fetched and reranked; at least k are always fetched

# Drop retrieved chunks whose stripped text is shorter than this many characters (0 = off).
# MIN_CHUNK_OVERFETCH x the usual candidate count is fetched so k results can still be returned.
MIN_CHUNK_CHARS = 0  # OFF; see EXPERIMENTS.md (no separate run)
MIN_CHUNK_OVERFETCH = 3
# Embed only the sentences that end with "?" or mention a parsed company / year
# (falls back to the whole question). Retrieval only; the original question is untouched.
QUERY_CLEAN = False  # OFF (X3 rejected); see EXPERIMENTS.md
# Drop chunks under 80 characters and chunks from exhibit-index / signature pages
# (drg/boilerplate.py). DROP_BOILERPLATE_OVERFETCH x the usual candidate count is fetched.
DROP_BOILERPLATE = False  # OFF (e4 / e45 no effect); see EXPERIMENTS.md
DROP_BOILERPLATE_OVERFETCH = 3
# When a company has both a 10k and a 10k_annualreport doc for the same period, exclude the
# annual-report doc in the where filter.
PREFER_10K_OVER_ANNUALREPORT = True

# Embed queries with the ONNX export of the embedding model (scripts/export_onnx.py) instead of
# sentence-transformers/torch: identical embeddings (scripts/verify_onnx.py), much faster cold start.
ONNX_ENCODER = True  # kept experiment X9 (identical embeddings; falls back to sentence-transformers if not exported)
ONNX_DIR = Path("models") / "bge-small-en-v1.5-onnx"

# Forward-looking question (expect / forecast / guidance / outlook ...) about year Y with no filing for Y:
# search the filing of Y-1 (where the outlook is published) instead of later filings.
FORECAST_PRIOR_YEAR = False  # OFF (X5 +1, rejected); see EXPERIMENTS.md

# Append formal filing terms for analyst shorthand (capex, R&D, bottom line, headcount, SG&A, ...) to the retrieval
# query (drg/query.py expand_query). Retrieval only; the question sent to the LLM is untouched.
QUERY_EXPAND = True  # kept experiment X2 (financial synonym expansion of the retrieval query)

# Hybrid retrieval: BM25 (drg/bm25.py, persisted in <index_dir>_bm25) over the same role/company/year-filtered
# candidates, fused with the dense ranking by reciprocal rank fusion. Build: python -m drg.bm25 build --index-dir index
HYBRID_BM25 = False  # OFF (X1 rejected); see EXPERIMENTS.md
HYBRID_DEPTH = 50  # candidates taken from each ranker before fusion
RRF_K = 60

# ask
ASK_MAX_CHUNKS_PER_PAGE = 1  # kept experiment X10: at most this many chunks of one (doc, page) in the ask context (0 = off)
RETRY_UNCITED = False  # answered without any valid [C#] marker -> one retry with a citation reminder (experiment X11)  # OFF, unmeasured; see EXPERIMENTS.md (X11)
PROMPT_VERSION = 1  # 4 = v3 + "cannot give the figure -> refused" rule and soft-refusal post-check (unmeasured, OFF). 2 = extended rules on units, calculation inputs and fiscal-period mismatch (experiment X7)  # default 1; 2 and 3 are OFF, unmeasured; see EXPERIMENTS.md (X7, X12)
ASK_K = 14  # chunks given to the LLM (200-token chunks; 8 was right for 350-token chunks: same token volume)
ASK_K_PER_COMPANY = 10  # chunks retrieved for EACH company when a question names 2+ companies (was 6 at 350 tokens)
LLM_TIMEOUT = 30  # seconds
CONTEXT_TOKEN_BUDGET = 4500  # max tokens of retrieved context sent to the LLM (bge tokenizer count, approximate)
# Provider / model come from the environment (.env): LLM_PROVIDER, LLM_MODEL. See .env.example.
