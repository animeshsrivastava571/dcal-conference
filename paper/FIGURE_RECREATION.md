# Lost in Handoff: paper figures and result tables

<!-- Transcribed from photos of paper/Version 2/FIGURE_RECREATION.md on the
office machine (IMG_8994-8998). Image links point to that machine's
experiments/ folder and do not resolve here. -->

This document is self-contained for redrawing the **three figures actually used in the Version 2 paper**. The images below are previews visible in this workspace; the numerical tables and drawing instructions still work if the images do not transfer. All rates are percentages, not raw proportions.

Important name mapping: **paper Fig. 2** is the experiment asset named `fig7_round_threshold_768`. The asset named `fig2_condition_ladder_768` is **not** included as a figure in this paper.

The main single-agent sample contains 115 company sessions and 1,887 scorable numeric turns per complete arm. Fig. 1 uses the run that permits abstention. Figs. 2 and 3 use forced-answer runs at the 768-token compaction trigger. The trigger is when compaction starts; it is **not** the length of the summary.

## Paper Fig. 1 – Accuracy by turn depth

![Fig. 1: accuracy by turn depth](../../experiments/phase1_within_session/figures/fig1_dilution_curve.png)

Recreate a **line chart**. Horizontal axis: turn depth within a chained session, at the starts of 5-turn buckets (0, 5, 10, 15). Vertical axis: numeric answer accuracy, 25% to 90%. Connect points within each series. Full history: solid slate line and circles. Default prose @1536: lighter red dashed line and squares. Default prose @768: red dashed line and triangles.

| Depth bucket | Scored turns per arm | Full history C | Default @1536 | Default @768 |
|---:|---:|---:|---:|---:|
| 0 | 570 | 84.21 | 76.67 | 52.98 |
| 5 | 573 | 83.25 | 64.92 | 46.42 |
| 10 | 575 | 85.74 | 70.09 | 50.78 |
| 15 | 169 | 78.70 | 63.31 | 33.73 |

**Overall across all depths:** C = 83.89%; default @1536 = 69.90%; default @768 = 48.60% (each n = 1,887). The last bucket is smaller; do not treat each plotted point as equally precise. The ceiling is an observed full-history result, not 100% accuracy.

Paper caption: "Numeric accuracy by turn-depth bucket in the 115-session permitted-abstention run. The ceiling also changes with depth; differences between policies are more informative than a single curve alone."

## Paper Fig. 2 – Accuracy by memory-update round

![Fig. 2: accuracy by memory-update round](../../experiments/phase1_within_session/figures/fig7_round_threshold_768.png)

Recreate a **line chart**. Horizontal axis: count of compaction/update rounds before the answer (0 = none yet). Vertical axis: accuracy, 0% to 100%. The three series all use the 768-token trigger. Draw a thin dotted vertical reference line halfway between rounds 0 and 1, labelled "first update".

| Round | Default prose 3a (accuracy; n) | Prompted prose 3b (accuracy; n) | Typed facts 3c (accuracy; n) |
|---:|---:|---:|---:|
| 0 | 87.13; 202 | 88.61; 202 | 85.01; 387 |
| 1 | 46.20; 487 | 42.83; 481 | 64.91; 114 |
| 2 | 45.87; 460 | 44.78; 469 | 71.93; 114 |
| 3 | 46.72; 366 | 46.01; 363 | 73.68; 114 |
| 4 | 36.02; 261 | 33.21; 262 | 69.30; 114 |
| 5 | 31.19; 109 | 25.00; 108 | 65.22; 115 |
| 6 | — | — | 75.65; 115 |
| 7 | — | — | 68.42; 114 |
| 8 | — | — | 73.45; 113 |
| 9 | — | — | 78.57; 112 |
| 10 | — | — | 74.77; 111 |
| 11 | — | — | 70.64; 109 |
| 12 | — | — | 68.22; 107 |
| 13 | — | — | 57.53; 73 |
| 14 | — | — | 53.66; 41 |

