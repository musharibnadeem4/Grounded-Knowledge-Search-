# Decisions

## Corpus observations

Source: `explore_report.md`, unless noted.

- 119 PDFs, 18,371 pages. Manifest matches files 119/119 case-sensitively and case-insensitively; no extra or duplicate files.
- Page length: per-file median ranges widely; the median of the per-file medians is ~3,355 chars (~840 tokens at 4 chars/token). TODO(me): the report only has per-file stats, so confirm the corpus-wide median page (I had ~3,500 chars / ~850 tokens).
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