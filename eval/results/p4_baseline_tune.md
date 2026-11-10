# Eval run: p4_baseline_tune

- Timestamp: 2026-11-09T13:05:55+05:00
- Config overrides (--set): none
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 350, 'chunk_overlap': 50, 'max_chunk_tokens': 500, 'written': '2026-11-08T18:55:59+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 33, 'off_desk': 4, 'unanswerable': 4}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 80 ms, p95 156 ms (n=41, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 33 | 1.000 | 0.606 | 0.525 | 1.000 | 0.697 | 0.616 | 1.000 | 0.848 | 0.747 | 0.334 | 0.697 | 0.697 | 0.601 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.250 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| calc | 5 | 1.000 | 0.800 | 0.800 | 1.000 | 0.800 | 0.800 | 1.000 | 1.000 | 1.000 | 0.400 | 0.800 | 0.800 | 0.800 |
| compare | 3 | 1.000 | 0.333 | 0.167 | 1.000 | 0.333 | 0.167 | 1.000 | 0.667 | 0.333 | 0.167 | 0.667 | 0.667 | 0.333 |
| dev | 20 | 1.000 | 0.550 | 0.500 | 1.000 | 0.700 | 0.650 | 1.000 | 0.850 | 0.792 | 0.304 | 0.650 | 0.650 | 0.600 |
| earnings | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 |
| generated | 13 | 1.000 | 0.692 | 0.564 | 1.000 | 0.692 | 0.564 | 1.000 | 0.846 | 0.679 | 0.381 | 0.769 | 0.769 | 0.603 |
| multi_page | 4 | 1.000 | 0.500 | 0.250 | 1.000 | 0.500 | 0.250 | 1.000 | 0.750 | 0.458 | 0.188 | 0.500 | 0.500 | 0.250 |
| narrative | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| statement_table | 9 | 1.000 | 0.667 | 0.481 | 1.000 | 0.667 | 0.481 | 1.000 | 0.889 | 0.648 | 0.272 | 0.778 | 0.778 | 0.537 |
| tune | 13 | 1.000 | 0.692 | 0.564 | 1.000 | 0.692 | 0.564 | 1.000 | 0.846 | 0.679 | 0.381 | 0.769 | 0.769 | 0.603 |
| year_ambiguous | 2 | 1.000 | 1.000 | 0.417 | 1.000 | 1.000 | 0.417 | 1.000 | 1.000 | 0.417 | 0.625 | 1.000 | 1.000 | 0.417 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 25 | 1.000 | 0.520 | 0.413 | 1.000 | 0.600 | 0.493 | 1.000 | 0.800 | 0.667 | 0.268 | 0.600 | 0.600 | 0.473 |
| 10q | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.483 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Earnings | 5 | 1.000 | 0.800 | 0.667 | 1.000 | 1.000 | 0.867 | 1.000 | 1.000 | 0.867 | 0.425 | 1.000 | 1.000 | 0.867 |

## Full config

```json
{
 "args": {
  "run_name": "p4_baseline_tune",
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
  "HASHES_FILE": "hashes.json",
  "INDEX_DIR": "D:\\Assignment DRG\\index",
  "INDEX_META_FILE": "index_meta.json",
  "LLM_TIMEOUT": "30",
  "MANIFEST_PATH": "D:\\Assignment DRG\\manifest.csv",
  "MAX_CHUNK_TOKENS": "500",
  "MIN_CHUNK_CHARS": "0",
  "MIN_CHUNK_OVERFETCH": "3",
  "PREFER_10K_OVER_ANNUALREPORT": "True",
  "QUERY_CLEAN": "False",
  "QUERY_PREFIX": "",
  "RERANKER": "None",
  "RERANKERS_ALLOWED": "('cross-encoder/ms-marco-MiniLM-L-6-v2', 'BAAI/bge-reranker-base')",
  "RERANK_DEPTH": "50",
  "YEAR_COMPANY_FILTER": "True"
 },
 "overrides": {},
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 33,
  "off_desk": 4,
  "unanswerable": 4
 }
}
```
