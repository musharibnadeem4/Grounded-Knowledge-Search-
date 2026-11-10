# Eval run: p5_x5_forecast

- Timestamp: 2026-11-09T13:18:05+05:00
- Config overrides (--set): {'QUERY_EXPAND': 'True', 'FORECAST_PRIOR_YEAR': 'True'}
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 350, 'chunk_overlap': 50, 'max_chunk_tokens': 500, 'written': '2026-11-08T18:55:59+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 33, 'off_desk': 4, 'unanswerable': 4}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 83 ms, p95 169 ms (n=41, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 33 | 1.000 | 0.788 | 0.677 | 1.000 | 0.879 | 0.753 | 1.000 | 0.939 | 0.833 | 0.438 | 0.848 | 0.848 | 0.753 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| calc | 5 | 1.000 | 0.800 | 0.800 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.442 | 1.000 | 1.000 | 1.000 |
| compare | 3 | 1.000 | 1.000 | 0.500 | 1.000 | 1.000 | 0.500 | 1.000 | 1.000 | 0.667 | 0.344 | 1.000 | 1.000 | 0.667 |
| dev | 20 | 1.000 | 0.750 | 0.700 | 1.000 | 0.850 | 0.775 | 1.000 | 0.950 | 0.867 | 0.401 | 0.800 | 0.800 | 0.750 |
| earnings | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 |
| generated | 13 | 1.000 | 0.846 | 0.641 | 1.000 | 0.923 | 0.718 | 1.000 | 0.923 | 0.782 | 0.496 | 0.923 | 0.923 | 0.756 |
| multi_page | 4 | 1.000 | 0.500 | 0.250 | 1.000 | 0.750 | 0.375 | 1.000 | 1.000 | 0.583 | 0.275 | 0.500 | 0.500 | 0.250 |
| narrative | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| statement_table | 9 | 1.000 | 0.889 | 0.593 | 1.000 | 1.000 | 0.704 | 1.000 | 1.000 | 0.796 | 0.438 | 1.000 | 1.000 | 0.759 |
| tune | 13 | 1.000 | 0.846 | 0.641 | 1.000 | 0.923 | 0.718 | 1.000 | 0.923 | 0.782 | 0.496 | 0.923 | 0.923 | 0.756 |
| year_ambiguous | 2 | 1.000 | 1.000 | 0.417 | 1.000 | 1.000 | 0.417 | 1.000 | 1.000 | 0.583 | 0.600 | 1.000 | 1.000 | 0.417 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 25 | 1.000 | 0.760 | 0.613 | 1.000 | 0.840 | 0.673 | 1.000 | 0.920 | 0.780 | 0.406 | 0.800 | 0.800 | 0.673 |
| 10q | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.483 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Earnings | 5 | 1.000 | 0.800 | 0.667 | 1.000 | 1.000 | 0.867 | 1.000 | 1.000 | 0.933 | 0.415 | 1.000 | 1.000 | 0.867 |

## Full config

```json
{
 "args": {
  "run_name": "p5_x5_forecast",
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
  "ASK_K": "8",
  "ASK_K_PER_COMPANY": "6",
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
  "FORECAST_PRIOR_YEAR": "True",
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
  "PREFER_10K_OVER_ANNUALREPORT": "True",
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
  "QUERY_EXPAND": "True",
  "FORECAST_PRIOR_YEAR": "True"
 },
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 33,
  "off_desk": 4,
  "unanswerable": 4
 }
}
```
