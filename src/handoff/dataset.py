"""Export the released dataset: one row per turn per arm, CSV and Excel.

BAICONF requires a dataset with the submission and prefers Excel. This is also
the results appendix: every number in the paper is recomputable from these rows
without an API key.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from handoff.config import MODEL_ID, RUNS_DIR
from handoff.eval.correctness import grade

COLUMNS = [
    "run",
    "pipeline",
    "condition",
    "arm",
    "budget",
    "abstention",
    "session",
    "ticker",
    "year",
    "depth",
    "question",
    "is_computed",
    "gold",
    "prediction",
    "outcome",
    "scale_factor",
    "summary_rounds",
    "model_id",
]


def _outcome(prediction: str, gold: float | str) -> tuple[str, float | None]:
    scored = grade(prediction, gold)
    if scored.correct:
        return "correct", scored.factor
    return ("wrong" if scored.answered else "abstained"), None


def _budget(arm: str) -> int | None:
    if "@" not in arm:
        return None
    return int(arm.split("@", 1)[1].split("/", 1)[0].replace("+handoff", ""))


def _rows_from_run(run_dir: Path) -> list[dict]:
    transcript = run_dir / "sessions.jsonl"
    if not transcript.exists():
        return []

    summary_path = run_dir / "summary.json"
    meta = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    pipeline = meta.get("pipeline", "single-agent")

    rows: list[dict] = []
    for line in transcript.open():
        record = json.loads(line)
        for arm, payload in record.get("arms", {}).items():
            forced = payload.get("forced")
            if forced is None:
                forced = "/forced" in arm or meta.get("forced", False)
            condition = arm.split("@", 1)[0].split("/", 1)[0].replace("+handoff", "")
            for turn in payload["turns"]:
                outcome, factor = _outcome(turn["prediction"], turn["gold"])
                rows.append(
                    {
                        "run": run_dir.name,
                        "pipeline": pipeline,
                        "condition": condition,
                        "arm": arm,
                        "budget": _budget(arm),
                        "abstention": "forbidden" if forced else "permitted",
                        "session": f"{run_dir.name}:{record['ticker']}",
                        "ticker": turn.get("ticker", record["ticker"]),
                        "year": turn.get("year"),
                        "depth": turn["depth"],
                        "question": turn["question"],
                        "is_computed": turn.get("is_computed"),
                        "gold": turn["gold"],
                        "prediction": turn["prediction"],
                        "outcome": outcome,
                        "scale_factor": factor,
                        "summary_rounds": turn.get("summary_rounds"),
                        "model_id": payload.get("model_id", MODEL_ID),
                    }
                )
    return rows


def build(
    runs_dir: Path = RUNS_DIR,
    min_sessions: int = 10,
    run_names: list[str] | None = None,
) -> pd.DataFrame:
    """Collect complete long-session runs, skipping pilots and aborted runs.

    With ``run_names`` exactly those runs are used, so a release cannot pick up
    a stray pilot. An aborted run still writes a line per session, so
    completeness is counted from sessions that actually carry results.
    """
    if run_names:
        missing = [n for n in run_names if not (runs_dir / n / "sessions.jsonl").exists()]
        if missing:
            raise SystemExit(f"runs not found under {runs_dir}: {missing}")
        candidates = [runs_dir / n for n in run_names]
    else:
        candidates = sorted(p for p in runs_dir.iterdir() if p.is_dir())

    rows: list[dict] = []
    for run_dir in candidates:
        transcript = run_dir / "sessions.jsonl"
        if not transcript.exists():
            continue
        complete = sum(
            1 for line in transcript.open() if json.loads(line).get("arms")
        )
        if complete < min_sessions:
            continue
        rows.extend(_rows_from_run(run_dir))
    return pd.DataFrame(rows, columns=COLUMNS)


# Numbers the paper reports for the 115-session single-agent runs, in percent.
# Each is (abstention, arm base, metric, low, high); a range covers the forced
# ceilings, which the paper reports as 82.9-84.3 across separately run arms.
PAPER = [
    ("permitted", "C", "accuracy", 83.9, 83.9),
    ("permitted", "3a@1536", "accuracy", 69.9, 69.9),
    ("permitted", "3a@768", "accuracy", 48.6, 48.6),
    ("permitted", "3a@768", "wrong", 27.0, 27.0),
    ("permitted", "3a@768", "abstained", 24.4, 24.4),
    ("forbidden", "C", "accuracy", 82.9, 84.3),
    ("forbidden", "3a@768", "accuracy", 48.3, 48.3),
    ("forbidden", "3a@768", "wrong", 38.8, 38.8),
    ("forbidden", "3a@768", "abstained", 12.8, 12.8),
    ("forbidden", "3b@768", "accuracy", 46.4, 46.4),
    ("forbidden", "3b@768", "wrong", 36.8, 36.8),
    ("forbidden", "3c@768", "accuracy", 72.4, 72.4),
    ("forbidden", "3c@768", "wrong", 17.6, 17.6),
]
TOLERANCE = 0.06  # the paper rounds to one decimal place


def check_against_paper(frame: pd.DataFrame) -> list[str]:
    """Return a failure message per paper number the release does not reproduce."""
    single = frame[frame["pipeline"] == "single-agent"].copy()
    single["base"] = [str(arm).split("/")[0] for arm in single["arm"]]
    per_run = (
        single.groupby(["run", "abstention", "base"])
        .agg(
            n=("outcome", "size"),
            accuracy=("outcome", lambda s: 100 * (s == "correct").mean()),
            wrong=("outcome", lambda s: 100 * (s == "wrong").mean()),
            abstained=("outcome", lambda s: 100 * (s == "abstained").mean()),
        )
        .reset_index()
    )

    failures = []
    print(f"\n{'check':<42} {'paper':>12} {'release':>18}")
    for abstention, base, metric, low, high in PAPER:
        found = per_run[(per_run["abstention"] == abstention) & (per_run["base"] == base)]
        label = f"{abstention} {base} {metric}"
        target = f"{low}" if low == high else f"{low}-{high}"
        if found.empty:
            failures.append(f"{label}: arm not present in the selected runs")
            print(f"  [FAIL] {label:<36} {target:>12} {'missing':>18}")
            continue
        values = found[metric].round(2).tolist()
        ok = all(low - TOLERANCE <= v <= high + TOLERANCE for v in values)
        shown = ", ".join(f"{v:.1f}" for v in values)
        print(f"  [{'ok ' if ok else 'FAIL'}] {label:<36} {target:>12} {shown:>18}")
        if not ok:
            failures.append(f"{label}: paper {target}, release {shown}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dataset")
    parser.add_argument("--min-sessions", type=int, default=10)
    parser.add_argument(
        "--runs", nargs="+", metavar="RUN_DIR",
        help="exact run directory names under runs/ to release (default: all complete runs)",
    )
    parser.add_argument(
        "--skip-paper-check", action="store_true",
        help="write even if the numbers do not reproduce the paper (diagnostics only)",
    )
    args = parser.parse_args()

    frame = build(min_sessions=args.min_sessions, run_names=args.runs)
    if frame.empty:
        raise SystemExit("no qualifying runs found")

    failures = check_against_paper(frame)
    if failures and not args.skip_paper_check:
        raise SystemExit(
            f"\n{len(failures)} paper number(s) not reproduced; nothing written. "
            "Select the paper's runs with --runs."
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / "turns.csv", index=False)

    pivot = (
        frame.assign(correct=frame["outcome"].eq("correct"))
        .groupby(["pipeline", "abstention", "arm"], dropna=False)
        .agg(
            turns=("correct", "size"),
            accuracy=("correct", "mean"),
            wrong=("outcome", lambda s: (s == "wrong").mean()),
            abstained=("outcome", lambda s: (s == "abstained").mean()),
        )
        .round(4)
        .reset_index()
    )
    pivot.to_csv(out / "summary.csv", index=False)

    with pd.ExcelWriter(out / "lost-in-handoff-dataset.xlsx") as writer:
        frame.to_excel(writer, sheet_name="turns", index=False)
        pivot.to_excel(writer, sheet_name="summary", index=False)

    print(f"wrote {out}/")
    print(f"  turns.csv                     {len(frame):,} rows")
    print(f"  summary.csv                   {len(pivot)} arms")
    print(f"  lost-in-handoff-dataset.xlsx  2 sheets")
    print(f"\nruns included: {frame['run'].nunique()}   sessions: {frame['session'].nunique()}")
    print(pivot.to_string(index=False))


if __name__ == "__main__":
    main()
