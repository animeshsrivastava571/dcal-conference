# BAICONF 2026 — candidate ideas

Venue-scoped folder. Candidate papers for **BAICONF 2026** (13th International Conference on Business Analytics and Intelligence, DCAL, IIM Bangalore). Ideas are numbered; the highest number is not the chosen one.

## Constraints every candidate must satisfy

| | |
|---|---|
| Conference | **17–19 Dec 2026**, IIM Bangalore |
| **Abstract deadline** | **19 Sep 2026** |
| Notification | 26 Sep 2026 |
| **Full paper** | **31 Oct 2026** — ~6 weeks after acceptance |
| Registration | 14 Nov 2026 |
| Abstract format | **≤500 words**, structured: *background · need · aims · methods · expected findings* |
| Full paper | ≤4,500 words / 12 pages |
| **Dataset** | **mandatory** with submission, Excel preferred |
| Submission | site after Register/Login · `dcal.iimb.ac.in/baiconf2026/` (bot-challenged; use a browser) |
| Contact | baiconf2026@iimb.ac.in |
| Fees incl. GST | corporate ₹10,000 · academic ₹7,000 · student/alumni ₹5,000 · international USD 500 · workshop ₹15,000 |
| Scale (2022) | ~450 abstracts → 200 selected (~44%) |

## Full theme list (from the submission form, 13 Sep)

ARIMA/ARIMAX · Artificial Neural Networks · Bagging/Boosting · Bayesian Regression · Big Data Technologies · CHAID · CART · CNN · Data Visualization · Decision Trees · Dynamic Pricing & Revenue Management · **Fraud Analytics** · Geospatial Analytics · Gradient Descent · Healthcare Analytics · IoT · KNN · Linear Programming · Logistic Regression · Market Basket Analytics · Markov Models · Meta Data · Multi-Criteria Decision Making · Multinomial Regression · Panel Data · PCA · **Recommender Systems** · Retail Analytics · **Reinforcement Learning** · **Sentiment Analysis** · Sports Analytics · Supervised Learning · Supply Chain Analytics · SVM · Telecom Analytics · **Text Analytics** · **Text Mining** · Web Analytics

**Treat it as a guideline, not a gate.** It carries no LLM, Generative AI, Agentic AI or NLP entry — but that is weak evidence. These keyword lists are legacy, LLM work maps cleanly under Text Analytics / Text Mining / Deep Learning / ANN, and the post-conference workshops (20–21 Dec) include **Agentic AI**, so the organisers are actively programming this material.

**What the list is genuinely useful for:** **finance has no vertical of its own**, while Healthcare, Retail, Sports, Telecom, Supply Chain, Web and Geospatial all do. So a finance paper enters under a **method** theme — lead with the analytic technique, with finance as the application.

**Target:** primary **Text Analytics / Text Mining**; secondary **Sentiment Analysis** or **Theory, Methods and Application**. Do not lead with Deep Learning unless contributing on architectures or training; do not stretch to Fraud Analytics.

## Publication route — read before choosing

Selected work routes to **IIMB Management Review** (ISSN 0970-3896, Elsevier, **Scopus-indexed, ABDC B**). So BAICONF **competes with** FinNLP/ICAIF rather than complementing them — the same work cannot be published twice.

Presenting ≠ publishing in IMR: only selected work is invited, and an invitation can be declined. Decide only if one arrives.

⚠️ **Open gate for all candidates:** email baiconf2026@iimb.ac.in and establish what *"selected work routes to IIMB Management Review"* actually commits to. One line; protects the stronger venues.

## Hard rules for candidates

1. **Open data only.** No CBA data, no internal system details — the disclosure review hasn't started, and a synthetic or public corpus also satisfies the mandatory-dataset requirement where CBA data could not.
2. **Buildable by 31 Oct.** Acceptance converts the idea into a dated commitment.
3. **`ideas/01` (versioned routing memory) is not eligible.** Reserved for a stronger venue.
4. **Lead with the business consequence, not the mechanism.** This is *Business Analytics and Intelligence*; a paper that reads as tooling fits the theme and reviews badly.

