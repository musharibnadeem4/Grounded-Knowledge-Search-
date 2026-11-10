# drg: grounded Q&A over a corpus of company filings

I built `ingest`, `search` and `ask` over 119 PDFs (10-K, 10-Q, 8-K, earnings) of 12 companies. Answers cite document and page.
Four desks (consumer, health_industrials, tech_telecom, lead) see only their own companies' filings.

## Run it

Python 3.10-3.13 (tested on 3.12; 3.15 has no wheels for the dependencies). On Windows install the Visual C++ redistributable first.
```
python -m venv .venv && .venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -e .
cp .env.example .env     # set GROQ_API_KEY (free key) or LLM_PROVIDER=ollama; .env is git-ignored
ingest <corpus_dir>      # needs manifest.csv in the working directory
search --role tech_telecom --k 5 "What was Adobe's operating profit for fiscal 2022?"   # JSON list
ask --role lead "Compare R&D spending at AMD and Pfizer in 2022."                       # one JSON object
python eval/run_eval.py --run-name my_run     # retrieval numbers below; see eval/README.md
```
Ingest on my laptop (`logs/ingest_full_2026-11-08.log`, `logs/ingest_c200.log`): parse 511.9 s (once, then cached), chunk 45.8 s,
embed 3,260.9 s, write 97.5 s: about an hour. The index, the parse cache and the `models/` folder (ONNX query encoder) are not in git: a fresh clone builds
them with `ingest` (the first run downloads bge-small once, then exports the encoder). Without `models/`, search still works through sentence-transformers, with a warning and a slower start.

Real output (`logs/readme_example_*.out`): `search` returns `ADOBE_2022_10K` p.54, then p.57.
The consumer desk asking about Pfizer gets `{"status": "refused", "answer": "This question concerns a company outside your desk's coverage.", "citations": []}`.
The AMD/Pfizer question returns AMD's $5,005 million (p.54 cited) and says Pfizer's figure is not in the filings: a known failure.

## How it works

```
ingest: PDF -> pdfplumber, page by page (cached) -> 200-token chunks inside a page + context header
        ("company | type | FY | page | page header") -> bge-small -> Chroma (stored text has no header)
ask:    question -> off-desk? refuse -> year beyond corpus? refuse -> parse company/year
        -> retrieve(): Chroma where-filter [role AND company AND period] -> query expansion -> dense top-14
        (one query per company for comparisons) -> one chunk per page -> 4,500-token budget
        -> LLM (JSON) -> citation check (unknown or missing citations -> refuse)
```
Pages are 1-based PDF pages. Year rule: the filing for the asked year, else the next two years. LLM: Groq (`openai/gpt-oss-120b`) or Ollama.

**Access control** lives in one place: the `where` filter inside `retrieve()`, applied in the Chroma query before ranking. `search`, `ask`, sub-queries and
the eval harness all call it; a parsed company can only narrow the role's set. Cost: a comparison needs one query per company, and a wrongly
parsed company or year can exclude the right filing. `eval/results/summary.csv` shows 0 ACL leaks in every run.

## Final numbers

Retrieval on `eval/questions_v2.jsonl`; `ctx_page_hit` = a gold page is in the chunks the LLM receives. Tune = 33 answerable questions, holdout = 9.

| set | run | ctx_page_hit | page_hit@5 | page_hit@10 | MRR@10 | ACL leaks |
|---|---|---:|---:|---:|---:|---:|
| tune, baseline | `p4_baseline_tune` | 0.697 | 0.606 | 0.697 | 0.334 | 0 |
| tune, final | `final_tune` | 0.939 | 0.606 | 0.788 | 0.380 | 0 |
| holdout, baseline | `p6_baseline_holdout` | 0.556 | 0.333 | 0.444 | 0.296 | 0 |
| holdout, final | `final_holdout` | 0.889 | 0.444 | 0.778 | 0.405 | 0 |

Answers (tune, 41 questions; refusal recall = off-desk and unanswerable questions refused; confident error = a wrong final figure stated, among the 20 numeric-gold questions):

| model | run | status acc. | refusal recall / precision | numeric acc. | confident error | citation hit |
|---|---|---:|---:|---:|---:|---:|
| gpt-oss-120b, baseline config | `p4_baseline_tune_answers_rescored4` | 0.927 | 1.00 / 0.727 | 0.800 | 0.00 | 0.567 |
| gpt-oss-20b, final config | `final_tune_answers_oss20b_rescored4` | 0.756 | 1.00 / 0.444 | 0.600 | 0.10 | 0.565 |

Holdout, final config, gpt-oss-20b (`final_holdout_answers_oss20b_rescored4`): status 0.769, numeric 0.625, confident error 0.00, citation hit 0.833.
I measured the final configuration's answers with gpt-oss-20b because gpt-oss-120b's free daily token cap was spent. The two rows are different models: do not subtract them.

Cold start (`logs/cold_latency_*.json`): `search` median 1.69 s with the ONNX encoder (1.65-1.86 s) against 18.86 s for the sentence-transformers path
(17.86-100.88 s; a day earlier 7.19 s, `eval/results/EXPERIMENT_LOG.md`). `ask` with the LLM call stubbed: 1.97 s against 17.84 s.
One real `ask`: 1.6 s in the LLM, 3.2 s in total inside the process (`logs/readme_example_ask_lead.stderr`). Hardware: 13th-gen Intel i7 laptop, Windows 11.

## Known limitations

* The eval set is small. 34 of 54 questions are generated by me and not yet hand-verified; holdout has 9 answerable questions (one is 11 points).
* The query-expansion synonym map is hand-written, after I had read the tune failures. Tune gains are optimistic; holdout agrees.
* Gold is a page. The same figure often sits on other pages, so strict page metrics undercount some correct retrievals.
* Table chunks and chart text can mislead: the model once took a chart label for AMD's R&D figure. The citation check cannot catch that.
* The model sometimes answers without citation markers and the check then refuses it (5 of 33 answerable on `final_tune_answers_oss20b`).
* 200-token chunks cover more but rank worse at the top: page_hit@5 0.606 against 0.758 for the 350-token index (`p5_x2_expand_alone`).
* Groq's free tier allows about 200,000 tokens a day: about 45 answered questions at the current context size (`eval/README.md`).

Cold-start figures above move with machine state. Open failures: EXPERIMENTS.md. Decisions: [DECISIONS.md](DECISIONS.md). Experiments: [EXPERIMENTS.md](EXPERIMENTS.md). Eval: [eval/README.md](eval/README.md).
