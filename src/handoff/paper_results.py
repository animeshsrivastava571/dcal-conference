"""The aggregate results reported in the paper.

Single source for Figs. 1-3 and Tables I-II: paper/make_figures.py draws from
these values and handoff.build_inputs writes them into the release workbook, so
the plotted and released numbers cannot drift apart. Values are transcribed from
paper/FIGURE_RECREATION.md, which records the curated 115-session result files.
Percentages throughout.
"""

from __future__ import annotations


# Fig. 1: accuracy by turn-depth bucket, permitted-abstention run.
FIG1 = {
    "depth": [0, 5, 10, 15],
    "scored_turns_per_arm": [570, 573, 575, 169],
    "full_history_C": [84.21, 83.25, 85.74, 78.70],
    "default_3a_1536": [76.67, 64.92, 70.09, 63.31],
    "default_3a_768": [52.98, 46.42, 50.78, 33.73],
}

# Fig. 2: accuracy by compaction/update round, forced-answer runs at 768.
# None marks rounds a policy never reached; they are not plotted as zeros.
FIG2 = {
    "round": list(range(15)),
    "default_3a": [87.13, 46.20, 45.87, 46.72, 36.02, 31.19] + [None] * 9,
    "default_3a_n": [202, 487, 460, 366, 261, 109] + [None] * 9,
    "prompted_3b": [88.61, 42.83, 44.78, 46.01, 33.21, 25.00] + [None] * 9,
    "prompted_3b_n": [202, 481, 469, 363, 262, 108] + [None] * 9,
    "typed_3c": [85.01, 64.91, 71.93, 73.68, 69.30, 65.22, 75.65, 68.42,
                 73.45, 78.57, 74.77, 70.64, 68.22, 57.53, 53.66],
    "typed_3c_n": [387, 114, 114, 114, 114, 115, 115, 114, 113, 112, 111, 109, 107, 73, 41],
}

# Fig. 3: field presence in carried memory, forced-answer runs at 768.
FIG3 = {
    "field": ["entity", "period", "unit", "value", "metric"],
    "default_3a": [24.70, 82.99, 79.91, 20.83, 61.97],
    "prompted_3b": [24.48, 82.72, 72.35, 20.61, 57.97],
    "typed_3c": [92.69, 93.91, 86.18, 28.46, 67.15],
}

# Table I: forced-answer outcomes at the 768-token trigger.
TABLE1 = {
    "policy": ["Full history (3c-run C)", "Default prose (3a)", "Prompted prose (3b)", "Typed facts (3c)"],
    "accuracy": [82.9, 48.3, 46.4, 72.4],
    "answered_wrong": [14.3, 38.8, 36.8, 17.6],
    "recovery": [None, "baseline", "-5%", "70%"],
}

# Table II: potentially dependent turns, conditional on earlier model answers.
TABLE2 = {
    "policy": ["Full history", "Default prose @768", "Prompted prose @768", "Typed facts @768"],
    "earlier_correct": [89.4, 76.8, 78.0, 75.1],
    "earlier_wrong": [33.9, 6.8, 5.2, 17.2],
}

# Further values the text reports, with where they appear. Most are percentages;
# labels name the unit where a value is a count or a difference in points.
REPORTED = [
    ("III.D", "Correct default-arm answers needing a non-identity scale factor", 23, "approximate"),
    ("IV.A", "Permitted, full history C, accuracy", 83.89, "n = 1,887"),
    ("IV.A", "Permitted, default prose @1536, accuracy", 69.90, "n = 1,887"),
    ("IV.A", "Permitted, default prose @768, accuracy", 48.60, "n = 1,887"),
    ("IV.A", "369 identical questions, @768 compacted once, accuracy", 45.26, ""),
    ("IV.A", "369 identical questions, @1536 not yet compacted, accuracy", 82.66, ""),
    ("IV.A", "Gap 3a@768 vs full history at round 1, points", 35.1, ""),
    ("IV.A", "Gap 3a@768 vs full history at round 5, points", 53.2, ""),
    ("IV.B", "Permitted @768, correct", 48.6, ""),
    ("IV.B", "Permitted @768, answered-wrong", 27.0, ""),
    ("IV.B", "Permitted @768, abstained", 24.4, ""),
    ("IV.B", "Forced @768, correct", 48.3, ""),
    ("IV.B", "Forced @768, answered-wrong", 38.8, ""),
    ("IV.B", "Forced @768, abstained", 12.8, ""),
    ("IV.B", "Forced full-history reference (own run), correct", 84.3, ""),
    ("IV.B", "Forced full-history reference (own run), answered-wrong", 12.6, ""),
    ("IV.C", "Typed facts @1536, accuracy", 74.8, "one company lacks this arm"),
    ("IV.C", "Sonnet summarizer @768, accuracy (from 46.1)", 48.6, "50 sessions; own ceiling 82.7"),
    ("IV.C", "Prompted prose minus default @768, points", -1.9, "company-cluster bootstrap interval spans zero"),
    ("IV.C", "Typed facts minus default @768, bootstrap low, points", 21, "5,000-draw company-level bootstrap; approximate"),
    ("IV.C", "Typed facts minus default @768, bootstrap high, points", 28, "5,000-draw company-level bootstrap; approximate"),
    ("IV.D", "Scorable turns labelled potentially dependent", 33.2, ""),
    ("IV.D", "Cross-period, document-present: eligible turns (count)", 161, "50 cross-period pairs"),
    ("IV.D", "Cross-period, document-present: turns answered with an earlier-year figure (count)", 0, ""),
    ("IV.D", "Cross-period, memory-only: eligible turns (count)", 161, "50 cross-period pairs"),
    ("IV.D", "Cross-period, memory-only: turns answered with an earlier-year figure (count)", 1, ""),
    ("IV.D", "Cross-entity: eligible turns (count)", 185, "50 cross-entity pairs"),
    ("IV.D", "Cross-entity: matches to the other company's earlier figures (count)", 0, "document-present and memory-only settings"),
    ("IV.E", "Routed multi-agent, full history, accuracy", 53.9, "50 sessions"),
    ("IV.E", "Routed multi-agent, default prose @768, accuracy", 43.1, "50 sessions"),
    ("IV.E", "Routed multi-agent, full history, answered-wrong", 9.0, "50 sessions"),
    ("IV.E", "Routed multi-agent, default prose @768, answered-wrong", 20.2, "50 sessions"),
]
