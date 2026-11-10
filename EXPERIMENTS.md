# EXPERIMENTS

Every experiment I ran, in order, including the ones that did not help. Numbers come from `eval/results/summary.csv` and the run files named
in each row (`eval/results/INDEX.md` maps run names to experiments). Per-question better / worse / same comes from `eval/compare_runs.py`;
its output is saved in `logs/compare_dev20_era.txt` and `logs/compare_final_vs_baseline.txt`. Hypotheses are what I wrote before the run (`DECISIONS.md` for e2 and e6, quoted exactly; `eval/results/EXPERIMENT_LOG.md` for the v2 era, shortened);
where I wrote none at the time, the cell says so.

## Two eras, two metrics: do not compare numbers across them

* **Dev-20 era (e0-e6).** 20 answerable dev questions, plain ranking metrics: `page_hit@k` = a gold page is among the top-k *chunks* returned by `retrieve()`.
  No LLM involved.
* **v2 era (P4, X1-X12, R1, B3000).** 54 questions (`eval/questions_v2.jsonl`), decided on the **tune** part only (33 answerable questions).
  The primary metric is now **`ctx_page_hit`**: a gold page is among the chunks that `ask` hands to the LLM (same sub-queries, page cap and token
  budget as `ask`). I changed it because `ask` reads ~8-14 chunks, not 5, so `page_hit@5` stopped predicting what the LLM can use.
  `page_hit@5` and `MRR@10` are still reported. The v2 baseline (`p4_baseline_tune`, page_hit@5 0.606) already includes the year/company filter and the
  context header from the first era, so it is not comparable with e0 (page_hit@5 0.15).
* Rule for keeping a change in the v2 era (fixed before the runs): at least 2 questions better net on tune `ctx_page_hit` (or on answer accuracy),
  0 ACL leaks, warm latency +0.5 s at most, tests pass.

## Dev-20 era (metric: page_hit@5 on 20 dev questions, plain 350-token index unless noted)

| id | what changed | hypothesis | key metric before -> after | better / worse / same | latency p50 | kept? | note |
|---|---|---|---|---|---|---|---|
| e0 `e0_baseline_dev20` | baseline: dense top-k, role filter only | none (reference) | page_hit@5 0.15, @10 0.25, @20 0.35, MRR 0.053 | - | 90.5 ms | - | 85 % of wrong top results were the right company's other filings (DECISIONS.md entry 11) |
| e2 `e2_year_company_filter` | parse company and year from the question; narrow the Chroma `where` (never wider than the role) | "Restricting retrieval to the filing(s) matching the question's company and fiscal year will raise page_hit@5 substantially, because 85% of wrong results are same-company, other-filing" (DECISIONS.md entry 11) | page_hit@5 0.15 -> 0.40; @10 0.25 -> 0.45; @20 0.35 -> 0.70; MRR 0.053 -> 0.307 | 9 / 0 / 11 | 86.1 ms | **yes** | largest single gain of the project |
| e3a `e3a_rerank_minilm` | + MiniLM cross-encoder, depth 50 (from e2) | none written; DECISIONS.md entry 11 predicted a reranker can only reorder what was retrieved | page_hit@5 0.40 -> 0.50; @10 0.45 -> 0.50; @20 0.70 -> 0.65; MRR 0.307 -> 0.283 | 4 / 6 / 10 | 1,399 ms (rerank 1,304 ms) | no | helps the top 5 a little, hurts deeper ranks; most of the 6 worse questions need a figure from a financial statement; about 15x slower |
| e3b `e3b_rerank_bge` | + bge-reranker-base, depth 50 | none written | page_hit@5 0.40 -> 0.30; @10 0.45 -> 0.45; @20 0.70 -> 0.65; MRR 0.307 -> 0.279 | 4 / 5 / 11 | 11,848 ms | no | worse and about 140x slower |
| e3c `e3c_rerank_bge_depth10` | bge-reranker-base, depth 10 | none written (try to cut the cost) | page_hit@5 0.40 -> 0.35; @10 0.45 -> 0.55; @20 0.70 -> 0.70; MRR 0.307 -> 0.300 | 3 / 5 / 12 | 4,864 ms | no | still about 55x slower, no gain at @5 |
| e4 `e4_drop_boilerplate` | drop short and exhibit/signature chunks | none written | identical to e2 on every metric | 0 / 0 / 20 | 85.6 ms | off (flag `DROP_BOILERPLATE`) | no effect on the dev questions |
| e5 `e5_prefer_10k` | exclude the annual-report PDF when a 10-K exists for the same period | none written | identical to e2 | 0 / 0 / 20 | 81.8 ms | **on** (harmless; avoids chart-text pages, see failure 1) | no measurable rank effect |
| e45 `e45_both` | e4 + e5 | none written | identical to e2 | 0 / 0 / 20 | 87.1 ms | - | confirms there is no interaction |
| e6 `e6_context_header` | embed `company \| type \| FY \| page \| page header` + chunk (stored text unchanged); 350-token chunks | "The units line ("In thousands" / "In millions") is at the top of the page, so mid-page chunks lose it" (DECISIONS.md entry 9, experiment E1) | page_hit@5 0.40 -> 0.55; @10 0.45 -> 0.70; @20 0.70 -> 0.85; MRR 0.307 -> 0.304 | 7 / 5 / 8 | 83.8 ms | **yes** (default) | most of the 5 worse questions need a figure from a financial statement; X2 recovered four of them (fb_04171, fb_10285, fb_03029, fb_02608), fb_00215 still failed (`p5_x2_expand_alone_failures.md`). Re-embed cost: embed 3,742.8 s (`logs/ingest_e6_context_header.log`) |

