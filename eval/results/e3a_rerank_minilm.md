# Eval run: e3a_rerank_minilm

- Timestamp: 2026-11-08T17:37:48+05:00
- Config overrides (--set): {'YEAR_COMPANY_FILTER': 'True', 'RERANKER': "'cross-encoder/ms-marco-MiniLM-L-6-v2'"}
- Git SHA: c87785e3b8366f57a6d2a3a99d9c1c62ced571f4 (dirty)
- Question types: {'answerable': 20}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 1399 ms, p95 1952 ms (n=20, retrieval depth 20, model load excluded)
- Rerank latency (included in the above): p50 1304 ms, p95 1680 ms

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 20 | 0.950 | 0.500 | 0.500 | 1.000 | 0.500 | 0.500 | 1.000 | 0.650 | 0.625 | 0.283 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| multi_page | 4 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 | 0.375 | 0.000 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 16 | 1.000 | 0.500 | 0.500 | 1.000 | 0.500 | 0.500 | 1.000 | 0.688 | 0.656 | 0.271 |
| 10q | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.667 |
| Earnings | 2 | 0.500 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |

## Full config

```json
{
 "args": {
  "run_name": "e3a_rerank_minilm",
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
  "RERANKER": "cross-encoder/ms-marco-MiniLM-L-6-v2",
  "RERANKERS_ALLOWED": "('cross-encoder/ms-marco-MiniLM-L-6-v2', 'BAAI/bge-reranker-base')",
  "RERANK_DEPTH": "50",
  "YEAR_COMPANY_FILTER": "True"
 },
 "overrides": {
  "YEAR_COMPANY_FILTER": "True",
  "RERANKER": "'cross-encoder/ms-marco-MiniLM-L-6-v2'"
 },
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 20
 }
}
```
