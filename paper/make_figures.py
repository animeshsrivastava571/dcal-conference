"""Draw paper Figs. 1-3 from the values in handoff/paper_results.py.

That module is the single source for these numbers and also exports them
in the released results workbook, so the plotted and released values cannot
drift apart. Exports vector PDF for the LaTeX manuscript and PNG for preview.

    PYTHONPATH=src python paper/make_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from handoff.paper_results import FIG1, FIG2, FIG3

OUT = Path(__file__).resolve().parent / "figures"

SLATE = "#2c3e50"
RED = "#e74c3c"
LIGHT_RED = "#f1948a"
ORANGE = "#e67e22"
GREEN = "#27ae60"

# IEEE single-column width.
SIZE = (3.5, 2.6)

plt.rcParams.update(
    {
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "legend.fontsize": 7,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    }
)


def _save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=300)
    plt.close(fig)


def fig1_dilution() -> None:
    depth = FIG1["depth"]
    ceiling = FIG1["full_history_C"]
    at_1536 = FIG1["default_3a_1536"]
    at_768 = FIG1["default_3a_768"]

    fig, ax = plt.subplots(figsize=SIZE)
    ax.plot(depth, ceiling, "-o", color=SLATE, label="Full history (ceiling)", ms=4)
    ax.plot(depth, at_1536, "--s", color=LIGHT_RED, label="LangMem default @1536", ms=4)
    ax.plot(depth, at_768, "--^", color=RED, label="LangMem default @768", ms=4.5)
    ax.set_title("Dilution: accuracy falls as memory compresses")
    ax.set_xlabel("Turn depth within session")
    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(depth)
    ax.set_ylim(25, 90)
    ax.legend(loc="lower left", frameon=False)
    _save(fig, "fig1_dilution_curve")


def fig2_round_threshold() -> None:
    # Prose policies never reach later rounds; drop the gaps rather than plot zeros.
    prose_rounds = [r for r, v in zip(FIG2["round"], FIG2["default_3a"]) if v is not None]
    default_3a = [v for v in FIG2["default_3a"] if v is not None]
    prompted_3b = [v for v in FIG2["prompted_3b"] if v is not None]
    typed_rounds = FIG2["round"]
    typed_3c = FIG2["typed_3c"]

    fig, ax = plt.subplots(figsize=SIZE)
    ax.axvline(0.5, color="0.55", lw=0.7, ls=":")
    ax.text(0.58, 97, "first compaction fires", fontsize=6, color="0.4", va="top")
    ax.plot(prose_rounds, default_3a, "-o", color=RED, label="LangMem default (3a)", ms=3.5)
    ax.plot(prose_rounds, prompted_3b, "-o", color=ORANGE, label="Better prompt (3b)", ms=3.5)
    ax.plot(typed_rounds, typed_3c, "-o", color=GREEN, label="Typed facts (3c)", ms=3.5)
    ax.set_title("The threshold is a step at round 1, not a turn-depth cliff")
    ax.set_xlabel("Compaction round (0 = before any compaction)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(range(0, 15, 2))
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right", frameon=False)
    _save(fig, "fig2_round_threshold_768")


def fig3_retention_by_field() -> None:
    fields = FIG3["field"]
    default_3a = FIG3["default_3a"]
    prompted_3b = FIG3["prompted_3b"]
    typed_3c = FIG3["typed_3c"]

    fig, ax = plt.subplots(figsize=SIZE)
    width = 0.26
    x = range(len(fields))
    ax.bar([i - width for i in x], default_3a, width, color=RED, label="LangMem default (3a)")
    ax.bar(list(x), prompted_3b, width, color=ORANGE, label="Better prompt (3b)")
    ax.bar([i + width for i in x], typed_3c, width, color=GREEN, label="Typed facts (3c)")
    ax.set_title("Where qualifiers die: typed facts hold entity/period; prompt does not")
    ax.set_ylabel("Qualifier retained (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(fields)
    ax.set_ylim(0, 100)
    # Below the axis: inside it, the legend covers the unit bars at ~80-86%.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False, ncol=3,
              columnspacing=1.0, handlelength=1.2)
    _save(fig, "fig3_retention_by_field_768")


if __name__ == "__main__":
    fig1_dilution()
    fig2_round_threshold()
    fig3_retention_by_field()
    for path in sorted(OUT.glob("*")):
        print(f"{path.stat().st_size:>8,}  {path.relative_to(OUT.parent)}")
