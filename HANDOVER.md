# Handover — Lost in Handoff

Everything needed to pick this up on another machine. Written 24 Sep 2026, at commit `b45c1cf`.

Paper: *Lost in Handoff: Memory-Induced Errors in Multi-Agent Financial Document Systems*, BAICONF 2026.
Abstract submitted 19 Sep · notification 26 Sep · **full paper due 31 Oct**.

---

## 1. Setup on a new machine

```bash
git clone https://github.com/animeshsrivastava571/dcal-conference.git
cd dcal-conference

python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create `.env` in the project root with both keys:

```
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
```

`OPENAI_API_KEY` is only used for embeddings in the cross-period (long-term memory)
experiment. The summarisation experiments — which are the ones that matter now —
do not need it.

Download the dataset (~17.5 MB, verifies its own size and record counts):

```bash
PYTHONPATH=src .venv/bin/python -m handoff.data.download
```

Confirm the install:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/ -q      # expect 39 passed
PYTHONPATH=src .venv/bin/python -m handoff.data.sessions # expect 707 sessions, 115 companies
```

Neither touches the API.

**Every command below needs `PYTHONPATH=src`.** If your shell has another
project's virtualenv active, prefix commands with `env -u VIRTUAL_ENV` — pip and
python will otherwise silently resolve to that other environment. This cost an
hour on the first day.

---

## 2. What is already established

All numbers below are measured, not estimated. Model: `claude-haiku-4-5-20251001`
throughout, for both the answering agent and the summariser.

### The headline finding

Compression does not change how often the agent is right. It changes **how it is
wrong**, and whether you can tell.

Twelve sessions, 196 turns per arm, run twice — once where the agent may say
"I can't answer", once where that is forbidden:

| arm | silent wrong (free → forced) | delta | accuracy delta |
|---|---|---|---|
| ceiling (no compression) | 16.3% → 13.8% | **−2.6** | +4.1 |
| 3a@3072 | 19.4% → 19.4% | 0.0 | +4.6 |
| 3a@1536 | 18.9% → 27.6% | **+8.7** | +2.6 |
| 3a@768 | 18.4% → 44.9% | **+26.5** | 0.0 |

At `@768` accuracy is **identical either way (42.9%)** while silent errors go from
18.4% to 44.9% — same score, 2.4× the wrong numbers. The ceiling row is the
control: with no compression, forbidding refusal *reduces* silent errors, so
forcing alone causes nothing. It is forcing **plus** compression.

### Dilution

Accuracy falls monotonically with compression: **76.5% → 66.8% → 61.7% → 42.9%**
across ceiling / @3072 / @1536 / @768. The ceiling stays flat or rises across turn
depth (73% → 94%) while every compressed arm declines — so it is compression, not
later questions being harder.

### Instruction is insufficient (condition 3b)

Qualifier-preserving summary prompts, paired against 3a on the same 12 sessions.
Expressed as the share of compression damage the prompt repairs:

| budget | damage above ceiling | prompt recovers |
|---|---|---|
| @3072 | 5.6 pts | 64% |
| @1536 | 13.8 pts | 37% |
| @768 | 31.1 pts | **16%** |

Prompting helps least where the damage is greatest. This confirms the abstract's
prediction that instruction would prove insufficient and structure necessary.

### Two nulls, both on full samples

- **Cross-period staleness: 0/161 stale answers** (95% CI [0.0%, 2.3%]) with the
  filing present. When the filing is withheld the agent abstains on 153 of 161
  turns rather than confabulating. Cause: LangMem's default instructions build a
  *user profile*, not a fact store, so no financial figure was ever stored to go
  stale.
- **Scale/unit loss: essentially zero.** Across 196 turns per arm, ~0 thousandfold
  errors despite 60% of filings stating "in thousands/millions/billions". The
  ~25% ×0.01 rate that does appear is percent-vs-ratio formatting, identical in
  the ceiling arm, so it is not a memory failure. Report it so a reader
  recomputing accuracy is not confused.

### The line that ties it together

