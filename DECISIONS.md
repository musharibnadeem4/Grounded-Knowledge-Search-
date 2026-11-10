# Decisions

## Corpus observations

Source: `docs/notes/explore_report.md`, unless noted.

- 119 PDFs, 18,371 pages. Manifest matches files 119/119 case-sensitively and case-insensitively; no extra or duplicate files.
- Page length: per-file median ranges widely; the median of the per-file medians is ~3,355 chars (~840 tokens at 4 chars/token). Pooled over all 18,371 pages the median is 3,138 chars (~784 tokens) (`logs/corpus_page_stats.txt`); I had guessed ~3,500 chars / ~850 tokens.
- PepsiCo 10-Ks for 2016–2022 run 479–667 pages (2015 is 168), with lower density (exhibits).
- Near-zero-text pages (< 50 chars): 127 of 18,371 (~0.7%). Pfizer is worst: 68 of 2,027 pages (~3.4%, including the 2023Q2 10-Q).
- Units differ by company: MGM statements are "(In thousands)", most others "(In millions)". Dev answers are given in millions or billions.
- Statement names differ from question wording: Boeing "Statements of Financial Position", Best Buy "Statements of Earnings", AMD "Statements of Operations", versus questions saying "balance sheet" / "income statement" / "P&L".
- Statement headers use period-end dates ("Fiscal Years Ended January 28, 2023"), not "FY2023".
- Each 10-K repeats 2–3 prior years, so the same line item appears in several filings with different values.
- "Table of Contents" / "Index" boilerplate appears at the top of most pages.
- Dev set (20 questions) has no lead-role, unanswerable or cross-desk questions.

## 1. Page number = 1-based PDF index

**Context:** Citations need page numbers. PDFs have a printed page number and a PDF index, and they can differ.

**Options considered:** 1-based PDF index; 0-based index; printed page number.

**Evidence:** Exact figures found on the gold pages with `pdf.pages[page - 1]`: Boeing 12645 on p.52, 3M 1577 on p.60, AMD 16% on p.12, MGM 0.01 on p.32. Every financial-statement gold page opens with the expected statement. 19 numbers found on gold pages vs 1 on a neighbour only. The 14 "not found" cases are derived ratios or unit-scaled values.

**Decision:** Page = 1-based PDF index.

**What would change my mind:** A hidden question set whose gold pages follow printed page numbers.

**Status:** decided

## 2. Ingest only manifest-listed PDFs; deny by default

**Context:** Access control filters by company and desk, which come from the manifest.

**Options considered:** Ingest everything in the corpus directory; ingest only manifest-listed files.

**Evidence:** A PDF without a manifest row has no company or desk, so it can't be filtered. Today 119/119 match, so this costs nothing now.

**Decision:** Skip and log any unlisted PDF; never index it.

**What would change my mind:** A requirement to search documents that have no manifest row.

**Status:** decided

## 3. doc_id verbatim from manifest; case-insensitive file matching

**Context:** Filenames and manifest spellings could differ in case.

**Options considered:** Exact-case matching only; case-insensitive matching with the manifest spelling kept.

**Evidence:** `Pfizer_2023Q2_10Q` has non-standard casing. Development is on Windows (case-insensitive filesystem, a path with a space); graders likely run Linux.

**Decision:** Match files case-insensitively with `pathlib`, but always use the manifest's `doc_id` spelling.

**What would change my mind:** A case collision between two files (the report shows none).

**Status:** decided

## 4. Chunks stay within one page: ~350 tokens, 50 overlap, hard cap 500

**Context:** Chunk size and boundaries affect both retrieval and page citations.

**Options considered:** Whole page per chunk; fixed windows across pages; within-page windows.

**Evidence:** bge-small truncates at 512 tokens and the median page is ~850 tokens, so a whole page would silently lose its bottom half. Crossing pages breaks page citations.

**Decision:** Within-page windows, ~350 tokens, 50-token overlap, never above 500.

**What would change my mind:** Retrieval experiments showing a different size works better. Chunk size is a planned experiment.

**Status:** provisional

**Correction (2026-11-10):** measured pooled median is 3,138 chars ≈ 784 tokens (`logs/corpus_page_stats.txt`), not ~850; the conclusion holds since it is still above bge-small's 512-token limit.

