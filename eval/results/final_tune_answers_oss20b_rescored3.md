# Eval run: final_tune_answers_oss20b_rescored3

- Timestamp: 2026-11-09T15:15:01+05:00
- Config overrides (--set): none
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 200, 'chunk_overlap': 40, 'max_chunk_tokens': 500, 'written': '2026-11-09T13:26:06+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 33, 'off_desk': 4, 'unanswerable': 4}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 110 ms, p95 204 ms (n=41, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 33 | 1.000 | 0.606 | 0.561 | 1.000 | 0.788 | 0.692 | 1.000 | 0.939 | 0.854 | 0.380 | 0.939 | 0.939 | 0.869 |

## By split (tune = used for decisions, holdout = first looked at in the final evaluation)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.125 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| calc | 5 | 1.000 | 0.600 | 0.600 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.445 | 1.000 | 1.000 | 1.000 |
| compare | 3 | 1.000 | 0.000 | 0.000 | 1.000 | 0.667 | 0.333 | 1.000 | 1.000 | 0.500 | 0.103 | 1.000 | 1.000 | 0.667 |
| dev | 20 | 1.000 | 0.650 | 0.600 | 1.000 | 0.700 | 0.650 | 1.000 | 0.900 | 0.875 | 0.351 | 0.900 | 0.900 | 0.875 |
| earnings | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 |
| generated | 13 | 1.000 | 0.538 | 0.500 | 1.000 | 0.923 | 0.756 | 1.000 | 1.000 | 0.821 | 0.426 | 1.000 | 1.000 | 0.859 |
| multi_page | 4 | 1.000 | 0.500 | 0.250 | 1.000 | 0.500 | 0.250 | 1.000 | 0.750 | 0.625 | 0.312 | 0.750 | 0.750 | 0.625 |
| narrative | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.333 | 1.000 | 1.000 | 1.000 |
| statement_table | 9 | 1.000 | 0.333 | 0.278 | 1.000 | 0.889 | 0.648 | 1.000 | 1.000 | 0.741 | 0.300 | 1.000 | 1.000 | 0.796 |
| tune | 13 | 1.000 | 0.538 | 0.500 | 1.000 | 0.923 | 0.756 | 1.000 | 1.000 | 0.821 | 0.426 | 1.000 | 1.000 | 0.859 |
| year_ambiguous | 2 | 1.000 | 0.500 | 0.250 | 1.000 | 1.000 | 0.417 | 1.000 | 1.000 | 0.583 | 0.333 | 1.000 | 1.000 | 0.583 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 25 | 1.000 | 0.600 | 0.540 | 1.000 | 0.800 | 0.673 | 1.000 | 0.920 | 0.807 | 0.364 | 0.920 | 0.920 | 0.827 |
| 10q | 3 | 1.000 | 0.333 | 0.333 | 1.000 | 0.667 | 0.667 | 1.000 | 1.000 | 1.000 | 0.208 | 1.000 | 1.000 | 1.000 |
| 8k | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Earnings | 5 | 1.000 | 0.600 | 0.600 | 1.000 | 0.800 | 0.667 | 1.000 | 1.000 | 0.933 | 0.400 | 1.000 | 1.000 | 0.933 |

## Answer quality (live LLM {'provider': 'groq', 'model': 'openai/gpt-oss-20b'}; sleep 8.0 s; split tune)

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | confident_error_rate | refusal_rate_numeric | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 41 | 33 | 0.756 | 1.000 | 0.444 | 0.697 | 0.303 | 0.600 | 20 | 0.150 | 0.250 | 0.565 | 0.471 | 13 | 22.920 | 34.360 | 1.890 | 2.710 |
| tune | 41 | 33 | 0.756 | 1.000 | 0.444 | 0.697 | 0.303 | 0.600 | 20 | 0.150 | 0.250 | 0.565 | 0.471 | 13 | 22.920 | 34.360 | 1.890 | 2.710 |

