# Eval run: p4_baseline_tune_answers_rescored2

- Timestamp: 2026-11-09T13:23:27+05:00
- Config overrides (--set): none
- Index metadata: {'context_header': True, 'embed_model': 'BAAI/bge-small-en-v1.5', 'chunk_tokens': 350, 'chunk_overlap': 50, 'max_chunk_tokens': 500, 'written': '2026-11-08T18:55:59+05:00'}
- Git SHA: b236e7cc54fd59e35538e1e58cb2bde402f3f768 (dirty)
- Question types: {'answerable': 33, 'off_desk': 4, 'unanswerable': 4}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 92 ms, p95 273 ms (n=41, retrieval depth 20, model load excluded)
- Rerank latency: n/a (RERANKER off)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 33 | 1.000 | 0.606 | 0.525 | 1.000 | 0.697 | 0.616 | 1.000 | 0.848 | 0.747 | 0.334 | 0.697 | 0.697 | 0.601 |

## By split (tune = used for decisions, holdout = first looked at in the final evaluation)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 | askk_page_hit | ctx_page_hit | ctx_gold_recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

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

## Answer quality (live LLM None; sleep 8.0 s; split tune)

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | confident_error_rate | refusal_rate_numeric | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 41 | 33 | 0.927 | 1.000 | 0.727 | 0.909 | 0.091 | 0.800 | 20 | 0.100 | 0.100 | 0.567 | 0.456 | 17 | 18.620 | 35.250 | 18.620 | 35.250 |

### By question type

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | confident_error_rate | refusal_rate_numeric | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| answerable | 33 | 33 | 0.909 | - | 0.000 | 0.909 | 0.091 | 0.800 | 20 | 0.100 | 0.100 | 0.567 | 0.456 | 17 | 18.860 | 31.716 | 18.860 | 31.716 |
| off_desk | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| unanswerable | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 18.030 | 36.766 | 18.030 | 36.766 |

### By tag

| group | n | n_answerable | status_accuracy | refusal_recall | refusal_precision | answer_rate_on_answerable | refusal_rate_on_answerable | numeric_accuracy | n_numeric | confident_error_rate | refusal_rate_numeric | citation_hit | citation_precision | ungrounded_warnings | latency_p50_s | latency_p95_s | latency_net_p50_s | latency_net_p95_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10q | 1 | 1 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 1 | 0.000 | 0.000 | 1.000 | 0.500 | 0 | 17.840 | 17.840 | 17.840 | 17.840 |
| 8k | 1 | 1 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 1 | 0.000 | 0.000 | 1.000 | 1.000 | 1 | 15.840 | 15.840 | 15.840 | 15.840 |
| calc | 5 | 5 | 0.800 | - | 0.000 | 0.800 | 0.200 | 0.800 | 5 | 0.000 | 0.200 | 0.750 | 0.625 | 5 | 17.620 | 19.912 | 17.620 | 19.912 |
| compare | 3 | 3 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 3 | 0.000 | 0.000 | 0.667 | 0.333 | 2 | 29.360 | 34.661 | 29.360 | 34.661 |
| dev | 20 | 20 | 0.950 | - | 0.000 | 0.950 | 0.050 | 0.714 | 7 | 0.286 | 0.000 | 0.421 | 0.351 | 9 | 18.780 | 26.148 | 18.780 | 26.148 |
| earnings | 2 | 2 | 0.500 | - | 0.000 | 0.500 | 0.500 | 0.500 | 2 | 0.000 | 0.500 | 1.000 | 1.000 | 0 | 19.105 | 21.306 | 19.105 | 21.306 |
| forecast | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 39.740 | 39.740 | 39.740 | 39.740 |
| generated | 21 | 13 | 0.905 | 1.000 | 0.800 | 0.846 | 0.154 | 0.846 | 13 | 0.000 | 0.154 | 0.818 | 0.636 | 8 | 17.620 | 35.250 | 17.620 | 35.250 |
| multi_page | 4 | 4 | 1.000 | - | - | 1.000 | 0.000 | 0.000 | 2 | 1.000 | 0.000 | 0.250 | 0.250 | 3 | 21.095 | 22.905 | 21.095 | 22.905 |
| narrative | 1 | 1 | 0.000 | - | 0.000 | 0.000 | 1.000 | 0.000 | 1 | 0.000 | 1.000 | - | - | 0 | 15.860 | 15.860 | 15.860 | 15.860 |
| nonexistent_metric | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 16.150 | 16.150 | 16.150 | 16.150 |
| off_desk | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| proxy_only | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 19.910 | 19.910 | 19.910 | 19.910 |
| statement_table | 9 | 9 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 9 | 0.000 | 0.000 | 0.778 | 0.556 | 7 | 21.620 | 32.894 | 21.620 | 32.894 |
| tune | 21 | 13 | 0.905 | 1.000 | 0.800 | 0.846 | 0.154 | 0.846 | 13 | 0.000 | 0.154 | 0.818 | 0.636 | 8 | 17.620 | 35.250 | 17.620 | 35.250 |
| unanswerable | 4 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 18.030 | 36.766 | 18.030 | 36.766 |
| year_ambiguous | 2 | 2 | 1.000 | - | - | 1.000 | 0.000 | 1.000 | 2 | 0.000 | 0.000 | 1.000 | 0.750 | 1 | 19.095 | 22.303 | 19.095 | 22.303 |
| year_beyond_corpus | 1 | 0 | 1.000 | 1.000 | 1.000 | - | - | - | 0 | - | - | - | - | 0 | 0.000 | 0.000 | 0.000 | 0.000 |

