#!/usr/bin/env python
"""Build eval/questions_v2.jsonl = 20 dev questions + 34 generated questions, with a held-out split.

  python eval/build_questions_v2.py

* dev questions come from eval/questions.jsonl (tagged "dev", split "tune"); a few get a `numeric`
  annotation so numeric accuracy can be scored.
* generated questions are written below. Every `evidence` entry is checked against the parse cache
  (cache/pages/<doc_id>.jsonl): the text must occur on that page (whitespace-normalised) and the page
  must be one of the question's gold / alt_gold pages. The script fails loudly otherwise.
* split: ~40% of the generated questions (stratified by `kind`) get tag "holdout"; the rest are "tune".
  Seeded, deterministic. Do not look at holdout results before the final evaluation.
* all generated questions are verified=false (the user verifies them later).

Fields: id, role, question, answer, type (answerable|off_desk|unanswerable), gold, alt_gold, evidence,
tags, split, source, verified, kind, numeric {kind: usd_m|pct|count, values: [..], mode: any|all}.
"""
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261109
HOLDOUT_FRACTION = 0.40


def G(doc, *pages):
    return {"doc_id": doc, "pages": list(pages)}


def E(doc, page, text):
    return {"doc_id": doc, "page": page, "text": text}


def N(kind, *values, mode="any"):
    return {"kind": kind, "values": list(values), "mode": mode}


