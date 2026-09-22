"""Re-score a saved run from its transcript, without calling any model.

Grading changes after a run should never cost another run, so every turn is
re-graded from the stored prediction rather than trusting the flags written at
the time.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from handoff.agents.pipeline import SessionResult, TurnResult
from handoff.config import RUNS_DIR
from handoff.eval.correctness import grade
from handoff.eval.staleness import StalenessReport, score_pair


def _rehydrate(payload: dict) -> SessionResult:
    session = SessionResult(
        conversation_id=payload["conversation_id"],
        ticker=payload["ticker"],
        year=payload["year"],
        include_document=payload["include_document"],
    )
    for turn in payload["turns"]:
        scored = grade(turn["prediction"], turn["gold"])
        session.turns.append(
            TurnResult(
                index=turn["index"],
                question=turn["question"],
                gold=turn["gold"],
                prediction=turn["prediction"],
                correct=scored.correct,
                scale_factor=scored.factor,
                recalled=turn.get("recalled", []),
            )
        )
    return session


def rescore(run_dir: Path) -> dict:
    records = [json.loads(line) for line in (run_dir / "pairs.jsonl").open()]
    arms = sorted(records[0]["late"])
    reports = {arm: StalenessReport() for arm in arms}
    scales: dict[str, Counter] = {arm: Counter() for arm in arms}

    for record in records:
        early = _rehydrate(record["early"])
        for arm in arms:
            late = _rehydrate(record["late"][arm])
            score_pair(early, late, reports[arm])
            for turn in late.turns:
                if turn.correct:
                    scales[arm][turn.scale_factor] += 1

    summary = {"pairs": len(records), "arms": {}}
    for arm, report in reports.items():
        low, high = report.confidence_interval
        summary["arms"][arm] = {
            "eligible_turns": report.eligible,
            "ambiguous_turns": report.ambiguous,
            "correct": report.correct,
            "stale": report.stale,
            "abstained": report.abstained,
            "other_wrong": report.other_wrong,
            "stale_rate": round(report.rate, 4),
            "ci95": [round(low, 4), round(high, 4)],
            "scale_factors": {str(k): v for k, v in sorted(scales[arm].items(), key=lambda kv: -kv[1])},
            "examples": [
                {
                    "question": e.question,
                    "prediction": e.prediction,
                    "gold": e.gold,
                    "matched_early_value": e.matched_early_value,
                }
                for e in report.examples[:10]
            ],
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", nargs="?", help="run directory; defaults to the newest")
    args = parser.parse_args()

    if args.run:
        run_dir = Path(args.run)
    else:
        candidates = [d for d in RUNS_DIR.iterdir() if (d / "pairs.jsonl").exists()]
        if not candidates:
            parser.error(f"no cross-period run found under {RUNS_DIR}")
        run_dir = max(candidates, key=lambda p: p.name)
    summary = rescore(run_dir)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"{run_dir.name}: {summary['pairs']} pairs\n")
    for arm, stats in summary["arms"].items():
        low, high = stats["ci95"]
        print(
            f"  {arm:<12} stale {stats['stale']}/{stats['eligible_turns']} "
            f"= {stats['stale_rate']:.1%}  95% CI [{low:.1%}, {high:.1%}]"
        )
        print(
            f"  {'':<12} correct {stats['correct']}, abstained {stats['abstained']}, "
            f"other wrong {stats['other_wrong']}, ambiguous {stats['ambiguous_turns']}"
        )
        print(f"  {'':<12} scale factors on correct: {stats['scale_factors']}\n")


if __name__ == "__main__":
    main()