Both interventions tested — permitting abstention, and qualifier-preserving
prompts — move failures from silent to loud. **Neither recovers the lost figure.**
Only the uncompressed ceiling does. Once a qualifier is gone from a 256-token
prose summary, nothing brings it back; you only choose whether the system admits
it. That is the argument for qualifiers as schema fields rather than prose.

---

## 3. What is left to run

**One thing: the two-agent handoff at full scale.**

The pipeline is built, debugged and verified on one session. Only 1 of 12 sessions
has been measured. This is the experiment that earns the paper's title — every
result above measures compression *inside* one agent, and the paper is called
"Lost in Handoff".

```bash
env -u VIRTUAL_ENV PYTHONPATH=src .venv/bin/python -W ignore \
  -m handoff.run_handoff --sessions 12 --seed 0
```

- 3 arms (ceiling, @768, @1536) × 12 sessions × ~16 turns × 2 calls per turn
- **≈ 1,200 model calls, ~25 minutes**
- Do **not** pipe it through `tail` — that buffers the log and destroys the error
  detail if something fails. It aborts cleanly on a billing or auth error.

### If you are short on API budget

| Option | Calls | Trade-off |
|---|---|---|
| `--sessions 12` | ~1,200 | Full pairing with existing results. Preferred. |
| `--sessions 6` | ~600 | Halves cost; wider intervals, still usable. |
| `--sessions 12 --no-ceiling` | ~800 | **Don't.** The handoff needs its own ceiling — a two-agent control is a different measurement from the single-agent one. |

`--no-ceiling` *is* safe for re-running short-term memory experiments, where an
identical ceiling already exists for the same sessions and seed.

### What to look for in the result

Compare the handoff accuracy against the single-agent numbers above. The open
question is whether the agent boundary adds loss on top of compression, or
whether the retrieval agent's persistent document access makes the two-agent
pipeline *more* robust. The single verified session came back at 100% for the
ceiling — above the single-agent's 82% — so a null here is a live possibility,
and would itself be a finding worth reporting.

### A contrast worth considering afterwards