### Per question

| id | type | expected | got | numeric_ok | cite_hit | warnings | s |
|---|---|---|---|---|---|---|---:|
| fb_00735 | answerable | answered | answered | None | False | 1 | 1.81 |
| fb_04171 | answerable | answered | answered | True | True | 0 | 1.29 |
| fb_00603 | answerable | answered | answered | None | False | 0 | 24.18 |
| fb_00499 | answerable | answered | answered | None | False | 2 | 23.1 |
| fb_10285 | answerable | answered | answered | True | True | 0 | 1.91 |
| fb_00494 | answerable | answered | answered | None | False | 0 | 16.87 |
| fb_00215 | answerable | answered | answered | None | False | 1 | 16.84 |
| fb_10130 | answerable | answered | answered | False | True | 0 | 20.39 |
| fb_00757 | answerable | answered | answered | None | False | 1 | 41.88 |
| fb_01275 | answerable | answered | refused | None | None | 0 | 2.95 |
| fb_04980 | answerable | answered | answered | True | False | 0 | 14.88 |
| fb_00407 | answerable | answered | answered | None | True | 0 | 25.32 |
| fb_00941 | answerable | answered | answered | None | True | 0 | 16.27 |
| fb_03029 | answerable | answered | answered | True | True | 0 | 18.62 |
| fb_01484 | answerable | answered | answered | None | False | 1 | 23.34 |
| fb_00005 | answerable | answered | answered | None | False | 0 | 18.7 |
| fb_03069 | answerable | answered | answered | False | False | 0 | 21.8 |
| fb_00591 | answerable | answered | answered | None | True | 2 | 23.59 |
| fb_01254 | answerable | answered | answered | None | True | 1 | 20.37 |
| fb_02608 | answerable | answered | answered | True | False | 0 | 18.86 |
| g_s02 | answerable | answered | answered | True | False | 0 | 20.43 |
| g_s04 | answerable | answered | answered | True | True | 4 | 17.62 |
| g_s05 | answerable | answered | answered | True | True | 0 | 21.62 |
| g_s08 | answerable | answered | refused | False | None | 0 | 15.86 |
| g_s09 | answerable | answered | answered | True | True | 0 | 17.84 |
| g_s11 | answerable | answered | answered | True | True | 0 | 21.55 |
| g_s12 | answerable | answered | refused | False | None | 0 | 16.66 |
| g_s14 | answerable | answered | answered | True | True | 1 | 15.84 |
| g_l03 | answerable | answered | answered | True | True | 0 | 29.36 |
| g_l04 | answerable | answered | answered | True | True | 0 | 27.75 |
| g_l05 | answerable | answered | answered | True | False | 2 | 35.25 |
| g_y02 | answerable | answered | answered | True | True | 0 | 22.66 |
| g_y03 | answerable | answered | answered | True | True | 1 | 15.53 |
| g_o01 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_o02 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_o05 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_o06 | off_desk | refused | refused | None | None | 0 | 0.0 |
| g_u02 | unanswerable | refused | refused | None | None | 0 | 0.0 |
| g_u03 | unanswerable | refused | refused | None | None | 0 | 19.91 |
| g_u05 | unanswerable | refused | refused | None | None | 0 | 16.15 |
| g_u06 | unanswerable | refused | refused | None | None | 0 | 39.74 |

### Manual review (answered, no numeric check)

