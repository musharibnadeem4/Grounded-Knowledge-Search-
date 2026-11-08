# Eval run: e3b_rerank_bge

- Timestamp: 2026-11-08T17:48:09+05:00
- Config overrides (--set): {'YEAR_COMPANY_FILTER': 'True', 'RERANKER': "'BAAI/bge-reranker-base'"}
- Git SHA: c87785e3b8366f57a6d2a3a99d9c1c62ced571f4 (dirty)
- Question types: {'answerable': 20}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 11848 ms, p95 31752 ms (n=20, retrieval depth 20, model load excluded)
- Rerank latency (included in the above): p50 11732 ms, p95 31417 ms

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 20 | 1.000 | 0.300 | 0.275 | 1.000 | 0.450 | 0.425 | 1.000 | 0.650 | 0.600 | 0.279 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| multi_page | 4 | 1.000 | 0.250 | 0.125 | 1.000 | 0.250 | 0.125 | 1.000 | 0.500 | 0.250 | 0.050 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 16 | 1.000 | 0.312 | 0.281 | 1.000 | 0.438 | 0.406 | 1.000 | 0.688 | 0.625 | 0.279 |
| 10q | 2 | 1.000 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.556 |
| Earnings | 2 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |

## Full config

```json
{
 "args": {
  "run_name": "e3b_rerank_bge",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "D:\\Assignment DRG\\index",
  "questions": "D:\\Assignment DRG\\eval\\questions.jsonl"
 },
 "drg.config": {
  "CACHE_DIR": "cache\\pages",
  "CHROMA_BATCH": "2000",
  "CHUNK_OVERLAP": "50",
  "CHUNK_TOKENS": "350",
  "COLLECTION": "chunks",
  "EMBED_BATCH": "64",
  "EMBED_MODEL": "BAAI/bge-small-en-v1.5",
  "HASHES_FILE": "hashes.json",
  "INDEX_DIR": "D:\\Assignment DRG\\index",
  "MANIFEST_PATH": "D:\\Assignment DRG\\manifest.csv",
  "MAX_CHUNK_TOKENS": "500",
  "QUERY_PREFIX": "",
  "RERANKER": "BAAI/bge-reranker-base",
  "RERANKERS_ALLOWED": "('cross-encoder/ms-marco-MiniLM-L-6-v2', 'BAAI/bge-reranker-base')",
  "RERANK_DEPTH": "50",
  "YEAR_COMPANY_FILTER": "True"
 },
 "overrides": {
  "YEAR_COMPANY_FILTER": "True",
  "RERANKER": "'BAAI/bge-reranker-base'"
 },
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 20
 }
}
```