### By question type

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | confident_error_rate | refusal_rate_numeric | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| answerable | 33 | 33 | 0.697 | - | 0.000 | 0.697 | 0.303 | 0.600 | 20 | 0.150 | 0.250 | 0.565 | 0.471 | 13 | 23.710 | 33.910 | 1.940 | 2.536 |
| off_desk | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| unanswerable | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 22.685 | 941.634 | 1.685 | 2.634 |

### By tag

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | confident_error_rate | refusal_rate_numeric | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 1 | 0.000 | 0.000 | 1.000 | 1.000 | 0 | 21.700 | 21.700 | 1.700 | 1.700 |
| 8k | 1 | 1 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 1 | 0.000 | 0.000 | 1.000 | 1.000 | 0 | 20.980 | 20.980 | 1.980 | 1.980 |
| calc | 5 | 5 | 0.800 | - | 0.000 | 0.800 | 0.200 | 0.600 | 5 | 0.200 | 0.200 | 0.500 | 0.500 | 2 | 20.980 | 23.308 | 1.980 | 2.604 |
| compare | 3 | 3 | 0.667 | - | 0.000 | 0.667 | 0.333 | 0.333 | 3 | 0.333 | 0.333 | 0.500 | 0.250 | 3 | 33.610 | 36.553 | 1.880 | 2.150 |
| dev | 20 | 20 | 0.600 | - | 0.000 | 0.600 | 0.400 | 0.571 | 7 | 0.000 | 0.429 | 0.583 | 0.486 | 7 | 25.580 | 29.392 | 2.020 | 2.467 |
| earnings | 2 | 2 | 0.500 | - | 0.000 | 0.500 | 0.500 | 0.000 | 2 | 0.500 | 0.500 | 0.000 | 0.000 | 0 | 20.980 | 23.500 | 1.980 | 2.160 |
| forecast | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 1103.760 | 1103.760 | 2.760 | 2.760 |
| generated | 21 | 13 | 0.905 | 1.000 | 0.800 | 0.846 | 0.154 | 0.615 | 13 | 0.231 | 0.154 | 0.545 | 0.455 | 6 | 21.700 | 36.880 | 1.700 | 2.710 |
| multi_page | 4 | 4 | 0.500 | - | 0.000 | 0.500 | 0.500 | 0.000 | 2 | 0.000 | 1.000 | 0.500 | 0.167 | 3 | 25.735 | 26.529 | 2.000 | 2.273 |
| narrative | 1 | 1 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 1 | 0.000 | 0.000 | 1.000 | 0.500 | 0 | 19.970 | 19.970 | 1.970 | 1.970 |
| nonexistent_metric | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 22.920 | 22.920 | 1.920 | 1.920 |
| off_desk | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| proxy_only | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 22.450 | 22.450 | 1.450 | 1.450 |
| statement_table | 9 | 9 | 0.889 | - | 0.000 | 0.889 | 0.111 | 0.667 | 9 | 0.222 | 0.111 | 0.500 | 0.438 | 6 | 23.710 | 35.572 | 1.700 | 2.562 |
| tune | 21 | 13 | 0.905 | 1.000 | 0.800 | 0.846 | 0.154 | 0.615 | 13 | 0.231 | 0.154 | 0.545 | 0.455 | 6 | 21.700 | 36.880 | 1.700 | 2.710 |
| unanswerable | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 22.685 | 941.634 | 1.685 | 2.634 |
| year_ambiguous | 2 | 2 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 2 | 0.000 | 0.000 | 0.500 | 0.500 | 0 | 21.540 | 22.467 | 1.540 | 1.567 |
| year_beyond_corpus | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |

### Per question