## v2 era (metric: `ctx_page_hit` on 33 answerable tune questions; baseline `p4_baseline_tune` = 0.697)

| id | what changed | hypothesis | key metric before -> after | better / worse / same | latency p50 | kept? | note |
|---|---|---|---|---|---|---|---|
| P4 `p4_baseline_tune` | reference: header index, 350 tokens, ASK_K 8, no expansion | - | ctx 0.697; page_hit@5 0.606; @10 0.697; MRR 0.334 | - | 80.3 ms | - | 13 of 33 miss page_hit@5; 56 of the 65 top-5 results of those misses were the right filing but the wrong page (`p4_baseline_tune_failures.md`) |
| X1 `p5_x1b_hybrid` | BM25 over the same filtered candidates, fused with dense by RRF | "exact line-item names match statement rows that dense embeddings miss" | ctx 0.697 -> 0.697; page_hit@10 0.697 -> 0.788 | 4 / 4 / 25 | 369.6 ms | no | **my first run (`p5_x1_hybrid`) said +3: it returned 50 hits instead of k, so the ask-depth metrics were inflated. Superseded, kept.** On top of X2 (`p5_x2c_expand_on_hybrid` vs `p5_x2_expand_alone`): 0.818 -> 0.848, 3 / 2 / 28, 353.6 ms: below the +2 bar and +0.27 s |
| X2 `p5_x2_expand_alone` | append formal filing terms for analyst shorthand (capex, R&D, bottom line, headcount, ...) to the retrieval query | "questions use shorthand, statements use formal labels; appending the formal label moves statement pages up; expect +2..4" | ctx 0.697 -> 0.818; page_hit@5 0.606 -> 0.758; MRR 0.334 -> 0.432 | 5 / 1 / 27 | 87.9 ms | **yes** | I wrote the map after reading the tune failures, so the tune gain is optimistic; holdout also improves (final vs baseline below) |
| X3 `p5_x3_queryclean` | keep only sentences with "?" or a company/year for retrieval | "dev questions contain persona/format boilerplate that dilutes the embedding" | ctx 0.697 -> 0.727 | 3 / 2 / 28 | 80.7 ms | no | +1 net, below the bar; gains only on long dev questions |
| X4 `p5_x4_prefix` | bge query instruction prefix | "may be nil: documents are embedded without the instruction" | ctx 0.697 -> 0.636; page_hit@5 0.606 -> 0.424 | 1 / 3 / 29 | 82.3 ms | no | made it worse, as suspected |
| X5 `p5_x5_forecast` | forward-looking question about year Y with no filing for Y: search the Y-1 filing | "expect +1 on fb_00494, ~0 elsewhere" | ctx 0.818 -> 0.848 (vs X2) | 1 / 0 / 32 | 82.5 ms | no (flag off) | one forward-looking question in tune: not enough evidence |
| X6 `p5_x6a_k12_b6500`, `p5_x6b_k12_b4500`, `p5_x6c_k5_b4500` | ASK_K 12 (token budget 6,500 / 4,500) and ASK_K 5, 350-token index (vs X2) | "bigger K raises recall; the budget decides the cost" | ctx 0.818 -> 0.909 (K12, both budgets); 0.818 -> 0.758 (K5) | 3 / 0 / 30; 0 / 2 / 31 | 81-87 ms | no | no answer-level evidence possible (quota); superseded by R1 |
| X7 | prompt v2 (units, calculation inputs, period-mismatch refusal), `PROMPT_VERSION=2` | "numeric accuracy is limited by units and wrong-period figures" | **not run** | - | - | off | needs an answer-level run (see below) |
| X8 | caution label for chart-extraction pages | "chart text can mislead the LLM" | **not implemented**: only 5 of 18,371 cached pages match the pattern; the AMD one is already excluded by e5 | - | - | no | see failure 1 |
| X9 `p5_x9_onnx` | ONNX query encoder instead of sentence-transformers | "retrieval must be identical; cold start should drop" | 0 of 41 questions with a different top-10; cosine min 1.000000 on 200 texts | 0 / 0 / 33 | 77.0 ms warm | **yes** | cold `search`: 7.19 s -> 1.62 s (`eval/results/EXPERIMENT_LOG.md`); again 18.86 s -> 1.69 s on another morning (`logs/cold_latency_search_*.json`) |
| X10 `p5_x10_cap1`, `p5_x10_cap2` | at most 1 (2) chunks per page in the ask context (vs X2) | "several contexts spend 2-3 of 8 slots on one page; expect +1..3" | ctx 0.818 -> 0.879 (cap 1); 0.848 (cap 2) | 2 / 0 / 31; 1 / 0 / 32 | 240 ms (measured while a re-embed used every core) | **yes (cap 1)** | token-neutral. Risk: a table split over two chunks of one page loses the second |
| X11 | one retry when the answer has no valid `[C#]` marker, `RETRY_UNCITED` | "models forget the markers and the check turns a correct answer into a refusal" | **not run**: attempt cancelled when Groq's daily cap appeared (`logs/x11_retry_uncited_tune_oss20b.log`) | - | - | off | the failure is real: 5 of 33 answerable on `final_tune_answers_oss20b`, 1 of 9 on `final_holdout_answers_oss20b` |
| X12 | citations as a JSON field, `PROMPT_VERSION=3` | "structured ids are more reliable than inline markers" | **not run** (quota) | - | - | off | implemented with tests |
| X13 | prompt v4 = v3 + "if you cannot give the specific figure or fact asked for, set status to refused; you may still list the inputs you found", and a post-check that turns an answered-but-unavailable reply into a refusal (`PROMPT_VERSION=4`) | the soft refusals (2 of 20 numeric-gold questions on `p4_baseline_tune_answers_rescored4`) should become honest refusals; partial multi-company answers should stay answered | **not run** (daily quota); the detector flags exactly those 2 baseline answers and none of the others | - | - | off | implemented with tests; evaluate with `--set PROMPT_VERSION=4` |
| R1 `p5_r1b_c200_k14_cap1` | the one re-embed: 200-token chunks (overlap 40), ASK_K 14 (same token volume), page cap 1 (vs X10) | "5 of 8 residual misses are one-sentence facts buried in a 350-token chunk; finer chunks should rank them higher" | ctx 0.879 -> 0.939; recall 0.768 -> 0.869. **Top-5 gets worse: page_hit@5 0.758 -> 0.606, MRR 0.432 -> 0.380** | 2 / 0 / 31 | 107 ms | **yes, narrowly** | at ASK_K 8 the 200-token index is worse (`p5_r1_c200_k8`: 0.818 -> 0.788, 3 / 4 / 26). Embed 3,260.9 s (`logs/ingest_c200.log`) |
| B3000 `p7_budget3000`, `p7_budget2200` | CONTEXT_TOKEN_BUDGET 3,000 and 2,200 vs 4,500 (final config) | "tail trimming costs 0-3 questions and cuts ~15-20 % of tokens" (I was partly wrong: it cost none) | ctx 0.939 -> 0.939 in both; gold recall 0.869 -> 0.854 | 0 / 0 / 33 | 103.7 / 100.4 ms | default left at 4,500 | mean context 3,280 -> 2,853 (-13 %) -> 2,072 tokens (-37 %). Answer quality at these sizes not tested |
| **Final** `final_tune`, `final_holdout` | X2 + X9 + X10 + R1 (defaults) | - | **tune** ctx 0.697 -> 0.939; **holdout** (`p6_baseline_holdout` -> `final_holdout`) 0.556 -> 0.889 | tune 8 / 0 / 25; holdout 3 / 0 / 6 | 102.7 / 99.0 ms | - | ACL leaks 0 in every run. Holdout has 9 answerable questions: one is 11 points |

