# eval/results: index of runs

Every `<run>.json` / `<run>.md` here was produced by `eval/run_eval.py`; `summary.csv` has one row per run (retrieval metrics, plus `ans_*`
columns for `--answers` runs). Nothing here is ever overwritten: a corrected run gets a new name. Experiment ids are explained in
[`../../EXPERIMENTS.md`](../../EXPERIMENTS.md); the long form (hypotheses written before each run) is [`EXPERIMENT_LOG.md`](EXPERIMENT_LOG.md).

**Question sets.** *dev-20* = `eval/questions.jsonl` (the 20 given dev questions, answerable only). *v2* = `eval/questions_v2.jsonl`
(20 dev + 34 generated, split into **tune** = 41 questions, 33 answerable, and **holdout** = 13 questions, 9 answerable; see `eval/README.md`).
Metrics are not comparable across the two sets (see EXPERIMENTS.md).

**Indexes.** `plain-350` = 350-token chunks, no context header (folder `index_plain`). `header-350` = 350-token chunks with context header
(was `index_e1`, then `./index`, now `index_c350`). `header-200` = 200-token chunks with context header (was `index_c200`, now `./index`).
The run files record the folder name used at the time.

| run | experiment | questions | index | purpose |
|---|---|---|---|---|
| `e0_baseline_dev20` | e0 | dev-20 | plain-350 | baseline: dense top-k, role filter only |
| `e2_year_company_filter` | e2 | dev-20 | plain-350 | company/year filter inside the Chroma `where` |
| `e3a_rerank_minilm` | e3a | dev-20 | plain-350 | + MiniLM cross-encoder reranker (depth 50) |
| `e3b_rerank_bge` | e3b | dev-20 | plain-350 | + bge-reranker-base (depth 50) |
| `e3c_rerank_bge_depth10` | e3c | dev-20 | plain-350 | bge-reranker-base, depth 10 |
| `e4_drop_boilerplate` | e4 | dev-20 | plain-350 | drop short / exhibit-index chunks |
| `e5_prefer_10k` | e5 | dev-20 | plain-350 | exclude the annual-report duplicate when a 10-K exists |
| `e45_both` | e4+e5 | dev-20 | plain-350 | e4 and e5 together |
| `e6_context_header` | e6 | dev-20 | header-350 | context header embedded with every chunk |
| `p4_baseline_tune` | P4 | v2 tune | header-350 | baseline of the v2 era (retrieval) |
| `p4_baseline_tune_answers` | P4 | v2 tune | header-350 | baseline answers; model not recorded in the file (`gpt-oss-120b` inferred, see EXPERIMENTS.md) |
| `p4_baseline_tune_answers_rescored` | P4 | v2 tune | header-350 | same answers re-scored with the corrected scorer (**use this one**) |
| `p4_baseline_tune_answers_replay`, `..._replay2` | P4 | v2 tune | header-350 | replay from the LLM cache (0 API calls); `_replay` is **superseded** (cache decoded with the wrong encoding), `_replay2` is the valid replay |
| `p4_baseline_tune_failures.md` | P4 | v2 tune | header-350 | `eval/inspect_run.py` failure analysis of the baseline |
| `p5_x1_hybrid` | X1 | v2 tune | header-350 | hybrid BM25, **superseded**: returned 50 hits instead of k, ask-depth metrics invalid |
| `p5_x1b_hybrid` | X1 | v2 tune | header-350 | hybrid BM25, corrected |
| `p5_x2_expand_alone` | X2 | v2 tune | header-350 | query expansion alone |
| `p5_x2_expand_on_hybrid` | X2 | v2 tune | header-350 | expansion + hybrid, **superseded** (same bug as X1) |
| `p5_x2c_expand_on_hybrid` | X2 | v2 tune | header-350 | expansion + hybrid, corrected |
| `p5_x3_queryclean` | X3 | v2 tune | header-350 | QUERY_CLEAN |
| `p5_x4_prefix` | X4 | v2 tune | header-350 | bge query instruction prefix |
| `p5_x5_forecast` | X5 | v2 tune | header-350 | forward-looking year rule (on top of X2) |
| `p5_x6a_k12_b6500`, `p5_x6b_k12_b4500`, `p5_x6c_k5_b4500` | X6 | v2 tune | header-350 | ASK_K / token-budget variants (on top of X2) |
| `p5_x9_onnx` | X9 | v2 tune | header-350 | ONNX encoder: retrieval must be identical to `p5_x2_expand_alone` |
| `p5_x10_cap1`, `p5_x10_cap2` | X10 | v2 tune | header-350 | at most 1 / 2 chunks per page in the ask context (on top of X2) |
| `p5_r1_c200_k8`, `p5_r1_c200_k14` | R1 | v2 tune | header-200 | 200-token chunks at ASK_K 8 and 14 (on top of X2) |
| `p5_r1b_c200_k14_cap1` | R1 | v2 tune | header-200 | 200-token chunks, ASK_K 14, page cap 1 (**the adopted configuration**) |
| `p5_r1c_c200_k10`, `p5_r1d_c200_k14_pc10_cap1` | R1 | v2 tune | header-200 | ASK_K 10; per-company depth 10 |
| `p5_x2_expand_alone_failures.md`, `final_tune_failures.md`, `final_holdout_failures.md` | - | v2 | see run | `eval/inspect_run.py` failure analyses |
| `final_tune` | final | v2 tune | header-200 | final configuration, retrieval |
| `final_holdout` | final | v2 holdout | header-200 | final configuration, retrieval, first look at holdout |
| `final_all_default_check` | final | v2 all | header-200 (`./index`) | `python eval/run_eval.py --run-name ...` with no other flags; reproduces final_tune and final_holdout |
| `p6_baseline_tune_repro` | P4 | v2 tune | header-350 | baseline re-run with the documented `--set` overrides: identical to `p4_baseline_tune` |
| `p6_baseline_holdout` | P4 | v2 holdout | header-350 | baseline on holdout |
| `p6_alt_c350_cap1_holdout` | R1 (alt) | v2 holdout | header-350 | 350-token + expansion + cap, on holdout, information only |
| `final_tune_answers_oss20b`, `final_holdout_answers_oss20b` | final | v2 tune / holdout | header-200 | answers with **gpt-oss-20b** (stand-in: the 120b daily quota was spent); not comparable with the 120b baseline |
| `p7_budget4500`, `p7_budget3000`, `p7_budget2200` | B3000 | v2 tune | header-200 | CONTEXT_TOKEN_BUDGET 4500 / 3000 / 2200, retrieval level |
| `p4_baseline_tune_answers_rescored2`, `final_tune_answers_oss20b_rescored2`, `final_holdout_answers_oss20b_rescored2` | P4 / final | v2 | see run | confident-error-rate rescore (`rescore_answers.py --suffix _rescored2`); **superseded** by `_rescored3` (lost the model label and the by-split tables) |
| `p4_baseline_tune_answers_rescored3`, `final_tune_answers_oss20b_rescored3`, `final_holdout_answers_oss20b_rescored3` | P4 / final | v2 | see run | the same answers re-scored with the confident error rate added (no LLM calls). Use these for the three numbers: confident error / refusal / numeric accuracy |
| `p4_baseline_tune_answers_rescored4`, `final_tune_answers_oss20b_rescored4`, `final_holdout_answers_oss20b_rescored4` | P4 / final | v2 | see run | the same answers with the five-way numeric outcome (correct / partial / soft_refusal / refused / confident_error, definitions in `eval/README.md`); **use these**. `_rescored3` has the older two-way "confident error" (answered and wrong), kept for comparison |
| `summary.csv` | - | - | - | one row per run |
| `EXPERIMENT_LOG.md` | - | - | - | long-form experiment log (hypotheses before results) |

Not run yet: answer-level runs of the final configuration on `gpt-oss-120b` (daily token cap), X6/X7/X11/X12 at answer level.
Raw logs of the live-LLM runs and of the latency measurements are in [`../../logs/`](../../logs/).
