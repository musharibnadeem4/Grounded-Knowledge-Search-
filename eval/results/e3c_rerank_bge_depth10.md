# Eval run: e3c_rerank_bge_depth10

- Timestamp: 2026-11-08T17:51:43+05:00
- Config overrides (--set): {'YEAR_COMPANY_FILTER': 'True', 'RERANKER': "'BAAI/bge-reranker-base'", 'RERANK_DEPTH': '10'}
- Git SHA: c87785e3b8366f57a6d2a3a99d9c1c62ced571f4 (dirty)
- Question types: {'answerable': 20}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 4864 ms, p95 6214 ms (n=20, retrieval depth 20, model load excluded)
- Rerank latency (included in the above): p50 4760 ms, p95 5954 ms

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 20 | 1.000 | 0.350 | 0.325 | 1.000 | 0.550 | 0.525 | 1.000 | 0.700 | 0.675 | 0.300 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| multi_page | 4 | 1.000 | 0.250 | 0.125 | 1.000 | 0.250 | 0.125 | 1.000 | 0.500 | 0.375 | 0.050 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 16 | 1.000 | 0.375 | 0.344 | 1.000 | 0.562 | 0.531 | 1.000 | 0.688 | 0.656 | 0.304 |
| 10q | 2 | 1.000 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.571 |
| Earnings | 2 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 | 0.500 | 0.000 |

## Full config

```json
{
 "args": {
  "run_name": "e3c_rerank_bge_depth10",
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
  "RERANK_DEPTH": "10",
  "YEAR_COMPANY_FILTER": "True"
 },
 "overrides": {
  "YEAR_COMPANY_FILTER": "True",
  "RERANKER": "'BAAI/bge-reranker-base'",
  "RERANK_DEPTH": "10"
 },
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 20
 }
}
```
