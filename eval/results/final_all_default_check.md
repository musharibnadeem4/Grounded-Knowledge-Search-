# Eval run: final_all_default_check

- Timestamp: 2026-11-10T09:27:50+05:00
- Config overrides (--set): none
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 200, 'chunk_overlap': 40, 'max_chunk_tokens': 500, 'written': '2026-11-09T13:26:06+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 42, 'off_desk': 6, 'unanswerable': 6}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 985 ms, p95 1483 ms (n=54, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 42 | 1.000 | 0.571 | 0.506 | 1.000 | 0.786 | 0.657 | 1.000 | 0.905 | 0.796 | 0.386 | 0.929 | 0.929 | 0.819 |

## By split (tune = used for decisions, holdout = first looked at in the final evaluation)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| holdout | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.778 | 0.528 | 1.000 | 0.778 | 0.583 | 0.405 | 0.889 | 0.889 | 0.639 |
| tune | 33 | 1.000 | 0.606 | 0.561 | 1.000 | 0.788 | 0.692 | 1.000 | 0.939 | 0.854 | 0.380 | 0.939 | 0.939 | 0.869 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 2 | 1.000 | 0.000 | 0.000 | 1.000 | 0.500 | 0.500 | 1.000 | 0.500 | 0.500 | 0.062 | 0.500 | 0.500 | 0.500 |
| 8k | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| calc | 8 | 1.000 | 0.375 | 0.375 | 1.000 | 0.875 | 0.812 | 1.000 | 0.875 | 0.875 | 0.315 | 0.875 | 0.875 | 0.875 |
| compare | 5 | 1.000 | 0.000 | 0.000 | 1.000 | 0.600 | 0.300 | 1.000 | 0.800 | 0.400 | 0.082 | 1.000 | 1.000 | 0.600 |
| dev | 20 | 1.000 | 0.650 | 0.600 | 1.000 | 0.700 | 0.650 | 1.000 | 0.900 | 0.875 | 0.351 | 0.900 | 0.900 | 0.875 |
| earnings | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 |
| generated | 22 | 1.000 | 0.500 | 0.420 | 1.000 | 0.864 | 0.663 | 1.000 | 0.909 | 0.723 | 0.417 | 0.955 | 0.955 | 0.769 |
| holdout | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.778 | 0.528 | 1.000 | 0.778 | 0.583 | 0.405 | 0.889 | 0.889 | 0.639 |
| multi_page | 4 | 1.000 | 0.500 | 0.250 | 1.000 | 0.500 | 0.250 | 1.000 | 0.750 | 0.625 | 0.312 | 0.750 | 0.750 | 0.625 |
| narrative | 2 | 1.000 | 1.000 | 0.750 | 1.000 | 1.000 | 0.750 | 1.000 | 1.000 | 0.750 | 0.292 | 1.000 | 1.000 | 0.750 |
| statement_table | 16 | 1.000 | 0.312 | 0.234 | 1.000 | 0.812 | 0.568 | 1.000 | 0.875 | 0.651 | 0.318 | 0.938 | 0.938 | 0.714 |
| tune | 13 | 1.000 | 0.538 | 0.500 | 1.000 | 0.923 | 0.756 | 1.000 | 1.000 | 0.821 | 0.426 | 1.000 | 1.000 | 0.859 |
| year_ambiguous | 3 | 1.000 | 0.667 | 0.250 | 1.000 | 1.000 | 0.361 | 1.000 | 1.000 | 0.472 | 0.556 | 1.000 | 1.000 | 0.472 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 32 | 1.000 | 0.562 | 0.477 | 1.000 | 0.812 | 0.643 | 1.000 | 0.906 | 0.763 | 0.367 | 0.938 | 0.938 | 0.794 |
| 10q | 4 | 1.000 | 0.250 | 0.250 | 1.000 | 0.500 | 0.500 | 1.000 | 0.750 | 0.750 | 0.156 | 0.750 | 0.750 | 0.750 |
| 8k | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Earnings | 5 | 1.000 | 0.600 | 0.600 | 1.000 | 0.800 | 0.667 | 1.000 | 1.000 | 0.933 | 0.400 | 1.000 | 1.000 | 0.933 |

## Full config

```json
{
 "args": {
  "run_name": "final_all_default_check",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "D:\\Assignment DRG\\index",
  "questions": "D:\\Assignment DRG\\eval\\questions_v2.jsonl",
  "split": "all",
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
 "overrides": {},
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 42,
  "off_desk": 6,
  "unanswerable": 6
 }
}
```
