# Eval run: final_holdout_answers_oss20b_rescored4

- Timestamp: 2026-11-09T14:37:26+05:00
- Config overrides (--set): none
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 200, 'chunk_overlap': 40, 'max_chunk_tokens': 500, 'written': '2026-11-09T13:26:06+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 9, 'off_desk': 2, 'unanswerable': 2}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 110 ms, p95 356 ms (n=13, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 9 | 1.000 | 0.444 | 0.306 | 1.000 | 0.778 | 0.528 | 1.000 | 0.778 | 0.583 | 0.405 | 0.889 | 0.889 | 0.639 |

## By split (tune = used for decisions, holdout = first looked at in the final evaluation)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

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

## Answer quality (live LLM {'provider': 'groq', 'model': 'openai/gpt-oss-20b'}; sleep 8.0 s; split holdout)

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | correct_rate | partial_rate | soft_refusal_rate | refused_rate | confident_error_rate | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 13 | 9 | 0.769 | 1.000 | 0.571 | 0.667 | 0.333 | 0.625 | 8 | 0.625 | 0.125 | 0.000 | 0.250 | 0.000 | 0.833 | 0.833 | 3 | 21.460 | 33.606 | 1.450 | 2.254 |
| tune | 13 | 9 | 0.769 | 1.000 | 0.571 | 0.667 | 0.333 | 0.625 | 8 | 0.625 | 0.125 | 0.000 | 0.250 | 0.000 | 0.833 | 0.833 | 3 | 21.460 | 33.606 | 1.450 | 2.254 |

### By question type

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | correct_rate | partial_rate | soft_refusal_rate | refused_rate | confident_error_rate | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| answerable | 9 | 9 | 0.667 | - | 0.000 | 0.667 | 0.333 | 0.625 | 8 | 0.625 | 0.125 | 0.000 | 0.250 | 0.000 | 0.833 | 0.833 | 3 | 21.460 | 35.054 | 1.460 | 2.406 |
| off_desk | 2 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| unanswerable | 2 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | - | - | - | 0 | 24.605 | 25.671 | 1.605 | 1.772 |

### By tag

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | correct_rate | partial_rate | soft_refusal_rate | refused_rate | confident_error_rate | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1 | 0.000 | - | 0.000 | 0.000 | 1.000 | 0.000 | 1 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | - | - | 0 | 25.460 | 25.460 | 1.460 | 1.460 |
| 8k | 1 | 1 | 0.000 | - | 0.000 | 0.000 | 1.000 | - | 0 | - | - | - | - | - | - | - | 0 | 19.710 | 19.710 | 1.710 | 1.710 |
| calc | 3 | 3 | 0.667 | - | 0.000 | 0.667 | 0.333 | 0.667 | 3 | 0.667 | 0.000 | 0.000 | 0.333 | 0.000 | 1.000 | 1.000 | 2 | 1.420 | 23.056 | 1.420 | 1.456 |
| compare | 2 | 2 | 0.500 | - | 0.000 | 0.500 | 0.500 | 0.000 | 2 | 0.000 | 0.500 | 0.000 | 0.500 | 0.000 | 1.000 | 1.000 | 1 | 34.330 | 37.588 | 2.330 | 2.672 |
| generated | 13 | 9 | 0.769 | 1.000 | 0.571 | 0.667 | 0.333 | 0.625 | 8 | 0.625 | 0.125 | 0.000 | 0.250 | 0.000 | 0.833 | 0.833 | 3 | 21.460 | 33.606 | 1.450 | 2.254 |
| holdout | 13 | 9 | 0.769 | 1.000 | 0.571 | 0.667 | 0.333 | 0.625 | 8 | 0.625 | 0.125 | 0.000 | 0.250 | 0.000 | 0.833 | 0.833 | 3 | 21.460 | 33.606 | 1.450 | 2.254 |
| narrative | 1 | 1 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 1 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0 | 21.460 | 21.460 | 1.460 | 1.460 |
| no_filing_for_year | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | - | - | - | 0 | 23.420 | 23.420 | 1.420 | 1.420 |
| nonexistent_segment | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | - | - | - | 0 | 25.790 | 25.790 | 1.790 | 1.790 |
| off_desk | 2 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| statement_table | 7 | 7 | 0.714 | - | 0.000 | 0.714 | 0.286 | 0.571 | 7 | 0.571 | 0.143 | 0.000 | 0.286 | 0.000 | 0.800 | 0.800 | 3 | 24.350 | 35.778 | 1.450 | 2.482 |
| unanswerable | 2 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | - | - | - | 0 | 24.605 | 25.671 | 1.605 | 1.772 |
| year_ambiguous | 1 | 1 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 1 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 24.350 | 24.350 | 1.350 | 1.350 |

### Per question

| id | type | expected | got | numeric_ok | cite_hit | warnings | s |
|---|---|---|---|---|---|---|---:|
| g_s01 | answerable | answered | answered | True | True | 1 | 1.42 |
| g_s03 | answerable | answered | answered | True | True | 1 | 1.23 |
| g_s06 | answerable | answered | answered | True | True | 0 | 21.46 |
| g_s07 | answerable | answered | answered | True | True | 0 | 20.45 |
| g_s10 | answerable | answered | refused | False | None | 0 | 25.46 |
| g_s13 | answerable | answered | refused | None | None | 0 | 19.71 |
| g_l01 | answerable | answered | answered | False | True | 1 | 30.71 |
| g_l02 | answerable | answered | refused | False | None | 0 | 37.95 |
| g_y01 | answerable | answered | answered | True | False | 0 | 24.35 |
| g_o03 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_o04 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_u01 | unanswerable | refused | refused | None | None | 0 | 23.42 |
| g_u04 | unanswerable | refused | refused | None | None | 0 | 25.79 |

### Manual review (answered, no numeric check)

_none_

## Full config

```json
{
 "args": {
  "run_name": "final_holdout_answers_oss20b",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "index_c200",
  "questions": "eval/questions_v2.jsonl",
  "split": "holdout",
  "answers": true
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
