# Idea 01 — Memory-induced failure modes in financial document agents

**Status:** locked as a BAICONF candidate, 12 Sep 2026. Nothing built yet.
**Working title:** *Lost in Handoff: Memory-Induced Errors in Multi-Agent Financial Document Systems*
**Venue constraints:** see [README](README.md)

> **Honest calibration.** ~70% a solid BAICONF paper. ~15% a FinNLP paper — **do not send it there.** This is a measurement paper, positioned honestly against adjacent published work. It does not claim a novel mechanism, and it should not pretend to.

---

## 1. The problem, plainly

An analyst asks an AI assistant about JPMorgan's 2007 annual report. It answers and stores notes.

Later, they ask about JPMorgan's **2018** report. The stored note reads *"JPMorgan revenue $X"* — **with no year attached**, because the summarisation step dropped it. The assistant answers the 2018 question with the 2007 figure.

**The note was never wrong. It stopped being the answer to the question being asked.**

The general principle, and the reason this is a *finance* paper rather than a generic memory paper:

> **A financial figure is meaningless without its qualifiers, and summarising strips qualifiers.**

*"Revenue was 233"* is not a fact until you know the **period**, **entity**, **scale** ($233m vs $233bn — wrong by 1000×), **currency**, **basis** (reported vs adjusted, GAAP vs IFRS), and **consolidation level**. Accounting standards *are* rules about which qualifiers a number must carry. Finance has an unusually dense set of them; a summariser trained to be concise strips exactly these, because they read like clutter.

## 1a. Naming: "handoff" is the title's concept, not a mode

**The title's "handoff" means the general idea** — information passing between stages and losing something each time. The pipeline is a chain of handoffs (`tool → agent → summary → summary → store → retrieval → other agent`) and the paper's distinctive contribution is **localising loss at each of them**.

**The fifth failure mode is therefore named `agent-boundary loss`, not "handoff loss."** Using "handoff" for both created a collision: a reader met the title expecting a paper about the agent boundary, then found it was one mode of five.

Keep this separation in all writing.

## 1b. Three families of harm — the organising frame *(added 13 Sep)*

The five failure modes are not a flat list. They are **three kinds of harm** compression causes, and the distinction determines what the remedy can and cannot fix.

| Family | Mode(s) | What compression does |
|---|---|---|
| **Omission** | dilution | drops what should have been kept |
| **Corruption** | error propagation | carries a wrong value forward |
| **Decontextualisation** | staleness, cross-entity contamination, agent-boundary loss | keeps the value, strips what makes it mean anything |

**Three things this buys:**

1. **Every mode gets set up.** Previously dilution and error propagation appeared in the Aims with no explanation in Need — a reader met the terms cold.
2. **It explains why the remedy covers three of five.** Typed facts fix **decontextualisation**. Omission and corruption need different treatment. Stated openly this is a *finding*, not a gap — and it sets up future work. Measuring more than you fix is normal and honest.
3. **It isolates what is finance-specific.** Omission and corruption occur in any domain. **Decontextualisation is where finance is unusual**, because accounting mandates that a figure carry its entity, period and unit. That is the defensible territory, and the taxonomy makes it visible rather than implicit.

**The answer to "why measure what you don't fix":**

> Compression harms in three ways and only one is specific to finance. We measure all three and remedy the one the domain already has a standard for.

**Record of a bad call:** an earlier review recommended *narrowing* to three qualifier-loss modes for coherence. That was optimising tidiness over substance — five measured modes is more empirical contribution, which is the currency at an applied venue. Animesh pushed back and was right.

## 2. The four failure modes

**Short-term memory — within one conversation**

1. **Context dilution** — as the conversation lengthens, relevant facts get crowded out; accuracy falls with turn depth.
2. **Error propagation** — a wrong figure at turn *n* is carried forward and reused at turns *n+1…*, compounding.

**Long-term memory — across sessions**

3. **Staleness** — a figure stored from FY(*t*) answers an FY(*t+k*) question.
4. **Cross-session bleed** — one company's figures appear in another's answers.

Why each bites in finance: conversations are long and numeric and the latest figure usually supersedes; ConvFinQA turns explicitly chain on earlier answers, so a bad number corrupts downstream arithmetic measurably; financial facts are period-bound by construction; and cross-session bleed in a bank is a potential **information-barrier breach** — a control failure, not noise. That last point is the one no other memory paper is positioned to make.

## 3. Measurable qualifiers

| Qualifier | Measurable on this data? |
|---|---|
| **Period** | ✅ year in the FinQA id, and in most question text |
| **Entity** | ✅ ticker in the id |
| **Scale / unit** | ✅ table headers carry *"(in millions)"* |
| Basis | ⚠️ partial — row labels say "adjusted", "continuing operations"; treat qualitatively |
| Currency | ❌ weak — S&P 500 filings are almost all USD |
| Restatement | ❌ too hard for six weeks |