## Candidates

| # | Idea | Status |
|---|---|---|
| [01](01-memory-qualifier-loss.md) | Memory-induced failure modes in financial document agents | ✅ **SELECTED** — abstract drafted, see [`abstract-baiconf2026.md`](abstract-baiconf2026.md) |

Two other candidates were drafted and **removed from this folder on 13 Sep to avoid confusion** — they were never for this deadline. Both remain recoverable in git history (commit `d9dee66`) and are summarised in the plan file:
- **02 — reason-aware non-answers in earnings call Q&A.** Best story, biggest public data; blocked on an unverified S&P Capital IQ redistribution licence and an unchecked novelty claim.
- **03 — do agent task-completion metrics agree on financial tasks?** Most applied; requires building a multi-agent system before any measurement, and novelty unchecked.

Revisit for FinNLP / ICAIF, not BAICONF.

**Why 01 was selected:** it is the only candidate that has been **verified**. Data checked (FinQA ids carry `TICKER/YEAR`, ~6 of 8 questions name their year, ≥5-year gap rule established, `store.search` filtering confirmed), LangMem source read line by line, novelty position examined repeatedly. 02 and 03 are where 01 was three days ago — promising and unexamined. With six days to the deadline, trading a de-risked candidate for two unexamined ones is a bad trade.

## Areas checked and found occupied — do not re-propose

Six ideation cycles across 12–13 Sep, every one occupied. This is structural, not bad luck: LLM-for-finance papers in major venues went **36 → 250 (+594%)**. Anything general we invent is already being written full-time by someone else.

| Area | Occupied by |
|---|---|
| Memory failure taxonomy | SHIELDA (2508.07935), *Anatomy of Agentic Memory* (2602.19320), *SoK: Agentic RAG* (2603.07379) |
| Type-aware compression / verbatim numerics | Adaptive Focus Memory (2511.12712) — FULL/COMPRESSED/PLACEHOLDER |
| Schema-validated memory writes | xmemory (2604.27906), Memanto (2604.22085) |
| Qualifier-preserving compression in finance | *When Summaries Distort Decisions* (2606.29251) |
| Text-chart consistency | **EvidFuse** (2601.05487) |
| Chart / visualization agent evaluation | ChartAnchor, DV-World, VegaChat, EvoGenUI-Bench, MisVisFix |
| Finance evals | FinBen, BizFinBench v1/v2, FinanceBench, Finance Agent Benchmark, FinTradeBench, SMARTFinRAG, PRBench-Finance |
| Operational cost-accuracy eval of financial doc processing | 2603.22651 |
| TBML / trade mispricing | UN Comtrade ML published; mirror statistics since Carrère & Grigoriou (2014) |
| CFPB complaints | the standard teaching dataset — many papers and theses |
| Abstention under reward pressure | TIAR, I-CALM, *Two Axes of LLM Abstention*, ternary +1/−1/0 reward |
| Escalation under authority limits | *Designing for Doubt* (2606.02965); otherwise framed as security (OWASP, AgentDojo) |

**One unclaimed vertical, parked:** every finance benchmark found covers investing, markets, filings or wealth management. **None covers trade finance operations** — documentary credits, guarantees, document examination. Real gap, and it is Animesh's domain. Previously raised as UCP 600 discrepancy detection and rejected; the reframe that differs is *"no finance benchmark covers this vertical"* rather than *"here is a detection method"*.

## Two process lessons

1. **Match the novelty bar to the venue before searching, not after.** BAICONF is ~44% acceptance; the criteria are sound method, real data, a clear finding and practitioner relevance. **Novelty is not the gate.** Six novelty searches were run against a top-tier bar that does not apply here.
2. **Weight single data points less.** Twice a single signal triggered an over-reaction — one adjacent paper caused a whole-topic pivot, and a legacy theme list caused a locked idea to be demoted. Both were wrong and both were reversed.