Legend: 3a red, 3b orange, 3c green; circular markers and solid lines. The prose series end at round 5 in this plot. Do not plot zeros in blank cells. The typed-fact policy performs more frequent extraction updates; a green "round" is not the same operation as a prose re-summarization round. Each point pools **different questions** at that round, not repeated answers to one question. It is therefore not a within-question before/after curve.

The stronger same-question check is separate from the plotted series: on **369 identical questions** where @768 had compacted once but @1536 had not compacted yet, accuracy was **45.26% vs 82.66%**. Later loss also continues: the gap between 3a@768 and full history on the corresponding round's questions grows from **35.1 points at round 1** to **53.2 at round 5**.

Paper caption: "Accuracy conditional on compaction count in the 115-session forced-answer runs. Round zero and round one contain different turns; the same-question budget comparison in the text is the more direct first-compaction check."

## Paper Fig. 3 – Which fields remain in memory?

![Fig. 3: field presence in carried memory](../../experiments/phase1_within_session/figures/fig3_retention_by_field_768.png)

Recreate a **grouped bar chart**. Horizontal groups, in this order: entity, period, unit, value, metric. Vertical axis: percentage of source facts whose given field was found in the final carried memory, 0% to 100%. Within each group, three bars: default prose 3a (red), prompted prose 3b (orange), typed facts 3c (green). All are forced-answer runs @768, 115 sessions. The extractor checks each field separately, not full fact linkage.

| Field | Default prose 3a | Prompted prose 3b | Typed facts 3c |
|---|---:|---:|---:|
| Entity | 24.70 | 24.48 | 92.69 |
| Period | 82.99 | 82.72 | 93.91 |
| Unit | 79.91 | 72.35 | 86.18 |
| Value | 20.83 | 20.61 | 28.46 |
| Metric | 61.97 | 57.97 | 67.15 |

Entity is roughly 25% for either prose method versus 93% for typed facts. However, a field being present does **not** establish that the correct year or unit is attached to the correct number. Unit detection is a coarse pattern match; value presence is low even under typed memory.

Paper caption: "Field-presence rates in carried memory at the 768-token trigger. Fields are scored separately against source facts; this does not establish that each retained qualifier is attached to the correct value."

## Paper result tables (not figures)

Table I reports **forced-answer outcomes at @768**. The full-history C row comes from the 3c run's own ceiling; other forced runs have slightly different ceilings. Recovery is `(arm accuracy - 48.3) / (82.9 - 48.3)`.

| Policy | Accuracy | Answered-wrong | Loss recovered |
|---|---:|---:|---:|
| Full history C (3c-run reference) | 82.9% | 14.3% | — |
| Default prose 3a | 48.3% | 38.8% | baseline |
| Prompted prose 3b | 46.4% | 36.8% | -5% |
| Typed facts 3c | 72.4% | 17.6% | 70% |

Table II concerns **potentially dependent turns**, classified by matching a program operand to an earlier turn's gold value. This is a proxy for reuse, not evidence that the assistant copied an earlier wrong model prediction.

| Policy | Accuracy when earlier related answer correct | When earlier related answer wrong |
|---|---:|---:|
| Full history C | 89.4% | 33.9% |
| Default prose 3a @768 | 76.8% | 6.8% |
| Prompted prose 3b @768 | 78.0% | 5.2% |
| Typed facts 3c @768 | 75.1% | 17.2% |

## Plot styling and provenance

Use a light background, readable axis labels and legends, and no truncation that changes the visual meaning of a comparison. The original palette was slate `#2c3e50`, red `#e74c3c`, orange `#e67e22`, and green `#27ae60`. Export vector PDF for the LaTeX manuscript, and PNG for preview. Keep the figure captions with the images when rebuilding the paper.

Numbers above come from the curated results saved alongside the experiment: `B_stm3a_permitted_115sessions_summary.json`, `B_round_threshold_115sessions.json`, `B_3a_forced_retention_115sessions.json`, `B_3b_forced_retention_115sessions.json`, and `B_3c_retention_115sessions.json`. They are enough to redraw the three paper figures without raw model transcripts. The paper's other charts are not used in Version 2; do not silently substitute them for Figs. 1–3.
