# eval/

Everything that produces the numbers in the top-level README / EXPERIMENTS.md. Run from the repository root with the venv active.

## The eval set: `questions_v2.jsonl` (54 questions)

* **20 dev questions** from the assignment (`eval/questions.jsonl`, converted by `convert_dev.py`). Answerable only. Verified by the course.
* **34 generated questions**, written by me (with an AI assistant) from the corpus by `build_questions_v2.py`, which fails unless every `evidence`
  line is found on the stated gold page in the parse cache. Mix: 14 single-company answerable (statement tables, calculations from two figures,
  10-Q/earnings/8-K items), 5 lead comparisons across two companies (including AMD vs Pfizer R&D 2022), 3 year-ambiguous, 6 off-desk
  (2 per non-lead role), 6 unanswerable (no filing for that year, year beyond the corpus, proxy-only information, nonexistent segment,
  nonexistent metric, a forecast). Method and limits: [`generate_notes.md`](generate_notes.md).
  **All generated questions are `"verified": false`**: I have not yet checked each by hand.
* **Split.** `tune` = the 20 dev + 21 generated (41 questions, 33 answerable). `holdout` = 13 generated questions chosen with a fixed seed,
  stratified by question kind (9 answerable). Experiments were decided on `tune` only; `holdout` was first run for the final evaluation.
  With 9 answerable holdout questions one question is 11 points: read holdout as a check against overfitting, not as a precise estimate.
* Fields: `gold` (pages scored by retrieval metrics), `alt_gold` (other pages with the same figure; accepted for *citations* only), `evidence`,
  `numeric` (expected figure, unit kind, tolerance mode), `split`, `verified`.

## Metrics, and why these

| metric | meaning | why |
|---|---|---|
| **`ctx_page_hit`** (primary) | a gold page is among the chunks that `ask` actually passes to the LLM (same retrieval, per-company sub-queries, page cap and token budget as `ask`) | the LLM can only use what it is given; `ask` passes ~14 chunks, so top-5 ranking alone understates what matters |
| `ctx_gold_recall` | share of the gold pages in that context | multi-page questions (ratios across statements) need all their pages |
| `page_hit@k`, `gold_page_recall@k`, `doc_hit@k`, `MRR@10` | classic ranking metrics over chunks, k = 5/10/20 | what `search --k n` returns; secondary here |
| **ACL leaks** | results from a company outside the role's desk | must be 0 for every run |
| status accuracy, **refusal precision / recall** | answered when it should, refused off-desk / unanswerable | refusing correctly is part of the task |
| **confident error rate** | among answerable questions with numeric gold: share with status=answered and a wrong number (a refusal is not one). Reported next to numeric accuracy and the refusal rate on the same questions; the three sum to 1 | a wrong number stated with confidence is worse than a refusal; accuracy alone hides it |
| **numeric accuracy** | the expected figure appears in the answer, thousands/millions/billions normalised, 1 % or rounding-aware tolerance | answers are checked on the figure, not the wording |
| **citation hit / precision** | a cited (doc, page) is in `gold` or `alt_gold` / share of citations that are | answers must point at the right page |
| ungrounded-number warnings | numbers in the answer not found in a cited chunk | cheap hallucination signal |
| latency | retrieval p50/p95 (warm); end-to-end per question in `--answers` runs (net of rate-limit waits is reported too) | |

### Outcomes of numeric-gold questions (five rates, summing to 1)

Computed for the answerable questions that have a `numeric` gold. Reported next to each other because numeric accuracy alone hides *how* a
system fails.

| outcome | definition |
|---|---|
| `correct` | status answered and the expected figure(s) are stated (this rate equals numeric accuracy) |
| `partial` | multi-part question (several expected figures), at least one stated correctly, and the answer explicitly marks the rest unavailable |
| `soft_refusal` | status answered, but the answer explicitly says the asked figure is unavailable or cannot be computed and states no expected figure; inputs listed on the way do not count as the figure |
| `refused` | status refused |
| `confident_error` | anything else that was answered: a wrong final figure stated without saying it is unavailable |

"Explicitly says unavailable" is a wording heuristic (`drg/unavailable.py`: "cannot be computed", "not disclosed / present / provided", "does not contain", "no information", ...).
Only the expected figures are checked: other numbers in the answer are not judged, so `partial` means "the expected figures that were stated are right", not "every number is right".
`answered_wrong_rate` keeps the earlier two-way reading (answered and numeric wrong = confident errors + soft refusals + partial answers) for comparison.

**How this definition came about.** The first version counted every answered-but-wrong question as a confident error (`*_rescored3` files: 6 of 28
numeric-gold questions). I then read each of those answers: only 2 were wrong figures (g_s04, g_s11); 2 were "cannot be computed" answers and 2 were
multi-company answers with the right figure for one company and the other explicitly unavailable. I changed the scorer after inspecting these cases, and
applied the new definition uniformly to every answer run (`*_rescored4`, no LLM calls); no case was reclassified by hand.

Non-numeric answered questions are listed in a *Manual review* section of the `.md` for me to read.

## Commands

```
python eval/build_questions_v2.py                  # rebuild questions_v2.jsonl (checks every evidence line)
python eval/run_eval.py --run-name my_run          # retrieval only; defaults: questions_v2.jsonl, split all, ./index
python eval/run_eval.py --run-name my_run --split tune        # what to use while tuning
python eval/run_eval.py --run-name my_run --set QUERY_EXPAND=False --set ASK_K=8    # any drg/config.py flag
python eval/run_eval.py --run-name my_ans --answers [--max-llm-calls 20] [--sleep 8]   # live LLM (needs .env)
python eval/compare_runs.py runA runB --metric ctx # per-question better/worse/same (also: rank, askk, answer)
python eval/inspect_run.py my_run                  # failure analysis of a run (needs the index it was run on)
python eval/rescore_answers.py my_ans              # re-score stored answers with the current scorer (no LLM)
```
Results go to `eval/results/<run>.json`, `.md` and a row in `summary.csv`; a run name that exists is refused, nothing is overwritten.
The `.md` reports **tune and holdout in separate tables**. `eval/results/INDEX.md` lists every run that exists.

**Runtime.** The no-flag retrieval run on 54 questions took 97.5 s on my laptop (Intel i7-13th gen, 16-32 GB; `logs/final_all_default_check.log`).
Answer runs are paced by the provider: with Groq's 8,000 tokens/minute limit I measured a p50 of 22.9 s per live question including rate-limit
waits, plus `--sleep 8` (`final_tune_answers_oss20b` in `eval/results/summary.csv`).

**Token cost of `--answers`.** Before spending anything, `run_eval.py --answers` prints an estimate to stderr (`eval/cost_estimate.py`:
~4.5k tokens per live call for the current configuration). Observed: the 200,000-token daily cap of Groq's free tier was used up by
49 live calls on `gpt-oss-120b` (36 in `logs/p4_baseline_tune_answers.log` + 13 in `logs/p5_x2_answers.log`) and by 46 on `gpt-oss-20b`
(11 + 35 in `logs/final_holdout_answers_oss20b.log` and `logs/final_tune_answers_oss20b.log`), i.e. about 4.0-4.3k tokens per question.
So a full run (about 36 questions reach the LLM on tune) costs most of one day's free quota. Identical prompts are answered from
`cache/llm` for free (`--no-llm-cache` disables it); `--max-llm-calls N` stops cleanly and marks the run PARTIAL; `ask` itself refuses
with "LLM quota exhausted (provider daily limit)" instead of waiting when the provider returns a daily-cap 429.