# ------------------------------------------------------------------ generated questions
# kind: single | lead_compare | year_ambiguous | off_desk | unanswerable
GEN = [
    # ---- 14 single-company answerable -------------------------------------------------
    dict(id="g_s01", kind="single", role="health_industrials", tags=["calc", "statement_table"],
         question="What share of 3M's 2021 sales did the company reinvest in capex?",
         answer="About 4.5%: purchases of PP&E of $1,603M on net sales of $35,355M.",
         gold=[G("3M_2021_10K", 45, 49)], alt_gold=[G("3M_2021_10K", 37, 39)],
         evidence=[E("3M_2021_10K", 45, "Net sales $ 35,355 $ 32,184 $ 32,136"),
                   E("3M_2021_10K", 49, "Purchases of property, plant and equipment (PP&E) (1,603) (1,501) (1,699)")],
         numeric=N("pct", 4.53)),
    dict(id="g_s02", kind="single", role="health_industrials", tags=["calc", "statement_table"],
         question="By how much did Boeing's bottom line deteriorate going from 2018 to 2019, in $ millions?",
         answer="$11,096M: net earnings of $10,460M in 2018 became a net loss of $636M in 2019.",
         gold=[G("BOEING_2019_10K", 22)], alt_gold=[G("BOEING_2019_10K", 20, 25)],
         evidence=[E("BOEING_2019_10K", 22, "Net (loss)/earnings ($636) $10,460 $8,458")],
         numeric=N("usd_m", 11096)),
    dict(id="g_s03", kind="single", role="health_industrials", tags=["calc", "statement_table"],
         question="What fraction of Pfizer's 2021 top line went to research and development?",
         answer="About 17.0%: R&D expenses of $13,829M on total revenues of $81,288M.",
         gold=[G("PFIZER_2021_10K", 39, 57)], alt_gold=[G("PFIZER_2021_10K", 42)],
         evidence=[E("PFIZER_2021_10K", 39, "Total revenues $ 81,288 $ 41,651"),
                   E("PFIZER_2021_10K", 57, "Research and development expenses(a) 13,829 9,393 8,385")],
         numeric=N("pct", 17.0)),
    dict(id="g_s04", kind="single", role="consumer", tags=["calc", "statement_table"],
         question="How far did MGM's net revenues fall from 2019 to 2020, in billions of dollars?",
         answer="About $7.74 billion: net revenues fell from $12.90B (2019) to $5.16B (2020); the filing reports thousands.",
         gold=[G("MGMRESORTS_2020_10K", 42)], alt_gold=[],
         evidence=[E("MGMRESORTS_2020_10K", 42, "Net revenues $ 5,162,082 $ 12,899,672 $ 11,763,096")],
         numeric=N("usd_m", 7737.59)),
    dict(id="g_s05", kind="single", role="tech_telecom", tags=["statement_table"],
         question="What was Adobe's operating profit for fiscal 2022, in $ millions?",
         answer="$6,098 million.",
         gold=[G("ADOBE_2022_10K", 54)], alt_gold=[],
         evidence=[E("ADOBE_2022_10K", 54, "Operating income 6,098 5,802 4,237")],
         numeric=N("usd_m", 6098)),
    dict(id="g_s06", kind="single", role="health_industrials", tags=["narrative"],
         question="How many people did Johnson & Johnson say it employed worldwide in its 2020 annual report?",
         answer="Approximately 134,500 employees.",
         gold=[G("JOHNSON_JOHNSON_2020_10K", 7, 8)], alt_gold=[G("JOHNSON_JOHNSON_2020_10K", 11)],
         evidence=[E("JOHNSON_JOHNSON_2020_10K", 7, "approximately 134,500 employees worldwide")],
         numeric=N("count", 134500)),
    dict(id="g_s07", kind="single", role="tech_telecom", tags=["statement_table"],
         question="What was Corning's 2021 profit attributable to its shareholders, in $ millions?",
         answer="$1,906 million.",
         gold=[G("CORNING_2021_10K", 30)], alt_gold=[G("CORNING_2021_10K", 26)],
         evidence=[E("CORNING_2021_10K", 30, "Net income attributable to Corning Incorporated $ 1,906 $ 512 $ 960")],
         numeric=N("usd_m", 1906)),
    dict(id="g_s08", kind="single", role="tech_telecom", tags=["narrative"],
         question="What was Adobe's headcount at the end of fiscal 2016?",
         answer="15,706 people (as of December 2, 2016).",
         gold=[G("ADOBE_2016_10K", 17)], alt_gold=[],
         evidence=[E("ADOBE_2016_10K", 17, "As of December 2, 2016, we employed 15,706 people.")],
         numeric=N("count", 15706)),
    dict(id="g_s09", kind="single", role="tech_telecom", tags=["calc", "10q", "statement_table"],
         question="By what percentage did Corning's quarterly net sales decline in Q2 2023 versus the same quarter of 2022?",
         answer="About 10.3%: net sales of $3,243M vs $3,615M.",
         gold=[G("CORNING_2023Q2_10Q", 3)], alt_gold=[],
         evidence=[E("CORNING_2023Q2_10Q", 3, "Net sales $ 3,243 $ 3,615 $ 6,421 $ 7,295")],
         numeric=N("pct", 10.3)),
    dict(id="g_s10", kind="single", role="consumer", tags=["calc", "10q", "statement_table"],
         question="What gross margin did Best Buy earn in the second quarter of fiscal 2024?",
         answer="About 23.2%: gross profit of $2,220M on revenue of $9,583M.",
         gold=[G("BESTBUY_2024Q2_10Q", 4)], alt_gold=[],
         evidence=[E("BESTBUY_2024Q2_10Q", 4, "Revenue $ 9,583 $ 10,329 $ 19,050 $ 20,976"),
                   E("BESTBUY_2024Q2_10Q", 4, "Gross profit 2,220 2,287 4,370 4,640")],
         numeric=N("pct", 23.17)),
    dict(id="g_s11", kind="single", role="consumer", tags=["earnings"],
         question="How fast did PepsiCo's organic sales grow in the first quarter of 2023?",
         answer="14.3% organic revenue growth.",
         gold=[G("PEPSICO_2023Q1_EARNINGS", 1)], alt_gold=[],
         evidence=[E("PEPSICO_2023Q1_EARNINGS", 1, "Organic revenue growth 14.3%")],
         numeric=N("pct", 14.3)),
    dict(id="g_s12", kind="single", role="consumer", tags=["calc", "earnings"],
         question="How much did Ulta's net sales grow year over year in the first quarter of fiscal 2024?",
         answer="About 12.3%: net sales of $2,634.3M vs $2,345.9M.",
         gold=[G("ULTABEAUTY_2024Q1_EARNINGS", 1)], alt_gold=[],
         evidence=[E("ULTABEAUTY_2024Q1_EARNINGS", 1, "Net sales $ 2,634.3 $ 2,345.9")],
         numeric=N("pct", 12.3)),
    dict(id="g_s13", kind="single", role="consumer", tags=["8k"],
         question="Who joined MGM's board in March 2023, and how many directors does it have after that?",
         answer="Benjamin (Ben) S. Winston was appointed; the board grew from eleven to twelve directors.",
         gold=[G("MGMRESORTS_2023_8K_dated-2023-03-01", 2)], alt_gold=[],
         evidence=[E("MGMRESORTS_2023_8K_dated-2023-03-01", 2, "Company from eleven to twelve and appointed")]),
    dict(id="g_s14", kind="single", role="health_industrials", tags=["calc", "8k"],
         question="In J&J's Kenvue split-off, how many Kenvue shares were exchanged for each J&J share tendered?",
         answer="About 8.03: 1,533,830,450 Kenvue shares for 190,955,435 J&J shares.",
         gold=[G("JOHNSON_JOHNSON_2023_8K_dated-2023-08-23", 2)], alt_gold=[],
         evidence=[E("JOHNSON_JOHNSON_2023_8K_dated-2023-08-23", 2, "190,955,435 shares of Johnson & Johnson common stock"),
                   E("JOHNSON_JOHNSON_2023_8K_dated-2023-08-23", 2, "1,533,830,450 shares of Kenvue common stock owned by")],
         numeric=N("count", 8.03)),
    # ---- 5 lead comparisons --------------------------------------------------------------
    dict(id="g_l01", kind="lead_compare", role="lead", tags=["compare", "statement_table"],
         question="Compare R&D spending at AMD and Pfizer in 2022.",
         answer="AMD spent $5,005M on R&D in 2022; Pfizer spent $11,428M (about 2.3x AMD).",
         gold=[G("AMD_2022_10K", 54), G("PFIZER_2022_10K", 54)],
         alt_gold=[G("AMD_2022_10K", 49, 50), G("PFIZER_2022_10K", 41)],
         evidence=[E("AMD_2022_10K", 54, "Research and development 5,005 2,845 1,983"),
                   E("PFIZER_2022_10K", 54, "Research and development expenses(a) 11,428 10,360 8,709")],
         numeric=N("usd_m", 5005, 11428, mode="all")),
    dict(id="g_l02", kind="lead_compare", role="lead", tags=["compare", "statement_table"],
         question="Between Boeing and 3M, who booked more top-line sales in 2021, and what were the two figures?",
         answer="Boeing: $62,286M of total revenues vs 3M: $35,355M of net sales; Boeing was higher by $26,931M.",
         gold=[G("BOEING_2021_10K", 60), G("3M_2021_10K", 45)],
         alt_gold=[G("BOEING_2021_10K", 28, 66)],
         evidence=[E("BOEING_2021_10K", 60, "Total revenues 62,286 58,158 76,559"),
                   E("3M_2021_10K", 45, "Net sales $ 35,355 $ 32,184 $ 32,136")],
         numeric=N("usd_m", 62286, 35355, mode="all")),
    dict(id="g_l03", kind="lead_compare", role="lead", tags=["compare", "statement_table"],
         question="Which had the bigger bottom line in 2022, Pfizer or J&J? Give both figures.",
         answer="Pfizer: net income attributable to common shareholders $31,372M; J&J: net earnings $17,941M.",
         gold=[G("PFIZER_2022_10K", 54), G("JOHNSON_JOHNSON_2022_10K", 47)],
         alt_gold=[G("JOHNSON_JOHNSON_2022_10K", 48)],
         evidence=[E("PFIZER_2022_10K", 54, "Net income attributable to Pfizer Inc. common shareholders $ 31,372 $ 21,979 $ 9,159"),
                   E("JOHNSON_JOHNSON_2022_10K", 47, "Net earnings $ 17,941 20,878 14,714")],
         numeric=N("usd_m", 31372, 17941, mode="all")),
    dict(id="g_l04", kind="lead_compare", role="lead", tags=["compare", "statement_table"],
         question="Which earned more in 2022, Verizon or AMD? State each company's net income.",
         answer="Verizon: net income attributable to Verizon $21,256M; AMD: net income $1,320M.",
         gold=[G("VERIZON_2022_10K", 54), G("AMD_2022_10K", 54)],
         alt_gold=[G("VERIZON_2022_10K", 58), G("AMD_2022_10K", 55, 57, 58)],
         evidence=[E("VERIZON_2022_10K", 54, "Net income attributable to Verizon 21,256 22,065 17,801"),
                   E("AMD_2022_10K", 54, "Net income $ 1,320 $ 3,162 $ 2,490")],
         # "net income" is ambiguous for Verizon: consolidated 21,748 or attributable to Verizon 21,256 (both on p.54)
         numeric=N("usd_m", [21256, 21748], 1320, mode="all")),
    dict(id="g_l05", kind="lead_compare", role="lead", tags=["compare", "statement_table"],
         question="How did Adobe's fiscal 2022 revenue stack up against AMD's 2022 revenue?",
         answer="Adobe's total revenue was $17,606M vs AMD's net revenue of $23,601M; AMD was higher by $5,995M.",
         gold=[G("ADOBE_2022_10K", 54), G("AMD_2022_10K", 54)],
         alt_gold=[G("ADOBE_2022_10K", 40, 41, 42), G("AMD_2022_10K", 49)],
         evidence=[E("ADOBE_2022_10K", 54, "Total revenue 17,606 15,785 12,868"),
                   E("AMD_2022_10K", 54, "Net revenue $ 23,601 $ 16,434 $ 9,763")],
         numeric=N("usd_m", 17606, 23601, mode="all")),
    # ---- 3 year-ambiguous ----------------------------------------------------------------
    dict(id="g_y01", kind="year_ambiguous", role="consumer", tags=["year_ambiguous", "statement_table"],
         question="What was Best Buy's revenue in 2022?",
         answer="Ambiguous: fiscal 2022 (year ended Jan 29, 2022) revenue was $51,761M; fiscal 2023 (ended Jan 28, 2023, i.e. the calendar-2022 year) was $46,298M. Either is acceptable if the interpretation is stated.",
         gold=[G("BESTBUY_2022_10K", 26), G("BESTBUY_2023_10K", 25, 40, 62)], alt_gold=[],
         evidence=[E("BESTBUY_2022_10K", 26, "Revenue $ 51,761 $ 47,262 $ 43,638"),
                   E("BESTBUY_2023_10K", 25, "Revenue $ 46,298 $ 51,761 $ 47,262")],
         numeric=N("usd_m", 51761, 46298, mode="any")),
    dict(id="g_y02", kind="year_ambiguous", role="health_industrials", tags=["year_ambiguous", "statement_table"],
         question="What were Johnson & Johnson's net earnings in 2021?",
         answer="$20,878 million (fiscal 2021, ended Jan 2, 2022); also shown as the prior-year column of the 2022 10-K.",
         gold=[G("JOHNSON_JOHNSON_2021_10K", 48, 49), G("JOHNSON_JOHNSON_2022_10K", 47, 48)], alt_gold=[],
         evidence=[E("JOHNSON_JOHNSON_2021_10K", 48, "Net earnings $ 20,878 14,714 15,119"),
                   E("JOHNSON_JOHNSON_2022_10K", 47, "Net earnings $ 17,941 20,878 14,714")],
         numeric=N("usd_m", 20878)),
    dict(id="g_y03", kind="year_ambiguous", role="consumer", tags=["year_ambiguous", "statement_table"],
         question="What were Ulta Beauty's full-year net sales for fiscal 2022?",
         answer="$10,208.6 million (fiscal 2022, ended Jan 28, 2023); the corpus files it as period 2023 (10-K and Q4 earnings release).",
         gold=[G("ULTABEAUTY_2023_10K", 37), G("ULTABEAUTY_2023Q4_EARNINGS", 1, 6)], alt_gold=[],
         evidence=[E("ULTABEAUTY_2023_10K", 37, "Net sales $ 10,208,580 $ 8,630,889 $ 6,151,953"),
                   E("ULTABEAUTY_2023Q4_EARNINGS", 1, "$ 10,208.6 $ 8,630.9 $ 6,152.0")],
         numeric=N("usd_m", 10208.6)),
    # ---- 6 off_desk (2 per non-lead role) ---------------------------------------------------
    dict(id="g_o01", kind="off_desk", role="consumer", tags=["off_desk"],
         question="What was Pfizer's total revenue in 2022?", answer="REFUSE (Pfizer is not on the consumer desk)."),
    dict(id="g_o02", kind="off_desk", role="consumer", tags=["off_desk"],
         question="How much did AMD spend on research and development in 2021?",
         answer="REFUSE (AMD is not on the consumer desk)."),
    dict(id="g_o03", kind="off_desk", role="health_industrials", tags=["off_desk"],
         question="What organic revenue growth did PepsiCo report for the first quarter of 2023?",
         answer="REFUSE (PepsiCo is not on the health_industrials desk)."),
    dict(id="g_o04", kind="off_desk", role="health_industrials", tags=["off_desk"],
         question="What was Verizon's net income in 2021?", answer="REFUSE (Verizon is not on the health_industrials desk)."),
    dict(id="g_o05", kind="off_desk", role="tech_telecom", tags=["off_desk"],
         question="What was Boeing's backlog at the end of 2022?", answer="REFUSE (Boeing is not on the tech_telecom desk)."),
    dict(id="g_o06", kind="off_desk", role="tech_telecom", tags=["off_desk"],
         question="How much revenue did Best Buy generate in fiscal 2023?", answer="REFUSE (Best Buy is not on the tech_telecom desk)."),
    # ---- 6 unanswerable ------------------------------------------------------------------
    dict(id="g_u01", kind="unanswerable", role="consumer", tags=["unanswerable", "no_filing_for_year"],
         question="What were Ulta Beauty's net sales in fiscal 2018?",
         answer="REFUSE (the corpus has Ulta filings for fiscal 2022-2024 only; no filing covers fiscal 2018)."),
    dict(id="g_u02", kind="unanswerable", role="tech_telecom", tags=["unanswerable", "year_beyond_corpus"],
         question="What was Verizon's total revenue in fiscal 2024?",
         answer="REFUSE (latest Verizon filing is the FY2022 10-K)."),
    dict(id="g_u03", kind="unanswerable", role="consumer", tags=["unanswerable", "proxy_only"],
         question="What was the total compensation of PepsiCo's CEO in 2022?",
         answer="REFUSE (executive pay is in the proxy statement, which is not in the corpus)."),
    dict(id="g_u04", kind="unanswerable", role="health_industrials", tags=["unanswerable", "nonexistent_segment"],
         question="How much revenue did Boeing's space tourism segment generate in 2021?",
         answer="REFUSE (Boeing has no such segment)."),
    dict(id="g_u05", kind="unanswerable", role="tech_telecom", tags=["unanswerable", "nonexistent_metric"],
         question="What was AMD's customer churn rate in 2022?",
         answer="REFUSE (AMD does not report a churn metric)."),
    dict(id="g_u06", kind="unanswerable", role="health_industrials", tags=["unanswerable", "forecast"],
         question="What will Pfizer's research and development spending be in 2024?",
         answer="REFUSE (no filing in the corpus forecasts 2024 R&D spending)."),
]