Three properly, one qualitatively. **The scale result may be the best one** — a dropped unit is a 1000× error, far more alarming to a practitioner than a stale year.

## 4. Five conditions

Vary only documented LangMem parameters, bracketed by two plain references. Every finding then maps to a setting a practitioner can change the same day.

| # | Condition | What it is |
|---|---|---|
| **F** | Floor — no memory | each turn answered independently |
| **3a** | **LangMem off the shelf** | defaults: `schemas=None`, bare summary prompts, `namespace=("memories","{langgraph_user_id}")` |
| **3b** | LangMem + period-aware prompts | custom summary prompts requiring figures retain their qualifiers |
| **3c** | LangMem + structured and scoped | Pydantic `schemas` with `fiscal_period`; entity in the `namespace` |
| **C** | Ceiling — full history, no summarisation | nothing dropped or compressed |

**F** says what memory was worth at all; **C** says how much was recoverable. Without **C**, "3c is better" is weak — with it, you can say *"recovers x% of what full history retains."*

Agent loop on **LangGraph** (checkpointer + store) for orchestration only; the memory policy is what varies.

### How each mode is measured

| Mode | Measurement |
|---|---|
| Dilution | turn-level execution accuracy vs turn depth |
| Error propagation | wrong answer at turn *n*; accuracy of dependent vs independent later turns |
| Staleness | cross-period pairs — **stale-answer rate** = share of FY(*t+k*) questions answered with the FY(*t*) value |
| Cross-session bleed | session 1 on company X, session 2 on Y; share of Y answers containing X's figures |

Report the **residual against C**, not only the delta from 3a.

## 4b. Session construction — long chains *(added 13 Sep, fixes a design flaw)*

**LangMem's summarisation is token-triggered.** From the source:

> *"once the cumulative number of message tokens reaches `max_tokens_before_summary`, all messages within it are summarized"*

It does not fire until a threshold is crossed. And **ConvFinQA conversations average ~3.6 turns** (14,115 turns / 3,892 conversations).

**As originally designed, summarisation would probably never have fired and we would have measured nothing.**

**The fix:** chain **4–5 ConvFinQA conversations about the same company into one 15–20 turn session.** Real questions, no synthetic content. For the bleed test, chain conversations about *different* companies — that is precisely the condition that triggers it. Also **sweep `max_tokens_before_summary`** rather than trusting one default.

**This changes the headline from a table to a curve** — qualifier retention against turn depth, with a visible cliff where summarisation fires and further drops at each subsequent round:

```
qualifier retention
100% ┤━━━━━━━━━┓
     │         ┃  ← summarisation fires
 60% ┤         ┗━━━━━┓
     │               ┗━━━━  ← fires again
 30% ┤
     └──┬────┬────┬────┬────
        5   10   15   20  turns
```

It answers the question practitioners actually have: **how many turns before my agent starts losing years?**

**Compounding across rounds.** The existing-summary prompt says *"**Extend this summary**"* — each round re-summarises the previous summary. Lossy compression applied repeatedly, so a qualifier surviving round 1 may not survive round 3. At 20 turns there are several rounds, so measure **degradation per round**, not just before/after.

## 4c. Which half of LangMem tests which failure

LangMem has two independent modules doing different jobs:

| Failure | Layer | Module |
|---|---|---|
| Dilution | within-session | `short_term/summarization.py` |
| Error propagation | within-session | `short_term/summarization.py` |
| Staleness (wrong year) | across sessions | `knowledge/extraction.py` |
| Cross-company bleed | across sessions | `knowledge/extraction.py` |