## 5. Fiscal-year convention: FY = calendar year in which the fiscal year ends

**Context:** Questions say "FY2023"; filings use period-end dates and company-specific labels.

**Options considered:** Year the fiscal year ends; the company's own label.

**Evidence:** The Best Buy FY2023 10-K covers the year ended Jan 28, 2023. The Ulta dev answer uses the same assumption while noting the company calls it "fiscal 2022".

**Decision:** FY = calendar year of the period end.

**What would change my mind:** Hidden questions using the company's own label.

**Status:** provisional

## 6. No OCR in the baseline

**Context:** Some pages have almost no extractable text and might be scans.

**Options considered:** OCR everything; OCR near-zero pages only; no OCR.

**Evidence:** Only ~0.7% of pages (127 of 18,371) have near-zero text, result of visually checking PFIZER_2018 p.4 and p.13, BOEING_2016 p.55, CORNING_2018 p.66.

**Decision:** No OCR for now.

**What would change my mind:** The visual check showing image-only tables or text.

**Status:** provisional (until the pages are checked)

## 7. Parser: pdfplumber, with a parsed-page cache

**Context:** Parsing is the slowest step and chunking will be re-run many times.

**Options considered:** pdfplumber; PyMuPDF; pdfplumber plus a cache.

**Evidence:** The full exploration pass took 28.6 min (~94 ms/page) on my laptop : i7-13th/16gb). Table rows extract readably, e.g. "Net sales $ 30,274 $ 31,821 $ 30,871".

**Decision:** pdfplumber; cache parsed pages keyed by file hash so chunking experiments don't re-parse.

**What would change my mind:** A faster parser (PyMuPDF) giving equal table quality on a few statement pages from different companies.

**Status:** provisional

## 8. Strip leading "Table of Contents" / "Index" lines before chunking

**Context:** Most pages begin with this boilerplate.

**Options considered:** Keep it; strip it.

**Evidence:** It is on nearly every page and adds shared tokens that carry no meaning.

**Decision:** Strip it before chunking.

**What would change my mind:** Redundant/same tokens from every page

**Status:** decided

## 9. Units stay attached to figures

**Context:** The units line ("In thousands" / "In millions") is at the top of the page, so mid-page chunks lose it.

**Options considered:** Ignore; prepend the header to every chunk; store it as metadata only.

**Evidence:** MGM 303 was not found on its gold page because that page is in thousands (answer is in millions).

**Decision:** Store each page's first lines as `page_header` metadata now. Test prepending it to chunks as experiment E1. The eval numeric matcher normalises thousands/millions/billions.

**What would change my mind:** E1 results.

**Status:** provisional

Further entries are added as decisions are made.

## 10. Embeddings Model 
Stay on bge-small: the full embed costs 49 min on my CPU; bge-base would be ~2.5 h per experiment, which would cut the number of experiments I can run. Would change if retrieval failures point at embedding quality rather than chunking or filtering.

## 11. Eval Set
85% of wrong results (72 of 85) come from the right company’s other filings. Retrieval isn’t confused about what is being asked; it can’t tell which year’s filing. Also noticed during exploration: each 10-K repeats 2–3 years of the same line items.
For 11 of 17 failures, the gold page isn’t even in the top 50. With ~8 near-identical filings per company crowding the results, the right one gets pushed out entirely. So a reranker can’t fix this: it can only reorder what was retrieved, and the gold isn’t there.
Hypothesis for E2: “Restricting retrieval to the filing(s) matching the question’s company and fiscal year will raise page_hit@5 substantially, because 85% of wrong results are same-company, other-filing.”

Fix: map a question’s year to filings

These rules are general facts about filings, not tuned to the dev set:

A filing for period P contains figures for P, P−1 and sometimes P−2. So prefer period = Y; if that company has no filing for Y (e.g. FY2013), widen to Y+1 and Y+2.
Multi-year questions (“FY2022 and FY2021”, “FY2015–FY2017”): use the latest year, because the latest filing contains the earlier ones.
No year in the question: don’t filter by year.
The parsed company filter can only narrow the role’s allowed set, never widen it. That’s the access-control invariant.

