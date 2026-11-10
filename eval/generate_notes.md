# How eval/questions_v2.jsonl was made

54 questions = 20 dev (from `eval/questions.jsonl`, unchanged file) + 34 generated (`eval/build_questions_v2.py`).

## Method (generated questions)
1. Sampling: I picked documents with a seeded random draw over the manifest (seed 20261109) for 10-Ks, then
   hand-chose the 10-Q / earnings / 8-K documents so each doc type and all 12 companies / desks are represented
   (3M, AMD, Adobe, Best Buy, Boeing, Corning, J&J, MGM, PepsiCo, Pfizer, Ulta, Verizon; years 2016-2024).
2. For each sampled document I searched `cache/pages/<doc_id>.jsonl` with regexes for line items
   (statement rows, headcount, board changes, share exchange) and copied the exact supporting line as `evidence`.
3. Questions are phrased as an analyst would and paraphrase the page wording ("capex" for "Purchases of property,
   plant and equipment", "bottom line" / "operating profit" / "top line" for statement row names, "headcount" for
   "employed N people").
4. Mix: 14 single-company answerable (8 from 10-Ks, 2 from 10-Qs, 2 from earnings releases, 2 from 8-Ks;
   8 need a calculation from two figures; 6 read statement tables; 2 narrative); 5 lead comparisons across two
   companies (incl. AMD vs Pfizer R&D 2022 with the ground truth AMD $5,005M / Pfizer $11,428M, p.54 both);
   3 year-ambiguous; 6 off_desk (2 per non-lead role); 6 unanswerable
   (no filing for that year, year beyond the corpus, proxy-only info, nonexistent segment, nonexistent metric, a forecast).
5. **Automatic check**: `build_questions_v2.py` fails unless each evidence string occurs on the stated gold (or
   alt_gold) page of the stated document in the parse cache. Absence for the unanswerable ones was checked by
   regex over the whole company's cache (e.g. no "churn" in any AMD page, no "space tourism" in any Boeing page,
   no proxy "Summary Compensation Table" in any PepsiCo page, no Ulta filing covering fiscal 2018).

## Fields
`gold` = pages scored by the retrieval metrics. `alt_gold` = other pages that contain the same figure (MD&A table,
five-year summary, the next year's prior-year column); they count as correct *citations* in answer scoring but
not as retrieval hits. `numeric` = machine-checkable expected value(s) (`kind` usd_m / pct / count; `mode` any|all).
Year-ambiguous questions list every valid doc/page in `gold` and every acceptable value in `numeric`.
Every generated question has `"verified": false` - please verify the evidence (listed in docs/notes/SUMMARY_FOR_ME.md, section 9).

## Split
Generated questions: round(40%) of each kind is tagged `holdout` (single 6/14, lead_compare 2/5, year_ambiguous 1/3,
off_desk 2/6, unanswerable 2/6 -> 13 held out), chosen with `random.Random(20261109)`. The other 21 + the 20 dev
questions are TUNE (41). `run_eval.py --split tune` is the default; holdout needs `--split holdout|all`.
Experiments are decided on TUNE only; holdout is first run in Phase 6. (I wrote the questions and know which ones
are in holdout; I did not look at any holdout retrieval or answer result before Phase 6.)

## Limits
- 21 generated tune questions + 20 dev is small: one question = 2.4 points; differences of 1-2 questions are noise
  (hence the decision rule requires >= 2 questions net).
- Numeric scoring covers questions with a `numeric` spec (28 of 54); the rest are in the manual-review section.
- Gold pages are the pages I found; a figure may be valid on other pages (see alt_gold) - retrieval metrics are strict.