Within a session there is a real choice: **pass the full state every turn** (LangGraph's default, via the checkpointer) **or** summarise when long. The first **is our ceiling condition (C)**.

The §4b long-session work targets the *within-session* module. The cross-year work targets the *across-session* module. Two experiments, two modules, four failure modes.

## 4d. Source verified against the INSTALLED package — 16 Sep 2026 ✅

Earlier claims were read from GitHub `main` on 12 Sep. Re-verified against the package actually installed in `.venv`. **Every claim holds.**

### Versions to pin in the paper

```
langmem               0.0.30
langgraph             1.2.11
langgraph-checkpoint  4.2.0
langchain-core        1.6.3
python                3.12.7
```

### STM — all verified in `langmem/short_term/summarization.py`

| Claim | Evidence |
|---|---|
| Default prompt never mentions numbers, dates or units | `"Create a summary of the conversation above:"` |
| Each round re-compresses the **previous summary** | `"Extend this summary by taking into account the new messages above:"` |
| Nowhere for a qualifier to live | `RunningSummary.summary: str` — flat string |
| Fixed budget | `max_summary_tokens = 256` |
| **No preservation mechanism exists** | grep for `preserve\|pin_\|exclude_\|protect` → **0 matches** |
| System message is exempt | line 123, `isinstance(messages[0], SystemMessage)` → `messages = messages[1:]` |
| Pinning costs budget one-for-one | line 128, `max_remaining_tokens -= token_counter([existing_system_message])` |

### LTM — all verified in `langmem/knowledge/extraction.py`

| Parameter | Default |
|---|---|
| `schemas` | `None` — unstructured |
| default `Memory` model | `{content: str}` — a bare string |
| `namespace` | `('memories', '{langgraph_user_id}')` — **user-scoped, not entity-scoped** |
| `enable_deletes` | `False` |
| `query_limit` | `5` |

### 🔑 NEW FINDING — the LTM default instructions actively instruct terseness

The `create_memory_store_manager` default `instructions` is a long prompt not previously read. It contains:

> *"Consolidate and **compress** redundant memories to maintain information-density; strengthen based on reliability and recency; **maximize SNR by avoiding idle words.**"*

**This is stronger evidence than anything we had.** For STM the claim is that the prompt *fails to protect* qualifiers. For LTM the default prompt **actively instructs the model to drop what it judges to be noise** — and to a compressor, *"(FY2015, $ millions)"* is exactly what "idle words" looks like.

Also present: *"Prefer dense, complete memories over overlapping ones."*

**Use this in the paper body**, not the abstract — the abstract's argument is structural (*"nowhere for a qualifier to live"*), which is stronger and more general than a prompt-wording argument. This quote is supporting evidence for the mechanism section.

## 5. The fix — three settings, no fork

LangMem source read from `main`, 12 Sep 2026 (MIT, 1,660 stars, pushed 2026-09-09). **Everything we vary is an injectable parameter.**

**The default summary prompt, verbatim:**

```
"Create a summary of the conversation above:"
```

That's the whole instruction. No mention of numbers, units, dates or periods. **That is the mechanism for qualifier loss, locatable in two lines of source.** And `RunningSummary.summary` is a flat `str` — nowhere to carry a period except inside prose, where the next round can drop it.

| Rule | LangMem lever | Condition |
|---|---|---|
| Period tagging | `schemas=[Fact(metric, value, scale, entity, fiscal_period, source_doc)]` | 3c |
| As-of filtering | `store.search(..., filter={"fiscal_period": ...})` | 3c |
| Recency dominance | post-retrieval ordering | 3c |
| Entity scoping | `namespace=("memories","{user}", company_id)` | 3c |
| Numeric pinning | `initial_summary_prompt` / `existing_summary_prompt` | 3b |

**`namespace` defaults to `("memories", "{langgraph_user_id}")` — scoped by *user*, not by the entity discussed.** So cross-session bleed is the documented default behaviour. Fixed by putting the company in the namespace.

⚠️ **Pin the LangMem version in the paper.** The API has moved before.

## 5b. Six nuances, in priority order *(added 13 Sep)*

1. **Where does the qualifier die?** Four candidate points: `tool output → agent's restatement → summary → later retrieval`. The tool output carries table headers ("in millions", year columns); the agent's *restatement* may drop them before summarisation touches anything. **Localising the loss is worth more than measuring it** — if half occurs at restatement, the summary prompt is the wrong fix.

2. **Which qualifier dies first?** They are not equally fragile — year is salient, **units read as clutter**. Rank by survival rate. *"Units are lost 3× more often than years"* is concrete and quotable, and units are the more dangerous loss (a 1000× error).

3. **Position effects.** The source processes messages *"from oldest to newest"*, so **early facts are summarised more times**. Predict: a figure from turn 2 is far more degraded by turn 20 than one from turn 14. Pairs directly with §4b.

4. **Silent vs visible failure.** *"Revenue was 233"* is **visible** ambiguity a human may catch. *"Revenue in 2018 was $233bn"* when that is the 2015 figure is **silent corruption**. Report separately — the second is what matters in finance.

5. **Computation questions should fail harder.** FinQA items like *"percentage growth from 2016 to 2017"* need **two** correctly-labelled years; lookups need one. **That difficulty axis is already in the data**, free.

6. **Similar companies should bleed more.** Two banks share metric names and magnitudes; a bank and a retailer do not. Pair same-sector vs cross-sector — it tells practitioners exactly when the default namespace is dangerous.

**Cheap extras if time allows:** sweep `max_summary_tokens` (default 256) to find the compression cliff; compare two model sizes, since a smaller model losing more qualifiers is a cost-quality finding this audience values.

**Measurement advantage:** ConvFinQA ships `exe_ans`, the executed answer — so correctness is checkable **numerically**, not by an LLM judge. Fewer arguments with reviewers.

## 5c. Model choice — a confound that must be controlled *(added 13 Sep)*

**Summarisation is lossy by definition.** Mapping many tokens to few means information must go; there is no lossless option. The question is *which* information is prioritised for survival — and that is set by the prompt, which says only *"Create a summary of the conversation above:"*. Nothing about numbers, units or dates.

**So the model is not failing. It is succeeding at the wrong objective.** A good prose summary reads better without "(FY2015, $millions)" cluttering it. This is an **objective-specification problem, not a capability ceiling** — which is precisely why the prompt fix (3b) is the right intervention.

**Loss may therefore not be monotonic in model quality.** Two plausible outcomes:
- *Better model → less loss*: it infers unprompted that financial figures need their periods.
- *Better model → more loss*: it writes better prose, and better prose drops parenthetical decoration.

**Either result is publishable, and one is much stronger:**

| Result | Meaning |
|---|---|
| Loss shrinks with model size | *"You can buy your way out — here is the cost curve"* |
| **Loss persists at the frontier** | ***"You cannot buy your way out. You must change the configuration"*** |

Working expectation: loss **persists**, because capability does not fix an underspecified objective. To be measured, not asserted.

### Three design consequences

1. **Hold the model constant within a condition.** If 3a runs on a small model and 3b on a large one, the comparison is meaningless. Same model across all five conditions, stated explicitly in the paper.
2. **Separate the two models in play.** The **summariser** does the compression; the **answerer** uses the memory. Hold the answerer fixed and vary only the summariser — otherwise a better answer cannot be attributed to better memory rather than a better reader.
3. **Model size is a second axis, not a nuisance parameter** — if time allows.

### What to use

- **Primary: a mid-size open model** — reproducible, cheap, pinnable. Carries the full grid.
- **Secondary: one frontier API model** on a subset — enough to answer "does capability close the gap?"
- **Pin every version.** API models change silently behind the same name, which would make the numbers unreproducible — and is, neatly, the exact drift problem `ideas/01` is about.

**Cost bounding:** 5 conditions × 4 modes × N sessions × 2 models adds up. Open model runs the full grid; frontier model runs one slice.

**Not in the abstract, deliberately.** It is a control, not a result, and the abstract is at 498/500 words. It would only belong there if varying model size became a headline finding — which requires committing to run it.

## 5d. What counts as a qualifier, and how to measure retention *(added 13 Sep)*

### Broaden the definition rather than adding dimensions

Period, entity and scale are not the whole set. A **qualifier is anything that constrains when or whether the number is true**:

| Type | Example | Note |
|---|---|---|
| Period | FY2015 | in the original three |
| Entity | JPM | in the original three |
| Scale / unit | $ millions | in the original three |
| **Basis** | *"excluding the divestiture"*, *"adjusted"*, *"unaudited"*, *"continuing operations"* | **possibly the most dangerous** |
| **Temporal scope** | *"as at 31 March"* vs *"for the year ended"* | point-in-time vs period |
| **Hedges** | *"approximately"*, *"preliminary"* | calibration |
| **Negations** | *"did not include"* | reverses meaning |

**Basis loss is worse than being wrong.** Drop *"excluding the divestiture"* and the figure is **literally correct and completely misleading** — nothing looks off, so nothing gets caught. A wrong number can be spotted; an unqualified correct one cannot.

### Measuring representativeness — extrinsic and intrinsic

- **Extrinsic (primary):** can the agent still answer correctly? Ties loss to consequence. This is the main measure.
- **Intrinsic (secondary):** does the summary retain the facts? Catches degradation *before* it produces a visible error.

### ⚠️ Do not use semantic similarity as the metric

A natural instinct, and the wrong tool — **it is blind to exactly the errors that matter**:

| Source | Summary | Cosine sim | Real error |
|---|---|---|---|
| "$233 **million**" | "$233 **billion**" | ~0.99 | **1000×** |
| "Revenue in **2015**" | "Revenue in **2018**" | ~0.99 | wrong answer |
| "grew, **excluding the divestiture**" | "grew" | ~0.95 | materially misleading |

Embedding similarity measures **topical** closeness; financial errors are **precision** errors. One token flips, correctness dies, the vector barely moves. Same failure mode as BLEU/ROUGE on factual QA.

**Use extraction-and-compare instead:** extract `(metric, value, scale, period, entity, basis)` from source and from summary, compare **field by field, exact match**. That yields a **qualifier retention rate** — deterministic, no judge, no embeddings.

### But keep similarity as a negative control — it is a result

Report cosine similarity **alongside** qualifier retention and show the divergence: similarity holding near ~0.95 while retention collapses to ~40%.

**That is a strong figure and a genuine warning:** the way practitioners currently sanity-check summaries — embedding similarity, or an LLM judge saying "looks good" — **would miss every one of these errors.** It converts a methodological aside into a finding practitioners can act on.

## 5e. Multi-agent scope — REQUIRED, added 13 Sep ⚠️

**This is a design change, not a framing change. It must be built.** The abstract now claims a multi-agent system; a single-agent implementation would make the title and Methods section false.

### What changes

Run the pipeline as **two agents sharing memory**, not one:

```
retrieval agent  ──handoff──▶  analysis agent
   (gathers figures)              (consumes them, answers)
        │                              │
        └────── shared memory ─────────┘
```

**Three consequences:**

1. **A new compression point.** The handoff is another place qualifiers are dropped — the retrieval agent summarises for the analysis agent, independently of LangMem's own summarisation. Loss now compounds across *rounds* **and** *handoffs*.
2. **A new blast radius.** With shared memory, one agent's qualifier loss corrupts *another agent's* output. The error crosses an ownership boundary — which in a bank is a different class of problem from a single agent being wrong.
3. **A fifth failure mode: agent-boundary loss.** The other four (dilution, error propagation, staleness, cross-entity contamination) are unchanged.

### Build cost

Small — one additional node in the LangGraph graph plus the handoff payload. But it must not be skipped, and it means:
- Every condition (F, 3a, 3b, 3c, C) runs through **both** agents
- Qualifier retention is measured at **each** stage: tool output → retrieval agent's restatement → **handoff** → analysis agent's answer → summary → later retrieval
- The §5d extraction-and-compare check runs at each of those points, which is what localises the loss

### ⚠️ Use a DOCUMENTED handoff pattern, not a bespoke one

**This protects the paper's strongest property.** The rest of the design measures **shipped defaults** — LangMem's bare summary prompt, its user-scoped namespace. Objective artefacts we found rather than chose. That is what makes the finding hard to argue with.

**The handoff is different: we design it.** A reviewer can fairly say *"you chose how the agents pass information, so you chose the result."* That criticism does not apply to the single-agent version.

**So use LangGraph's shipped supervisor / handoff primitives as documented. Do not hand-roll the handoff summarisation.** Then we are still measuring a default — just a second one.

### Scope protection

Five modes × five conditions × two agents × six measurement points, in six weeks. The danger is not impossibility — it is doing all of it shallowly rather than some of it well.

| | |
|---|---|
| **Cut first** | model-size axis; `max_summary_tokens` sweep; basis and temporal-scope qualifiers |
| **Cut last** | the handoff measurement — it justifies the title |
| **Never cut** | the correctness gate |

### Why it is worth the scope increase

It matches production reality (real financial systems are multi-agent), it broadens the audience at a venue whose workshop programme includes Agentic AI, and it sharpens the compounding argument — each summary re-summarises the previous summary, and each handoff re-compresses again.

**Title history:** *"Broken Telephone"* was considered for exactly this compounding metaphor and **rejected — the idiom does not travel** ("Chinese whispers" in Indian/British English, "telephone" in American). A title that needs explaining is a bad title. *"Lost in Handoff"* is plain, universal, and makes the multi-agent claim concrete rather than decorative.

## 6. Data — verified, not assumed

- **ConvFinQA** — `github.com/czyssrs/ConvFinQA`, EMNLP 2022. 3,037 / 421 / 434 conversations; conversation- and turn-level. Ships a 17.5 MB `data.zip`.
- **FinQA** — `github.com/czyssrs/FinQA`, **CC-BY-4.0**, S&P 500 earnings reports **1999–2019**. Plain JSON (train 78 MB).

### Worked example + coverage figures — measured from the data, 13 Sep

Downloaded `data.zip` and inspected it directly. A real record:

**`id: Single_MRO/2007/page_134.pdf-1`** — Marathon Oil, 2007 report.

```
                                          2007      2006      2005
weighted average exercise price/share    $ 60.94   $ 37.84   $ 25.14
expected volatility                        27%       28%       28%
```

| Turn | Question | `exe_ans` |
|---|---|---|
| 0 | what was the weighted average exercise price per share in **2007**? | 60.94 |
| 1 | and what was **it** in 2005? | 25.14 |
| 2 | what was, then, **the change** over the years? | 35.8 |
| 3 | what was the weighted average exercise price per share in 2005? | 25.14 |
| 4 | and how much does **that change** represent in relation to **this 2005**…? | 1.42403 |

**Three properties this confirms:**

1. **Turn 1 is the qualifier problem live.** *"and what was **it** in 2005?"* never names the metric — it exists only in turn 0. If summarisation drops "weighted average exercise price per share", turn 1 becomes unanswerable.
2. **Error propagation is native to the data**, not induced. Turns 2 and 4 depend on earlier answers.
3. **The dependency graph is machine-readable.** `turn_program` for turn 4 is `subtract(60.94, 25.14), divide(#0, 25.14)` — `#0` references turn 2. **Dependent vs independent turns can be separated programmatically**, which is exactly what the error-propagation measurement needs. Free.

`exe_ans_list` confirms **per-turn numeric ground truth**.

### Measured coverage (train + dev, 3,458 conversations)

| Metric | Value |
|---|---|
| ids parsed to `TICKER/YEAR` | **3,458 / 3,458 (100%)** |
| distinct companies | 133 |
| **companies with a ≥5-year span** | **89** |
| **candidate cross-period year pairs (≥5yr gap)** | **964** |
| turns per conversation | mean **3.64**, max 9 |
| chaining 5 conversations | **~18 turns** |

**This de-risks two open concerns:**
- *"Cross-period pairs might be too thin"* — **964 candidate pairs across 89 companies.** Ample.
- *"Will chaining reach 15–20 turns?"* — **5 conversations ≈ 18 turns.** Exactly the target, no padding needed.

⚠️ **Parser detail:** ConvFinQA ids carry a **`Single_` / `Double_` prefix** (300/121 in dev) that FinQA ids do not. Strip it before parsing `TICKER/YEAR`:

```python
core = i.split('_',1)[1] if '_' in i.split('/')[0] else i
m = re.match(r'([A-Z0-9.\-]+)/(\d{4})/', core)
```

### Dataset sizes — verified 13 Sep

| | Size | Role |
|---|---|---|
| **ConvFinQA** | 3,892 conversations (train 3,037 / dev 421 / test 434); **14,115 turns** (11,104 / 1,490 / 1,521) | **multi-turn — the evaluation set.** All experiments run here |
| **FinQA** | ~8,281 QA pairs (dev **883**, test **1,147** counted directly; train is the 78 MB file) | **single-turn — the source corpus.** ConvFinQA is built from it and inherits its documents and `TICKER/YEAR` ids |

⚠️ **FinQA is not conversational.** An earlier abstract draft described both as "analyst conversations", which was wrong. ConvFinQA supplies the multi-turn structure the whole design depends on; FinQA supplies the report corpus, the id convention, and a larger pool for constructing cross-period pairs when ConvFinQA alone yields too few at a ≥5-year gap.

**Checks run 12 Sep 2026:**

**No structured fiscal-period field.** But FinQA ids follow the FinTabNet convention, verified on real records:

```
ILMN/2007/page_78.pdf-2      JPM/2007/page_157.pdf-1
BLK/2012/page_160.pdf-1      JPM/2018/page_110.pdf-5
```

`TICKER/YEAR/page_N.pdf-index` → **company and report year come free.** (JPM at both 2007 and 2018 in an 8-record sample confirms multi-year coverage.) And ~6 of 8 sampled questions name their target year in the text.

**Design rules that follow:**
- Filter to questions naming one explicit year; parse by regex; report how much of the set survives.
- **Pair years ≥5 apart.** Annual reports carry 2–3 years of comparatives, so adjacent years overlap and the "stale" figure would be legitimately present. Without this the measurement is vacuous.
- Cross-entity pairs: different tickers.

**LangGraph `store.search` supports metadata filtering** — `filter: dict[str, Any]` confirmed in source. The as-of rule needs no workaround.

**Released dataset:** derived cross-period and cross-entity pairs, CSV **and Excel** — satisfies the mandatory-dataset requirement where CBA data could not.

## 7. Positioning — the nearest neighbours

**[2604.17979](https://arxiv.org/abs/2604.17979) — "Architecture Matters More Than Scale", AIITA 2026, IEEE. Published, not a preprint.** Uses FinQA and ConvFinQA; compares baseline / RAG / structured LTM / memory-augmented conversational with Mem0 on an 8B local model. Contains typed *entity-period-metric* tuples, scale normalisation, per-dialog scoping against cross-dialog leakage, and an accuracy-by-turn-depth figure.

**Strong related work, not a kill.** Its stated question is *"given a fixed 8B locally-hosted model, which architecture delivers the strongest accuracy?"*, and it *"makes no state-of-the-art claim."* An architecture bake-off under SME compute constraints — failure modes appear as passing observations, not the object of study.

| | Paper 1 | This paper |
|---|---|---|
| Question | which architecture wins under compute limits? | what breaks, and which setting fixes it? |
| Reports | aggregate accuracy | **per-failure-mode rates** |
| Library | Mem0, 8B local | **LangMem** — "what do the shipped defaults do" is library-specific |
| Cross-fiscal-year staleness | no | **yes**, ≥5-year gaps |

**[2606.29251](https://arxiv.org/html/2606.29251) — "When Summaries Distort Decisions".** The **motivation citation.** Shows financial compression changes the *investment decision*, and names **decontextualization** — evidence retained but separated from the qualifiers needed to interpret it. Open with it: someone has shown these errors change decisions; we show where they come from and how to stop them.

## 8. Already taken — do not re-claim

| Claim | Taken by |
|---|---|
| Taxonomy of memory failure modes | SHIELDA (2508.07935) names Outdated / Poisoned / Misaligned Memory; *Anatomy of Agentic Memory* (2602.19320); *SoK: Agentic RAG* (2603.07379) already uses the STM/LTM split |
| Type-aware compression (verbatim numbers, summarised prose) | Adaptive Focus Memory (2511.12712) — FULL / COMPRESSED / PLACEHOLDER; the phrase *"type-aware retention"* is in use |
| Schema-validated memory writes with validation gates | xmemory (2604.27906); Memanto (2604.22085) |
| Fact-recovery measurement under compression | AFM — *"60% of facts become irrecoverable"* at 36.7× |
| Qualifier-preserving compression prompts | 2606.29251 — and it uses a better metric (decision flips) |
| Ground-truth-preserving memory for auditability | MemMachine (2604.04853) |

**Terminology:** avoid "poisoning" — in the literature it means adversarial injection. Use **error propagation** for non-adversarial compounding, or a reviewer asks for a threat model.

## 9. ⚠️ The real risk is effect size, not novelty

The paper assumes LangMem's defaults measurably damage financial figures. **If summarisation mostly keeps years and units, or ConvFinQA conversations are too short for dilution to bite, there is no paper.** Nobody has checked. Including us.

**Go/no-go check, 1–2 days:** ~50 cross-year pairs, default config, count answers carrying the wrong year.

- ~30% stale → paper
- ~3% → stop; six weeks saved

Run it **before** committing to the full paper — but not before the abstract, which is design-stage and due in 7 days regardless.

## 9b. Writing discipline — assert only what is verifiable

Caught during the abstract sanity pass: an earlier draft stated *"Summarisation discards them"* in the Need section while Expected findings said *"we expect qualifier retention to fall."* **Internally inconsistent** — if it is already established, why measure it? A reviewer asks exactly that.

**The rule for the whole paper:**

| Claim type | How to state it |
|---|---|
| **Verifiable now** — e.g. LangMem's default prompt contains no instruction to preserve numbers, units or dates | assert it plainly. *"Default summarisation prompts never mention them."* Checkable in the source |
| **Mechanism / reasoning** — why a compressor would drop them | assert as reasoning. *"To a compressor, qualifiers read as redundancy."* |
| **Logical consequence** — what an unqualified figure is | assert. *"An unqualified figure can be literally correct and still mislead."* |
| **Our unmeasured result** — whether qualifiers are in fact lost, and how often | **hedge.** *"We expect…"* Never state as fact before the measurement exists |

This matters more than it sounds. The paper's credibility rests on the reader trusting the separation between what was *found in the source* and what was *found in the experiment*. Blurring them once invites doubt about everything else.

## 9c. The strongest objection — "why not just write a better prompt?"

**Expect this from a reviewer.** If LangMem's default summary prompt is the problem, and LangMem lets you override it, then the paper reads as *"we found a suboptimal default that the docs already tell you how to change."*

**Three answers, in order of strength:**

**1. We test whether the better prompt actually works — and expect it to fail partially.** This is the real answer. Condition 3b *is* the better prompt. Three mechanical reasons it should be insufficient alone:
- `max_summary_tokens` defaults to **256** — under a fixed budget something must go, whatever the prompt asks for
- **each round re-summarises the previous summary**, not the original, so a prompt applied at round 1 cannot protect what round 3 drops
- `RunningSummary.summary` is a **flat `str`** — there is nowhere structured to put a qualifier; it survives only as prose, where the next round can drop it

**If prompting were sufficient this would be a short and boring paper. The interesting result is where it fails**, and that is what motivates the structured-schema condition (3c).

**2. A prompt does nothing for three of the five failure modes.** Cross-company bleed is the `namespace` default (user-scoped, not entity-scoped). Agent-boundary loss is a different compression point entirely. Cross-session staleness lives in the store. **Only dilution and error propagation are summariser-side.** The other three live in the store and the graph.

**3. Defaults are what gets deployed.** *"You could have configured it better"* is true of nearly every production failure; the question is how many practitioners know to. Quantifying the cost of the default is precisely what tells them.

**Reflected in the abstract** as a specific, falsifiable prediction rather than a hedge: *"We expect prompt-level fixes alone to prove insufficient — the summary budget is fixed and each round re-compresses the last — with structured storage needed to close the gap."*

## 9d. The method contribution — XBRL fact-context as a memory schema

**Problem it solves.** Until 13 Sep the paper had **no method contribution**: the "remedy" was documented LangMem parameters. That is fine for feasibility and fatal for a reviewer asking *"what do you propose?"* — and it made the paper circular, since the diagnosis blamed the prompt and the remedy was a prompt.

**The proposal.** The diagnosis — *a figure needs its context and prose cannot carry it* — points at a representation financial reporting already mandates.

In **XBRL**, a fact is never a bare number. It is `value + context`, and context is required:

| XBRL context | Our qualifier |
|---|---|
| Entity identifier | entity |
| Period (instant **or** duration) | period |
| Unit | scale |
| Dimensions | basis |

> **Agent memory for financial figures should store XBRL-style facts — value plus mandatory context — with retrieval matched on context.**

**Why this beats "add some fields":** it gives a **principled answer to which qualifiers are mandatory, and when.** Revenue needs period + entity + unit; a ratio needs period + entity but no unit; a rate needs an *instant*, not a duration. The standard specifies this — we adopt a taxonomy rather than inventing one. Every number in every filing already carries it.

**Honest positioning: an adaptation, not an invention.** The contribution is that **the domain has a solved representation for exactly this problem and agent memory discards it.**

### ⚠️ Do not lock the claim to XBRL

**The claim is structural typing — qualifiers as schema fields rather than prose. XBRL is the precedent that justifies it, not the deliverable.**

The abstract therefore says *"typed facts carrying mandatory entity, period and unit context"* and cites XBRL as the standard that already mandates such a representation. If implementation shows XBRL's model is awkward for conversational memory, or something fits better, **the claim survives and only the instantiation changes.**

Alternatives to weigh during implementation:

| Representation | Fit |
|---|---|
| **XBRL / iXBRL** | Finance-native, mandatory, richest context model. Current default choice |
| **Bitemporal records** (valid time / transaction time) | **Complementary, not competing** — XBRL says what a fact *is*; bitemporal says when a record was *valid*. MemStrata (2606.26511) uses this. Could combine |
| **RDF / OWL with temporal qualification** | More general, heavier, no finance semantics |
| **SDMX / Data Cube** | Statistical dimensions; good for time series, weaker for narrative facts |
| **Plain typed records** | Simplest; loses the principled answer to *which* qualifiers are mandatory |

**The property to preserve whichever is chosen:** a *metric-conditional* required-field set — revenue needs period, entity and unit; a ratio needs no unit; a rate needs an instant rather than a duration. That is what distinguishes this from "add some fields", and it is the reason XBRL is the current pick.

### Novelty check, 13 Sep

XBRL + LLM work exists but is all about **reading** XBRL, not using its model as memory:

| Work | What it does |
|---|---|
| **XBRL-Agent** (ICAIF 2024, ACM 10.1145/3677052.3698614) | LLM agent that *analyses* XBRL reports |
| **FinTagging** | benchmark for *extracting and tagging* facts into XBRL |
| **AuditFlow** ([2606.03031](https://arxiv.org/pdf/2606.03031)) | symbolic verification of structured financial reporting |

**None uses the fact-context model as an agent memory representation.** Adjacent and worth citing: *From Prompts to Contracts: Harness Engineering for Auditable Enterprise LLM Agents* ([2607.08028](https://arxiv.org/pdf/2607.08028)), and the Deterministic State Store / Generative Context split in audit-oriented agent design.

### Consequence for the experiment

Condition **3c** is no longer "a Pydantic schema with some fields" — it is **an XBRL-derived fact schema**, and the required-field set is **metric-conditional** rather than uniform. The instructed summariser (3b) is the **control arm**, not the remedy.

## 10. Framing requirement

**Lead with decision risk, not mechanism.** Not *"memory loses qualifiers"* but:

> A financial analyst's AI assistant reports last year's figure for this year's question, or drops "millions" from a number, and the analyst acts on it. We measure how often the memory layer in widely used agent frameworks produces materially wrong figures from correct source documents — and identify the configuration settings that prevent it.

Same paper; now a business-analytics problem rather than plumbing.

## 11. Open items

- [ ] **Email baiconf2026@iimb.ac.in** — what does the IMR route commit to? Gates everything (see README).
- [ ] Confirm exact theme wording from the submission form.
- [ ] Write the 500-word abstract (due 19 Sep).
- [ ] Run the §9 go/no-go check.
- [ ] Correctness gate: reproduce ConvFinQA's published baselines (~68.9% fine-tuned, ~52.4% multi-aspect, 89.4% human) before measuring anything new.