# numeric annotations for dev questions (expected values read from the dev answers)
DEV_NUMERIC = {
    "fb_04171": N("usd_m", 303), "fb_10285": N("usd_m", 12645), "fb_03029": N("usd_m", 1577),
    "fb_04980": N("usd_m", 4600), "fb_03069": N("pct", 4.2), "fb_10130": N("count", 63.86),
    "fb_02608": N("pct", 2.8),
}  # fb_00005 (working capital, gold 831) is manual-review: its number depends on which current items count


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


_pages = {}


def page_text(doc, page):
    if doc not in _pages:
        p = ROOT / "cache" / "pages" / f"{doc}.jsonl"
        if not p.exists():
            sys.exit(f"no parse cache for {doc}")
        _pages[doc] = {}
        for line in p.read_text(encoding="utf-8").splitlines()[1:]:
            r = json.loads(line)
            _pages[doc][r["page"]] = norm(r["text"])
    return _pages[doc].get(page)


def check(q):
    gold_pages = {(g["doc_id"], p) for g in q.get("gold", []) + q.get("alt_gold", []) for p in g["pages"]}
    for g in q.get("gold", []) + q.get("alt_gold", []):
        for p in g["pages"]:
            if page_text(g["doc_id"], p) is None:
                sys.exit(f"{q['id']}: {g['doc_id']} has no page {p}")
    for ev in q.get("evidence", []):
        if (ev["doc_id"], ev["page"]) not in gold_pages:
            sys.exit(f"{q['id']}: evidence page {ev['doc_id']} p.{ev['page']} is not a gold/alt_gold page")
        if norm(ev["text"]) not in page_text(ev["doc_id"], ev["page"]):
            sys.exit(f"{q['id']}: evidence not found on {ev['doc_id']} p.{ev['page']}: {ev['text']!r}")