---

# Decisions from the experiment phase (2026-11-08 to 2026-11-10)

Run names refer to `eval/results/` (index: `eval/results/INDEX.md`; full table: `EXPERIMENTS.md`).

## 12. Narrow before ranking: year/company filter in; rerankers and the boilerplate filter out

**Date:** 2026-11-08 (dev-20 era).

**Context:** Entry 11 found that most wrong results were the right company's other filings, and that the gold page was often not in the top 50.

**Options considered:** (a) rerank a wider candidate set; (b) restrict candidates by parsed company and year inside the Chroma `where`; (c) drop boilerplate chunks; (d) prefer the 10-K over the annual-report PDF.

**Evidence:** Filter (`e0_baseline_dev20` -> `e2_year_company_filter`): page_hit@5 0.15 -> 0.40, @20 0.35 -> 0.70, MRR 0.053 -> 0.307; 9 questions better, 0 worse (`logs/compare_dev20_era.txt`).
Rerankers on top of the filter: MiniLM (`e3a_rerank_minilm`) page_hit@5 0.40 -> 0.50 but @20 0.70 -> 0.65, 4 better / 6 worse (most of the worse ones need a statement figure), p50 1,399 ms against 86 ms;
bge-reranker-base (`e3b_rerank_bge`) page_hit@5 0.30 at 11,848 ms; depth 10 (`e3c_rerank_bge_depth10`) 0.35 at 4,864 ms. Boilerplate filter (`e4_drop_boilerplate`), 10-K preference (`e5_prefer_10k`) and both (`e45_both`): identical to e2 on all 20 questions.

**Decision:** Keep the filter (`YEAR_COMPANY_FILTER`). Reject all rerankers. Keep `DROP_BOILERPLATE` off. Keep `PREFER_10K_OVER_ANNUALREPORT` on: no measured effect, but it removes a duplicate document whose chart pages are misleading (EXPERIMENTS.md, failure 1).

**What would change my mind:** A candidate set in which the gold page is reliably present but badly ordered (then a reranker could pay for its latency); a boilerplate-heavy hidden question set; a wrong year or company parse excluding the right filing in practice.

**Status:** decided

## 13. What gets embedded and how big: context header, 200-token chunks, 14 chunks, one per page

**Date:** 2026-11-09. Supersedes the size in entry 4; answers experiment E1 of entry 9.

**Context:** Mid-page chunks lose the statement name and units; 350-token chunks bury one-sentence facts; `ask` reads a token budget, not a fixed top 5.

**Options considered:** Plain 350-token chunks; 350 tokens with a context header ("company | type | FY | page | page header") embedded but not stored; 200-token chunks with the header at the same token volume (ASK_K 14 instead of 8); a cap of one chunk per page in the `ask` context.

**Evidence:** Header (`e6_context_header`): page_hit@5 0.40 -> 0.55, @10 0.45 -> 0.70; 7 better / 5 worse. Page cap (`p5_x10_cap1`): `ctx_page_hit` 0.818 -> 0.879, 2 better / 0 worse. 200-token chunks (`p5_r1b_c200_k14_cap1` vs `p5_x10_cap1`): `ctx_page_hit` 0.879 -> 0.939, gold recall 0.768 -> 0.869, 2 better / 0 worse, mean context 3,146 vs 2,875 tokens (`eval/results/EXPERIMENT_LOG.md`).
**The trade-off:** the top of the ranking gets worse: page_hit@5 0.758 -> 0.606 and MRR@10 0.432 -> 0.380. At ASK_K 8 the 200-token index is worse than the 350-token one (`p5_r1_c200_k8`: 0.818 -> 0.788). The re-embed took 3,260.9 s (`logs/ingest_c200.log`).
Final vs baseline on holdout: 0.556 -> 0.889 (`p6_baseline_holdout`, `final_holdout`); the 350-token alternative scored 0.667 there (`p6_alt_c350_cap1_holdout`).

**Decision:** Header on by default; `CHUNK_TOKENS=200`, overlap 40; `ASK_K=14` (10 per company for comparisons: a token-volume argument, not measured separately); one chunk per page.

