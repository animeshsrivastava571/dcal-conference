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


def build(runs_dir: Path = RUNS_DIR, min_sessions: int = 10) -> pd.DataFrame:
    """Collect every complete long-session run, skipping pilots and aborted runs.

    An aborted run still writes a line per session, so completeness is counted
    from sessions that actually carry results; a run that died partway would
    otherwise contribute a lopsided arm.
    """
    rows: list[dict] = []
    for run_dir in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dataset")
    parser.add_argument("--min-sessions", type=int, default=10)
    args = parser.parse_args()

    frame = build(min_sessions=args.min_sessions)
    if frame.empty:
        raise SystemExit("no qualifying runs found")

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