def main():
    rng = random.Random(SEED)
    out = []
    for l in open(ROOT / "eval" / "questions.jsonl", encoding="utf-8"):
        if not l.strip():
            continue
        q = json.loads(l)
        q["tags"] = sorted(set(q.get("tags", []) + ["dev"]))
        q.update(source="dev", split="tune", verified=True, kind="dev", alt_gold=[], evidence=[])
        if q["id"] in DEV_NUMERIC:
            q["numeric"] = DEV_NUMERIC[q["id"]]
        out.append(q)
    n_dev = len(out)

    gen = []
    for q in GEN:
        q = dict(q)
        q.setdefault("gold", [])
        q.setdefault("alt_gold", [])
        q.setdefault("evidence", [])
        q["type"] = ("answerable" if q["kind"] in ("single", "lead_compare", "year_ambiguous")
                     else q["kind"])
        if q["type"] == "answerable":
            if not q["gold"] or not q["evidence"]:
                sys.exit(f"{q['id']}: answerable question needs gold and evidence")
        check(q)
        q.update(source="generated", verified=False)
        gen.append(q)

    # stratified holdout: round(40% of each kind), at least 1 per kind
    for kind in sorted({q["kind"] for q in gen}):
        qs = [q for q in gen if q["kind"] == kind]
        k = max(1, round(HOLDOUT_FRACTION * len(qs)))
        held = {q["id"] for q in rng.sample(qs, k)}
        for q in qs:
            q["split"] = "holdout" if q["id"] in held else "tune"
            q["tags"] = sorted(set(q["tags"] + ["generated", q["split"] if q["split"] == "holdout" else "tune"]))
    out += gen

    path = ROOT / "eval" / "questions_v2.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for q in out:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    from collections import Counter
    c = Counter((q["split"], q["kind"]) for q in out)
    print(f"wrote {path}: {len(out)} questions ({n_dev} dev + {len(gen)} generated)")
    for k in sorted(c):
        print(" ", k, c[k])
    print("split totals:", dict(Counter(q["split"] for q in out)))


if __name__ == "__main__":
    main()