**fb_00735** (consumer)
- Q: Has Pepsico reported any materially important ongoing legal battles from FY2022 and FY2021?
- Gold: No, Pepsico is not involved in material legal battles.
- System: PepsiCo disclosed that it is a party to a variety of ongoing litigation, claims, legal or regulatory proceedings, inquiries and investigations in its 2022 Form 10-K (covering fiscal year ended December 31, 2022)[C3]. The filing notes that these matters are “inherently uncertain” and could have an adverse impact on the business. No comparable disclosure for fiscal year 2021 is present in the provided context, so the answer for FY2021 cannot be determined from the given filings.
- Cited: [('PEPSICO_2022_10K', 25)]

**fb_00603** (consumer)
- Q: What drove the increase in Ulta Beauty's merchandise inventories balance at end of FY2023?
- Gold: Increase in Merchandise inventories balance was driven by the opening of 47 new stores. The answer here assumes FY2023 refers to the 12 months ended on January 28, 2023 (although the company refers to this period as its fiscal 2022.
- System: Ulta Beauty’s merchandise inventories rose to $1.6 billion at the end of fiscal 2023 (January 28, 2023), an increase of $104.2 million (7.0%) from $1.5 billion a year earlier. The increase was driven by three primary factors: $54 million of the rise came from the addition of 47 new stores opened since January 29 2022; $25 million was due to new key brand launches; and another $25 million resulted from higher inventory costs.[C1]
- Cited: [('ULTABEAUTY_2023_10K', 41)]

**fb_00499** (health_industrials)
- Q: Is 3M a capital-intensive business based on FY2022 data?
- Gold: No, the company is managing its CAPEX and Fixed Assets pretty efficiently, which is evident from below key metrics:
CAPEX/Revenue Ratio: 5.1%
Fixed assets/Total Assets: 20%
Return on Assets= 12.4%
- System: Based on FY2022 data, 3M’s operations involve substantial capital investment, which is characteristic of a capital-intensive business. In FY2022 the company reported total capital spending of $1,749 million (i.e., $1.749 billion) and net property, plant and equipment of $92,000 million (i.e., $92 billion) [C5]. These large amounts of capital outlays and assets suggest that 3M’s business model requires significant capital resources.
- Cited: [('3M_2022_10K', 34)]

**fb_00494** (health_industrials)
- Q: What production rate changes is Boeing forecasting for FY2023?
- Gold: Boeing forecasts an increase in the production rates for the 737, 777X and 787 aircrafts in 2023.
- System: Boeing expects to gradually increase its production rate to about 5 aircraft per month in fiscal year 2023 [C1].
- Cited: [('BOEING_2022_10K', 35)]

**fb_00215** (tech_telecom)
- Q: Is Verizon a capital intensive business based on FY 2022 data?
- Gold: Yes. Verizon's capital intensity ratio was approximately 2.774729. This means that it took approximately $2.77 of assets to generate $1 of revenue and thus, Verizon can be considered capital intensive.
- System: Verizon’s FY 2022 data show a capital-intensive business. The company recorded cash flows from capital expenditures of $23,087 million in 2022 [C2] and operating revenues of $136,835 million in the same year [C2]. The capital intensity can be expressed as:

CapEx % = (CapEx / Operating Revenues) × 100
= ($23,087 million / $136,835 million) × 100
= 0.1687 × 100 ≈ 16.9 %.

Thus, capital spending was about 16.9 % of revenue, indicating a capital-intensive operation. Additionally, Verizon reported long-term debt commitments of $149.4 billion as of December 31 2022 [C1], underscoring the substantial capital financing needs of the business.
- Cited: [('VERIZON_2022_10K', 21), ('VERIZON_2022_10K', 38)]

**fb_00757** (tech_telecom)
- Q: Did AMD report customer concentration in FY22?
- Gold: Yes, one customer accounted for 16% of consolidated net revenue
- System: Yes. In its FY22 filing AMD disclosed that a small number of customers will continue to account for a substantial part of AMD’s revenue in the future, indicating customer concentration. [C7]
- Cited: [('AMD_2022_10K', 4)]

**fb_00407** (consumer)
- Q: Which type of debt received the largest investment among the short term investments for MGM in H1 FY2023?
- Gold: the biggest short term investment is in corporate bonds (almost 82% of the total investment)
- System: Among the short-term investments reported for the six months ended June 30, 2023 (H1 FY2023), corporate bonds had the largest amount, $416,420 (thousands)[C1].
- Cited: [('MGMRESORTS_2023Q2_10Q', 11)]

**fb_00941** (health_industrials)
- Q: Which debt securities are registered to trade on a national securities exchange under 3M's name as of Q2 of 2023?
- Gold: Following debt securities registered under 3M's name are listed to trade on the New York Stock Exchange:
-1.500% Notes due 2026 (Trading Symbol: MMM26)
-1.750% Notes due 2030 (Trading Symbol: MMM30)
-1.500% Notes due 2031 (Trading Symbol: MMM31)
- System: As of the second quarter of 2023 (the period ended June 30, 2023), 3M had three debt securities registered under Section 12(b) to trade on a national securities exchange: the 1.500% Notes due 2026 (ticker MMM26) listed on the New York Stock Exchange; the 1.750% Notes due 2030 (ticker MMM30) listed on the New York Stock Exchange; and the 1.500% Notes due 2031 (ticker MMM31) listed on the New York Stock Exchange. [C5]
- Cited: [('3M_2023Q2_10Q', 1)]

**fb_01484** (health_industrials)
- Q: How did JnJ's US sales growth compare to international sales growth in FY2022?
- Gold: US sales increased 3.0% vs international sales decline of 0.6%.
- System: In fiscal year 2022, Johnson & Johnson’s U.S. sales grew 3.0% (to $48.6 billion) while international sales fell 0.6% (to $46.4 billion)[C1]. The difference in growth rates is 3.0% - (-0.6%) = 3.6 percentage points, meaning U.S. sales outperformed international sales by 3.6 pp.
- Cited: [('JOHNSON_JOHNSON_2022_10K', 28)]

**fb_00005** (tech_telecom)
- Q: Does Corning have positive working capital based on FY2022 data? If working capital is not a useful or relevant metric for this company, then please state that and explain why.
- Gold: Yes. Corning had a positive working capital amount of $831 million by FY 2022 close. This answer considers only operating current assets and current liabilities that were clearly shown in the balance sheet.
- System: Yes. Corning reported working capital of $2,278 million for fiscal year 2022, indicating a positive working capital position (the figure is presented in millions) [C1].
- Cited: [('CORNING_2022_10K', 34)]

**fb_00591** (tech_telecom)
- Q: Does Adobe have an improving Free cashflow conversion as of FY2022?
- Gold: Yes, the FCF conversion (using net income as the denominator) for Adobe has improved by ~13% from 143% in 2021 to 156% in 2022
- System: Yes. Adobe’s free-cash-flow (FCF) conversion improved in FY2022 compared with FY2021. 

- FY2022 net cash provided by operating activities: $7,838 million [C4].
- FY2022 purchases of property and equipment (capex): $442 million [C1].
- FY2022 free cash flow = $7,838 m - $442 m = $7,396 million.
- FY2022 net income: $4,756 million [C7].
- FY2022 FCF conversion = $7,396 m ÷ $4,756 m = 1.56, or 156 %.

- FY2021 net cash provided by operating activities: $7,230 million [C4].
- FY2021 purchases of property and equipment: $348 million [C1].
- FY2021 free cash flow = $7,230 m - $348 m = $6,882 million.
- FY2021 net income: $4,822 million [C7].
- FY2021 FCF conversion = $6,882 m ÷ $4,822 m = 1.43, or 143 %.

Since the conversion rose from about 143 % in FY2021 to about 156 % in FY2022, Adobe’s free-cash-flow conversion improved in FY2022.
- Cited: [('ADOBE_2022_10K', 47), ('ADOBE_2022_10K', 57), ('ADOBE_2022_10K', 54)]

**fb_01254** (consumer)
- Q: Has MGM Resorts paid dividends to common shareholders in FY2022?
- Gold: Yes. MGM maintained 0.01$ per share annual dividend through out FY 2022.
- System: Yes. MGM Resorts paid dividends to its common shareholders in fiscal year 2022 (year ended December 31, 2022). The company maintained an annual dividend of $0.01 per share throughout 2022 [C1] and recorded a dividend of $4,048 thousand (i.e., $4.048 million) in its consolidated statements of stockholders' equity for 2022 [C4]. Additionally, the company reported paying quarterly dividends of $0.0025 per share in March, June, September and December 2022, totaling about $4 million for the year [C6].
- Cited: [('MGMRESORTS_2022_10K', 32), ('MGMRESORTS_2022_10K', 64), ('MGMRESORTS_2022_10K', 47)]


## Full config

```json
{
 "args": {
  "run_name": "p4_baseline_tune_answers",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "D:\\Assignment DRG\\index",
  "questions": "eval/questions_v2.jsonl",
  "split": "tune",
  "answers": true
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