**What would change my mind:** If a use needs the top 5 to be precise (a UI showing five results), I would go back to 350 tokens: that is where it is better. The +2 over the 350-token index is narrow, and the holdout has only 9 answerable questions.

**Status:** decided (narrowly)

## 14. Query side: a synonym map for the query, and an ONNX encoder for cold start

**Date:** 2026-11-09.

**Context:** Two query-time problems. Analysts write "capex", "R&D", "bottom line", "headcount"; statements say "Purchases of property, plant and equipment", "Research and development", "Net income", "we employed N people". And a cold `search` or `ask` process spent most of its time importing torch and sentence-transformers, not searching.

**Options considered:** For the wording gap: nothing; hybrid BM25 + dense (RRF) over the same filtered candidates; strip persona text (QUERY_CLEAN); the bge query instruction; a synonym map appended to the retrieval query only. For the cold start: keep sentence-transformers; ONNX export of bge-small (fp32) with onnxruntime and tokenizers only; int8 quantisation.

**Evidence (wording, tune `ctx_page_hit`):** map alone (`p5_x2_expand_alone`) 0.697 -> 0.818, 5 better / 1 worse, +8 ms. Hybrid (`p5_x1b_hybrid`) 0.697 -> 0.697 and +0.29 s; on top of the map (`p5_x2c_expand_on_hybrid`) +1 net. QUERY_CLEAN (`p5_x3_queryclean`) 0.727, +1 net. Instruction prefix (`p5_x4_prefix`) 0.636, worse. My first hybrid run looked like +3 because of a bug (it returned 50 hits instead of k); I kept the run, marked it superseded, and added a regression test.
**Evidence (cold start):** embeddings identical: cosine min 1.000000 on 200 texts; 0 of 41 questions with a different top-10 (`p5_x9_onnx` vs `p5_x2_expand_alone`). Cold `search`: 7.19 s -> 1.62 s (`eval/results/EXPERIMENT_LOG.md`); on another morning 18.86 s -> 1.69 s (`logs/cold_latency_search_torch_c350.json`, `logs/cold_latency_search_onnx.json`). The old path varies a lot with machine state; the ONNX path stays near 1.7 s.

**Decision:** Keep the map (`QUERY_EXPAND`); the LLM still sees the original question. Hybrid, QUERY_CLEAN and the prefix stay off. Use ONNX by default (`ONNX_ENCODER`); `ingest` exports and verifies it (cosine > 0.999 on 20 texts) when it is missing, and on failure warns and falls back to sentence-transformers. No quantisation: it would change the embeddings.

**What would change my mind:** I wrote the map after reading the tune failures, so the tune gain is optimistic; holdout also improved but is small. If hidden questions use filing wording the map does nothing; if it hurts, switch it off. A learned or configured map would be better than a hard-coded one. For ONNX: a platform without onnxruntime wheels (the fallback covers it) or a model change.

**Status:** decided

## 15. Refusal layers and where access control lives

**Date:** 2026-11-09.

**Context:** Wrong answers are worse than refusals, and a desk must never see another desk's filings.

**Options considered:** Rely on the LLM to refuse; filter results after retrieval; filter inside the vector query; refuse before retrieval when the question names an off-desk company.

**Evidence:** Order in `ask`: (1) a company named in the question outside the desk -> refuse before any retrieval; (2) a year more than one past the latest filing -> refuse before retrieval; (3) the LLM may refuse; (4) an answer without a valid citation is refused. The access filter is a Chroma `where` inside `retrieve()` (the invariant of entry 11); sub-queries per company pass through the same function.
ACL leaks: 0 in all 46 runs in `eval/results/summary.csv`. Refusal recall (off-desk and unanswerable refused): 1.00 on tune for the 120b baseline (`p4_baseline_tune_answers_rescored`) and for gpt-oss-20b (`final_tune_answers_oss20b`), and 1.00 on holdout (`final_holdout_answers_oss20b`).
Costs: a comparison needs one query per company; a wrongly parsed company or year can exclude the right filing; a correct answer without citation markers is refused (5 of 33 answerable on `final_tune_answers_oss20b`).

**Decision:** Keep all four layers; never filter after retrieval; a parsed company can only narrow the role's set.