| id | type | expected | got | numeric_ok | cite_hit | warnings | s |
|---|---|---|---|---|---|---|---:|
| fb_00735 | answerable | answered | refused | None | None | 0 | 27.89 |
| fb_04171 | answerable | answered | answered | True | True | 1 | 22.27 |
| fb_00603 | answerable | answered | refused | None | None | 0 | 34.36 |
| fb_00499 | answerable | answered | answered | None | False | 0 | 26.18 |
| fb_10285 | answerable | answered | answered | True | True | 0 | 22.56 |
| fb_00494 | answerable | answered | answered | None | True | 0 | 19.29 |
| fb_00215 | answerable | answered | answered | None | True | 3 | 26.59 |
| fb_10130 | answerable | answered | refused | False | None | 0 | 25.29 |
| fb_00757 | answerable | answered | answered | None | False | 1 | 27.5 |
| fb_01275 | answerable | answered | answered | None | True | 0 | 25.87 |
| fb_04980 | answerable | answered | answered | True | True | 1 | 23.53 |
| fb_00407 | answerable | answered | answered | None | True | 1 | 21.4 |
| fb_00941 | answerable | answered | refused | None | None | 0 | 25.94 |
| fb_03029 | answerable | answered | answered | True | False | 0 | 25.9 |
| fb_01484 | answerable | answered | refused | None | None | 0 | 22.1 |
| fb_00005 | answerable | answered | answered | None | False | 0 | 23.66 |
| fb_03069 | answerable | answered | refused | False | None | 0 | 21.82 |
| fb_00591 | answerable | answered | refused | None | None | 0 | 26.42 |
| fb_01254 | answerable | answered | answered | None | False | 0 | 19.38 |
| fb_02608 | answerable | answered | refused | False | None | 0 | 29.13 |
| g_s02 | answerable | answered | answered | True | False | 1 | 16.46 |
| g_s04 | answerable | answered | answered | False | False | 1 | 23.71 |
| g_s05 | answerable | answered | answered | True | True | 1 | 30.34 |
| g_s08 | answerable | answered | answered | True | True | 0 | 19.97 |
| g_s09 | answerable | answered | answered | True | True | 0 | 21.7 |
| g_s11 | answerable | answered | answered | False | False | 0 | 23.78 |
| g_s12 | answerable | answered | refused | False | None | 0 | 18.18 |
| g_s14 | answerable | answered | answered | True | True | 0 | 20.98 |
| g_l03 | answerable | answered | refused | False | None | 0 | 36.88 |
| g_l04 | answerable | answered | answered | False | False | 0 | 29.18 |
| g_l05 | answerable | answered | answered | True | True | 3 | 33.61 |
| g_y02 | answerable | answered | answered | True | True | 0 | 22.57 |
| g_y03 | answerable | answered | answered | True | False | 0 | 20.51 |
| g_o01 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_o02 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_o05 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_o06 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_u02 | unanswerable | refused | refused | None | None | 0 | 0.0 |
| g_u03 | unanswerable | refused | refused | None | None | 0 | 22.45 |
| g_u05 | unanswerable | refused | refused | None | None | 0 | 22.92 |
| g_u06 | unanswerable | refused | refused | None | None | 0 | 1103.76 |

### Manual review (answered, no numeric check)

**fb_00499** (health_industrials)
- Q: Is 3M a capital-intensive business based on FY2022 data?
- Gold: No, the company is managing its CAPEX and Fixed Assets pretty efficiently, which is evident from below key metrics:
CAPEX/Revenue Ratio: 5.1%
Fixed assets/Total Assets: 20%
Return on Assets= 12.4%
- System: Yes. 3M’s FY2022 financials show substantial capital outlays and a large property, plant and equipment base, indicating a capital-intensive business. In 2022, 3M recorded $1,831 million in capital expenditures [C3] and held $9,178 million in net PP&E [C6]. The company also reported capital spending of approximately $1.5 billion to $1.8 billion for 2023, underscoring ongoing investment intensity [C2]. These figures, expressed in millions of dollars for FY2022, demonstrate significant capital requirements relative to its asset base.
- Cited: [('3M_2022_10K', 123), ('3M_2022_10K', 124), ('3M_2022_10K', 39)]

