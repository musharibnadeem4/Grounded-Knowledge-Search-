# Eval run: p6_alt_c350_cap1_holdout

- Timestamp: 2026-11-09T14:31:07+05:00
- Config overrides (--set): {'ASK_K': '8', 'ASK_K_PER_COMPANY': '6', 'CHUNK_TOKENS': '350', 'CHUNK_OVERLAP': '50'}
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 350, 'chunk_overlap': 50, 'max_chunk_tokens': 500, 'written': '2026-11-08T18:55:59+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 9, 'off_desk': 2, 'unanswerable': 2}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 78 ms, p95 165 ms (n=13, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.667 | 0.417 | 1.000 | 0.889 | 0.694 | 0.390 | 0.667 | 0.667 | 0.417 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| calc | 3 | 1.000 | 0.333 | 0.167 | 1.000 | 0.667 | 0.333 | 1.000 | 1.000 | 1.000 | 0.122 | 0.667 | 0.667 | 0.333 |
| compare | 2 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 | 0.250 | 1.000 | 0.500 | 0.250 | 0.071 | 0.500 | 0.500 | 0.250 |
| generated | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.667 | 0.417 | 1.000 | 0.889 | 0.694 | 0.390 | 0.667 | 0.667 | 0.417 |
| holdout | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.667 | 0.417 | 1.000 | 0.889 | 0.694 | 0.390 | 0.667 | 0.667 | 0.417 |
| narrative | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.500 | 0.000 | 0.000 | 0.000 | 0.000 |
| statement_table | 7 | 1.000 | 0.429 | 0.250 | 1.000 | 0.714 | 0.393 | 1.000 | 0.857 | 0.679 | 0.359 | 0.714 | 0.714 | 0.393 |
| year_ambiguous | 1 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 1.000 | 0.250 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 7 | 1.000 | 0.429 | 0.250 | 1.000 | 0.714 | 0.393 | 1.000 | 0.857 | 0.607 | 0.359 | 0.714 | 0.714 | 0.393 |
| 10q | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## Full config

```json
{
 "args": {
  "run_name": "p6_alt_c350_cap1_holdout",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "index",
  "questions": "eval/questions_v2.jsonl",
  "split": "holdout",
  "answers": false
 },
 "drg.config": {
  "ASK_K": "8",
  "ASK_K_PER_COMPANY": "6",
  "ASK_MAX_CHUNKS_PER_PAGE": "1",
  "CACHE_DIR": "cache\\pages",
  "CHROMA_BATCH": "2000",
  "CHUNK_OVERLAP": "50",
  "CHUNK_TOKENS": "350",
  "COLLECTION": "chunks",
  "CONTEXT_TOKEN_BUDGET": "4500",
  "DROP_BOILERPLATE": "False",
  "DROP_BOILERPLATE_OVERFETCH": "3",
  "EMBED_BATCH": "64",
  "EMBED_MODEL": "BAAI/bge-small-en-v1.5",
  "FORECAST_PRIOR_YEAR": "False",
  "HASHES_FILE": "hashes.json",
  "HYBRID_BM25": "False",
  "HYBRID_DEPTH": "50",
  "INDEX_DIR": "index",
  "INDEX_META_FILE": "index_meta.json",
  "LLM_TIMEOUT": "30",
  "MANIFEST_PATH": "D:\\Assignment DRG\\manifest.csv",
  "MAX_CHUNK_TOKENS": "500",
  "MIN_CHUNK_CHARS": "0",
  "MIN_CHUNK_OVERFETCH": "3",
  "ONNX_DIR": "models\\bge-small-en-v1.5-onnx",
  "ONNX_ENCODER": "True",
  "PREFER_10K_OVER_ANNUALREPORT": "True",
  "PROMPT_VERSION": "1",
  "QUERY_CLEAN": "False",
  "QUERY_EXPAND": "True",
  "QUERY_PREFIX": "",
  "RERANKER": "None",
  "RERANKERS_ALLOWED": "('cross-encoder/ms-marco-MiniLM-L-6-v2', 'BAAI/bge-reranker-base')",
  "RERANK_DEPTH": "50",
  "RRF_K": "60",
  "YEAR_COMPANY_FILTER": "True"
 },
 "overrides": {
  "ASK_K": "8",
  "ASK_K_PER_COMPANY": "6",
  "CHUNK_TOKENS": "350",
  "CHUNK_OVERLAP": "50"
 },
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 9,
  "off_desk": 2,
  "unanswerable": 2
 }
}
```