**Answer-level runs.** `p4_baseline_tune_answers_rescored` (gpt-oss-120b, inferred: the run file did not record the model): status 0.927, numeric 0.800, citation hit 0.567.
`final_tune_answers_oss20b` and `final_holdout_answers_oss20b` use gpt-oss-20b because the 120b daily quota was spent: not comparable.
Not run: the final configuration on gpt-oss-120b, and X7, X11, X12, X13 at answer level (the free daily token cap was spent). The answer rows above are what exists.

## The 3 worst failures (final configuration)

### 1. "Compare R&D spending at AMD and Pfizer in 2022." (holdout `g_l01`, role lead)
* **Retrieved** (`final_holdout_answers_oss20b`, context in rank order): AMD_2022_10K p.43, 44, 50, 52, 48, 54; PFIZER_2022_10K p.73, 34, 42, 11, 105, 36.
  Gold: AMD_2022_10K p.54 (found) and PFIZER_2022_10K p.54 (missing; p.41 also holds the figure and is missing). The answer gives AMD $5,005 million and says Pfizer's figure is not in the filings.
* **Root cause.** The per-company sub-query is "R&D spending at Pfizer in 2022." The word "spending" pulls narrative cost discussions; the statement of income ranks 37th
  (`logs/diag_pfizer_rd_rank.txt`), but 1st for "Pfizer R&D expense 2022 statement of income". My expansion adds "research and development" and no statement title.