An earlier draft of the pipeline gave the retrieval agent the filing **only on the
first turn of each conversation**, then made it rely on shared memory. That
collapsed to 23.5%. It was fixed because it starved the agent rather than
measuring a handoff — but it is a legitimate second architecture ("retrieve once,
then trust your notes") and the contrast would be strong:

> Whether a handoff destroys financial context depends on whether the retrieval
> agent can re-read the source. Persistent access is robust; retrieve-once-then-
> remember collapses.

That needs a second run and a flag; it is not built.

---

## 4. Rebuilding the dataset deliverable

BAICONF requires a dataset with the submission and prefers Excel. It is committed
at `dataset/` and currently holds 2,352 turn-level rows across 36 sessions.

After any new run, regenerate it:

```bash
PYTHONPATH=src .venv/bin/python -m handoff.dataset
```

Writes `dataset/turns.csv`, `dataset/summary.csv`, and
`dataset/lost-in-handoff-dataset.xlsx` (sheets: `turns`, `summary`). Every figure
in the paper is recomputable from `turns.csv` **without an API key** — useful on a
machine with limits, and it doubles as the results appendix.

Runs that aborted partway are excluded automatically by counting sessions that
actually carry results.

---

## 5. Re-scoring without spending anything

Transcripts are the source of truth; summaries are derived and disposable. If a
grading rule changes, re-grade from disk rather than re-running:

```bash
PYTHONPATH=src .venv/bin/python -m handoff.rescore            # newest cross-period run
PYTHONPATH=src .venv/bin/python -m handoff.rescore runs/<dir> # a specific run
```

This exists because a long-running process once finished after its session ended
and overwrote `summary.json` using the scorer it had loaded in memory — the
version from before a bug fix. Always re-score before quoting a number from a
`summary.json` you did not just generate.

**`runs/` is gitignored and lives only on the original machine.** The office
laptop will not have the raw transcripts. `dataset/turns.csv` **is** committed and
contains every per-turn result, which is enough for all analysis and writing.

---

## 6. Where things are

| Path | What |
|---|---|
| `docs/01-memory-qualifier-loss.md` | The design doc. Authoritative. Read before changing the experiment. |
| `docs/abstract-baiconf2026.md` | The submitted abstract. |
| `src/handoff/config.py` | Pinned model id, the ≥5-year gap rule, tolerances. |
| `src/handoff/data/` | Download, loader, cross-period pairs, session chaining. |
| `src/handoff/memory/summarization.py` | Conditions 3a and 3b; the qualifier prompts. |
| `src/handoff/agents/stm.py` | Single-agent loop. `INSTRUCTIONS` vs `FORCED_INSTRUCTIONS`. |
| `src/handoff/agents/twoagent.py` | The two-agent handoff. |
| `src/handoff/eval/correctness.py` | Scale-tolerant grading that records the matching factor. |
| `src/handoff/eval/staleness.py` | Cross-period stale-answer detection. |
| `dataset/` | The deliverable. Committed. |
| `runs/` | Raw transcripts. **Local only, gitignored.** |

---

## 7. Things that will bite you

1. **`VIRTUAL_ENV` pointing elsewhere.** `pip install` lands in another project's
   venv while `PATH` still resolves here. Use `env -u VIRTUAL_ENV .venv/bin/python -m pip ...`.
2. **Running out of API credit mid-run.** Previously killed 38 of 48 arm-runs and
   produced a `summary.json` that looked like a real experiment. The runners now
   abort on the first billing or auth error — don't remove that.
3. **Piping a background run through `tail`.** It buffers everything and you lose
   the traceback. Let it write in full.
4. **Prompt caching has a floor.** Haiku 4.5 declines to cache below ~4k tokens,
   so it only helps on longer sessions and the two-agent path. An early estimate
   of 80% savings was wrong.
5. **`text-embedding-3-small` is unversioned**, unlike the pinned Claude snapshot.
   It is the one component without a dated pin — mention it in limitations.

---

## 8. Known gaps, for the limitations section

- **One model only** (Haiku 4.5, the cheapest current Claude). The obvious
  reviewer question — *"would a stronger model avoid this?"* — is unanswered. A
  slice on Sonnet 5 across the two arms that produce the effect would close it in
  about an hour. §5c argues the loss should persist, because the default summary
  prompt is an underspecified objective rather than a capability ceiling, but
  that is a prediction, not a measurement.
- **Twelve sessions.** Fine for effect sizes this large; a reviewer may still ask.
- **Condition 3c (typed facts) is not built** and I would not build it before
  31 Oct. The abstract proposes it as the remedy; §1b notes typed facts address
  decontextualisation, which is not what these experiments measured. Propose it,
  show why the diagnosis points there, do not claim to have validated it.
- **The multi-agent result is one session.** See §3.

---

## 9. Suggested paper structure

1. **Problem** — open with the Lockheed Martin case: compression garbled one
   figure into `$3,671/share` and `$235 billion` of buybacks (the summariser even
   flagged it as "a data anomaly" and carried it forward anyway), after which the
   agent reported compensation *rose 11%* when it *fell 13%*. The arithmetic was
   correct at every step; only the remembered figure was wrong.
2. **Setup** — ConvFinQA, chained sessions, the conditions, numeric grading
   against `exe_ans` (no LLM judge).
3. **Result 1** — dilution and the depth gradient.
4. **Result 2** — the abstention interaction. The contribution.
5. **Result 3** — instruction insufficient, with the recovery curve.
6. **Result 4** — the handoff, once run.
7. **Nulls** — staleness and scale, reported plainly. A failed prediction
   honestly reported buys credibility for the rest.
8. **Implication** — qualifiers as schema fields, XBRL as precedent.
9. **Limitations** — §8 above.

Harness health for the methods section: the single-agent ceiling scores **75–80%**,
above ConvFinQA's published ~68.9% fine-tuned baseline, so the null results are
not a broken pipeline.