**What would change my mind:** If the missing-marker refusals stay common after the structured-citation prompt (X12, not yet measured), I would accept uncited but well-grounded answers with a flag.

**Status:** decided

## 16. Eval set and primary metric: 20 dev + 34 generated questions, tune and holdout; gold page inside the context the LLM reads

**Date:** 2026-11-09.

**Context:** The 20 dev questions are answerable only and too few to decide anything about refusals, comparisons or ambiguity. And `page_hit@5`, the metric of the first experiments, stopped matching reality: `ask` reads ~14 chunks, so a gold page at rank 9 helps the answer and not the metric.

**Options considered:** Dev set only; add generated questions; hand-label a large set. For the metric: page_hit@5 and MRR only; recall over the whole token-budgeted context; answer accuracy only.

**Evidence (set):** `eval/build_questions_v2.py` builds 34 questions and fails unless every evidence line is found on the stated gold page of the parse cache (14 single-company, 5 comparisons, 3 year-ambiguous, 6 off-desk, 6 unanswerable). 13 of them (9 answerable) are held out with a fixed seed; I decided on tune only (41 questions, 33 answerable) and ran holdout for the final evaluation. After reading the baseline answers I corrected the scorer (rounding-aware numbers, two accepted values for Verizon "net income", one dev question moved to manual review) and re-scored the baseline into a new file (`p4_baseline_tune_answers_rescored`: numeric 0.667 -> 0.800). The same prompt produced different wording across two runs of the same model (`p4_baseline_tune_answers_replay2` vs the original), so answer-level differences of one or two questions are noise.
**Evidence (metric):** the two metrics disagree: the 200-token index lowers page_hit@5 (0.758 -> 0.606) and raises `ctx_page_hit` (0.879 -> 0.939). Answer-level metrics are the real target but cost about 4.0-4.3k tokens per question against a free daily cap of 200,000 (`eval/README.md`).

**Decision:** Use this set; mark every generated question `verified: false` until I check it by hand. Decide retrieval changes on `ctx_page_hit` (tune), report page_hit@k and MRR beside it, and use answer metrics (numeric accuracy, refusal precision/recall, citation hit/precision) on the final configuration. The two eras' numbers are not comparable (EXPERIMENTS.md).

**What would change my mind:** Errors found when I verify the questions; a larger or independently written set; a strong answer-level result that contradicts `ctx_page_hit` (e.g. more context hurting accuracy).

**Status:** provisional (verification pending)

## 17. LLM provider, model and the token budget

**Date:** 2026-11-09.

**Context:** I need an LLM that costs graders nothing: Groq's free tier (or a local Ollama).

**Options considered:** Groq (`openai/gpt-oss-120b` configured in my `.env`); Ollama locally; a context of 4,500, 3,000 or 2,200 tokens.

**Evidence:** Groq's limits for this model are 8,000 tokens a minute and 200,000 a day (`eval/results/EXPERIMENT_LOG.md`); the daily cap was reached after 49 live calls on gpt-oss-120b and 46 on gpt-oss-20b (`logs/p4_baseline_tune_answers.log`, `logs/p5_x2_answers.log`, `logs/final_holdout_answers_oss20b.log`, `logs/final_tune_answers_oss20b.log`). Budget at the retrieval level on tune: `ctx_page_hit` 0.939 at 4,500 (`p7_budget4500`), 3,000 (`p7_budget3000`) and 2,200 (`p7_budget2200`); mean context 3,280 / 2,853 / 2,072 tokens; gold recall 0.869 / 0.854 / 0.854.

**Decision:** Groq with a 4,500-token budget (default unchanged). `ask` retries short rate limits (up to 60 s), and on a daily-cap 429 it returns "LLM quota exhausted (provider daily limit); retrieval succeeded" instead of waiting. Evaluation runs use a prompt-keyed cache and `--max-llm-calls`.

**What would change my mind:** An answer-level run at 3,000 or 2,200 tokens that matches 4,500 (it would cut tokens a lot); a paid tier. The final configuration's answers were measured with gpt-oss-20b only (the 120b daily cap was spent), and the budget was compared at the retrieval level only, so a 120b answer run at 4,500, 3,000 and 2,200 tokens would settle it.

**Status:** provisional