* **The earlier AMD story.** For AMD, `AMD_2022_annualreport` p.3 is a chart page whose cached text reads `$9.8B $4.3B` on one line and
  `REVENUE GROSS PROFIT R&D INVESTMENT` on another (`cache/pages/AMD_2022_annualreport.jsonl`): numbers and labels are not associated, and a model can read "$9.8B" as R&D.
  The citation check passes such an answer because the cited page does contain the number. e5 now excludes that PDF when a 10-K exists. The real figure is $5,005 million (AMD_2022_10K p.54).
  The answer that said "$9.8 billion" for AMD R&D, citing that page, is in `logs/manual_2026-11-08_amd_rnd_chart_misread.txt` (captured manually from the terminal on 2026-11-08, before the 10-K preference and the per-company sub-queries existed).
* **Next.** Append the statement title for line-item words (income statement, cash flow, balance sheet items) to the retrieval query. I found this by reading a holdout failure, so
  I have not adopted it: it needs a check on tune first.

### 2. "Has Pepsico reported any materially important ongoing legal battles from FY2022 and FY2021?" (dev `fb_00735`)
* **Retrieved** (`final_tune.json`, context): PEPSICO_2022Q4_EARNINGS p.24, then PEPSICO_2022_10K p.25, 32, 35, 17, 64, 19, 76, 131 ...: risk-factor and cautionary-statement pages. Gold: PEPSICO_2022_10K p.26, not retrieved.
  It was not in the top 50 even in the baseline (`p4_baseline_tune_failures.md`). On `final_tune_answers_oss20b` the answer then lacked citation markers and was refused.
* **Root cause.** The answer is the short "Item 3. Legal Proceedings" paragraph at the bottom of a page that is mostly the Item 2 properties table, so its chunk embeds as "properties".
  "Legal battles" matches risk-factor prose about litigation instead.
* **Next.** Start a new chunk at `Item N.` headings, and add legal synonyms (lawsuit, litigation, legal proceedings, contingencies) to the expansion map. A BM25 hit on "Proceedings" is another option.

### 3. "Is 3M a capital-intensive business based on FY2022 data?" (dev `fb_00499`, three gold pages)
* **Retrieved** (`final_tune.json`, context): 3M_2022_10K p.34, 39, 123, 38, 7, 124, 64, 41, 40, 28, 21, 53, 37, 94. Gold: p.48 (income statement), p.50, p.52: none retrieved.
* **Root cause.** A ratio needs net sales, property and capital expenditures from three statements. One query finds MD&A prose about capex instead. The expansion for "capital intensive" adds capex terms only.
* **Next.** Decompose ratio questions into component sub-queries (net sales, PP&E, capex), as I already do per company, and add the statement titles from failure 1.

Also open: answers without citation markers are refused (X11/X12), and 200-token chunks rank worse at the top (R1).
