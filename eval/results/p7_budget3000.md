# Eval run: p7_budget3000

- Timestamp: 2026-11-09T16:23:58+05:00
- Config overrides (--set): {'CONTEXT_TOKEN_BUDGET': '3000'}
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 200, 'chunk_overlap': 40, 'max_chunk_tokens': 500, 'written': '2026-11-09T13:26:06+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 33, 'off_desk': 4, 'unanswerable': 4}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 104 ms, p95 209 ms (n=41, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 33 | 1.000 | 0.606 | 0.561 | 1.000 | 0.788 | 0.692 | 1.000 | 0.939 | 0.854 | 0.380 | 0.939 | 0.939 | 0.854 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.125 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| calc | 5 | 1.000 | 0.600 | 0.600 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.445 | 1.000 | 1.000 | 1.000 |
| compare | 3 | 1.000 | 0.000 | 0.000 | 1.000 | 0.667 | 0.333 | 1.000 | 1.000 | 0.500 | 0.103 | 1.000 | 1.000 | 0.667 |
| dev | 20 | 1.000 | 0.650 | 0.600 | 1.000 | 0.700 | 0.650 | 1.000 | 0.900 | 0.875 | 0.351 | 0.900 | 0.900 | 0.850 |
| earnings | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 |
| generated | 13 | 1.000 | 0.538 | 0.500 | 1.000 | 0.923 | 0.756 | 1.000 | 1.000 | 0.821 | 0.426 | 1.000 | 1.000 | 0.859 |
| multi_page | 4 | 1.000 | 0.500 | 0.250 | 1.000 | 0.500 | 0.250 | 1.000 | 0.750 | 0.625 | 0.312 | 0.750 | 0.750 | 0.500 |
| narrative | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.333 | 1.000 | 1.000 | 1.000 |
| statement_table | 9 | 1.000 | 0.333 | 0.278 | 1.000 | 0.889 | 0.648 | 1.000 | 1.000 | 0.741 | 0.300 | 1.000 | 1.000 | 0.796 |
| tune | 13 | 1.000 | 0.538 | 0.500 | 1.000 | 0.923 | 0.756 | 1.000 | 1.000 | 0.821 | 0.426 | 1.000 | 1.000 | 0.859 |
| year_ambiguous | 2 | 1.000 | 0.500 | 0.250 | 1.000 | 1.000 | 0.417 | 1.000 | 1.000 | 0.583 | 0.333 | 1.000 | 1.000 | 0.583 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 25 | 1.000 | 0.600 | 0.540 | 1.000 | 0.800 | 0.673 | 1.000 | 0.920 | 0.807 | 0.364 | 0.920 | 0.920 | 0.807 |
| 10q | 3 | 1.000 | 0.333 | 0.333 | 1.000 | 0.667 | 0.667 | 1.000 | 1.000 | 1.000 | 0.208 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Earnings | 5 | 1.000 | 0.600 | 0.600 | 1.000 | 0.800 | 0.667 | 1.000 | 1.000 | 0.933 | 0.400 | 1.000 | 1.000 | 0.933 |

## Full config

```json
{
 "args": {
  "run_name": "p7_budget3000",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "D:\\Assignment DRG\\index",
  "questions": "eval/questions_v2.jsonl",
  "split": "tune",
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
  "CONTEXT_TOKEN_BUDGET": "3000",
  "DROP_BOILERPLATE": "False",
  "DROP_BOILERPLATE_OVERFETCH": "3",
  "EMBED_BATCH": "64",
  "EMBED_MODEL": "BAAI/bge-small-en-v1.5",
  "FORECAST_PRIOR_YEAR": "False",
  "HASHES_FILE": "hashes.json",
  "HYBRID_BM25": "False",
  "HYBRID_DEPTH": "50",
  "INDEX_DIR": "D:\\Assignment DRG\\index",
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
  "RETRY_UNCITED": "False",
  "RRF_K": "60",
  "YEAR_COMPANY_FILTER": "True"
 },
 "overrides": {
  "CONTEXT_TOKEN_BUDGET": "3000"
 },
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 33,
  "off_desk": 4,
  "unanswerable": 4
 }
}
```
