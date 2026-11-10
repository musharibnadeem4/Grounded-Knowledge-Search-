# Eval run: final_holdout

- Timestamp: 2026-11-09T14:30:54+05:00
- Config overrides (--set): none
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 200, 'chunk_overlap': 40, 'max_chunk_tokens': 500, 'written': '2026-11-09T13:26:06+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 9, 'off_desk': 2, 'unanswerable': 2}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 99 ms, p95 210 ms (n=13, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.778 | 0.528 | 1.000 | 0.778 | 0.583 | 0.405 | 0.889 | 0.889 | 0.639 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| calc | 3 | 1.000 | 0.000 | 0.000 | 1.000 | 0.667 | 0.500 | 1.000 | 0.667 | 0.667 | 0.097 | 0.667 | 0.667 | 0.667 |
| compare | 2 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 | 0.250 | 1.000 | 0.500 | 0.250 | 0.050 | 1.000 | 1.000 | 0.500 |
| generated | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.778 | 0.528 | 1.000 | 0.778 | 0.583 | 0.405 | 0.889 | 0.889 | 0.639 |
| holdout | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.778 | 0.528 | 1.000 | 0.778 | 0.583 | 0.405 | 0.889 | 0.889 | 0.639 |
| narrative | 1 | 1.000 | 1.000 | 0.500 | 1.000 | 1.000 | 0.500 | 1.000 | 1.000 | 0.500 | 0.250 | 1.000 | 1.000 | 0.500 |
| statement_table | 7 | 1.000 | 0.286 | 0.179 | 1.000 | 0.714 | 0.464 | 1.000 | 0.714 | 0.536 | 0.342 | 0.857 | 0.857 | 0.607 |
| year_ambiguous | 1 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 1.000 | 0.250 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 7 | 1.000 | 0.429 | 0.250 | 1.000 | 0.857 | 0.536 | 1.000 | 0.857 | 0.607 | 0.377 | 1.000 | 1.000 | 0.679 |
| 10q | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## Full config

```json
{
 "args": {
  "run_name": "final_holdout",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "index_c200",
  "questions": "eval/questions_v2.jsonl",
  "split": "holdout",
  "answers": false
 },
 "drg.config": {
  "ASK_K": "14",
  "ASK_K_PER_COMPANY": "10",
  "ASK_MAX_CHUNKS_PER_PAGE": "1",
  "CACHE_DIR": "cache\\pages",
  "CHROMA_BATCH": "2000",
  "CHUNK_OVERLAP": "40",
  "CHUNK_TOKENS": "200",
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
  "INDEX_DIR": "index_c200",
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
 "overrides": {},
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 9,
  "off_desk": 2,
  "unanswerable": 2
 }
}
```