**fb_00494** (health_industrials)
- Q: What production rate changes is Boeing forecasting for FY2023?
- Gold: Boeing forecasts an increase in the production rates for the 737, 777X and 787 aircrafts in 2023.
- System: Boeing forecasts that in FY2023 the 787 program will ramp up to about 5 aircraft per month, the 777X program will resume production, and the 737 program will gradually increase its production rate from the current 31 aircraft per month, depending on market demand and supply-chain capacity [C2].
- Cited: [('BOEING_2022_10K', 9)]

**fb_00215** (tech_telecom)
- Q: Is Verizon a capital intensive business based on FY 2022 data?
- Gold: Yes. Verizon's capital intensity ratio was approximately 2.774729. This means that it took approximately $2.77 of assets to generate $1 of revenue and thus, Verizon can be considered capital intensive.
- System: Yes. Verizon’s FY 2022 capital expenditures were $23.1 billion, which is 16.9 % of its operating revenue of $136.835 billion, and its net property, plant and equipment was $107.434 billion. These figures indicate a high level of capital investment relative to revenue and asset base, characteristic of a capital-intensive business. [C4] [C9] [C8]
- Cited: [('VERIZON_2022_10K', 39), ('VERIZON_2022_10K', 21), ('VERIZON_2022_10K', 56)]

**fb_00757** (tech_telecom)
- Q: Did AMD report customer concentration in FY22?
- Gold: Yes, one customer accounted for 16% of consolidated net revenue
- System: Yes. AMD disclosed customer concentration in FY22 by presenting a table that lists major customers that accounted for at least 10% of consolidated net revenue, including Customer A at 16% of FY22 revenue. [C13]
- Cited: [('AMD_2022_10K', 69)]

**fb_01275** (consumer)
- Q: Among operations, investing, and financing activities, which brought in the most (or lost the least) cash flow for Best Buy in FY2023?
- Gold: Best Buy generated the most cash flow from operating activities in FY 2023 ($1.8 bn)
- System: For fiscal year 2023, Best Buy’s operating activities generated the largest cash inflow, providing $1,824 million in cash [C2]. In contrast, investing activities used $962 million of cash [C3] and financing activities used $1,806 million of cash [C3]. Thus, operating activities brought in the most cash flow (or lost the least).
- Cited: [('BESTBUY_2023_10K', 42), ('BESTBUY_2023_10K', 29)]

**fb_00407** (consumer)
- Q: Which type of debt received the largest investment among the short term investments for MGM in H1 FY2023?
- Gold: the biggest short term investment is in corporate bonds (almost 82% of the total investment)
- System: Among the short-term investments reported for the six months ended June 30 2023, the largest investment was in corporate bonds, amounting to $416,420 thousand (≈$416.4 million). [C2]
- Cited: [('MGMRESORTS_2023Q2_10Q', 11)]

**fb_00005** (tech_telecom)
- Q: Does Corning have positive working capital based on FY2022 data? If working capital is not a useful or relevant metric for this company, then please state that and explain why.
- Gold: Yes. Corning had a positive working capital amount of $831 million by FY 2022 close. This answer considers only operating current assets and current liabilities that were clearly shown in the balance sheet.
- System: Yes, Corning had positive working capital of $2,278 million as of December 31, 2022 (year ended December 31, 2022). [C1]
- Cited: [('CORNING_2022_10K', 34)]

**fb_01254** (consumer)
- Q: Has MGM Resorts paid dividends to common shareholders in FY2022?
- Gold: Yes. MGM maintained 0.01$ per share annual dividend through out FY 2022.
- System: Yes, MGM Resorts paid dividends to common shareholders in FY2022, totaling $4 million. [C5]
- Cited: [('MGMRESORTS_2022_10K', 47)]


## Full config

```json
{
 "args": {
  "run_name": "final_tune_answers_oss20b",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "index_c200",
  "questions": "eval/questions_v2.jsonl",
  "split": "tune",
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
  "answerable": 33,
  "off_desk": 4,
  "unanswerable": 4
 }
}
```
