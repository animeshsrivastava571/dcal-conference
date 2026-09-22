"""Run the cross-period staleness check and persist every transcript."""

from __future__ import annotations

import argparse
import dataclasses
import json
import traceback
from datetime import datetime, timezone

from dotenv import load_dotenv

from handoff.agents.pipeline import run_session
from handoff.config import RUNS_DIR, Condition
from handoff.data.pairs import sample_pairs
from handoff.eval.staleness import StalenessReport, score_pair
from handoff.memory.conditions import build_policy

ARMS = {
    # Memory and the correct filing are both available: does memory override
    # the document?
    "document": True,
    # The filing is withheld: does memory supply a confidently wrong figure?
    "memory-only": False,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--arms", nargs="+", choices=sorted(ARMS), default=sorted(ARMS))
    args = parser.parse_args()

    load_dotenv()
    pairs = sample_pairs(args.pairs, seed=args.seed)

    run_dir = RUNS_DIR / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=True)
    transcript = (run_dir / "pairs.jsonl").open("w")

    reports = {arm: StalenessReport() for arm in args.arms}
    failures = 0

    for i, pair in enumerate(pairs, 1):
        print(f"[{i}/{len(pairs)}] {pair.ticker} {pair.early.year} -> {pair.late.year}", flush=True)
        try:
            policy = build_policy(Condition.LANGMEM_DEFAULT)
            early = run_session(pair.early, policy, include_document=True)

            record = {
                "ticker": pair.ticker,
                "gap": pair.gap,
                "early": dataclasses.asdict(early),
                "memory_after_early": policy.dump(),
                "late": {},
            }
            for arm in args.arms:
                # commit=False keeps the arms independent: a late session that
                # wrote its own answers back would seed the next arm's recall.
                late = run_session(
                    pair.late, policy, include_document=ARMS[arm], commit=False
                )
                score_pair(early, late, reports[arm])
                record["late"][arm] = dataclasses.asdict(late)

            transcript.write(json.dumps(record) + "\n")
            transcript.flush()
        except Exception:
            failures += 1
            print(f"  failed: {traceback.format_exc(limit=1).strip()}", flush=True)

    transcript.close()

    summary = {
        "pairs_requested": args.pairs,
        "pairs_failed": failures,
        "seed": args.seed,
        "arms": {},
    }
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
            "examples": [dataclasses.asdict(e) for e in report.examples[:10]],
        }

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\nwrote {run_dir}")
    for arm, stats in summary["arms"].items():
        ci = stats["ci95"]
        print(
            f"  {arm:<12} stale {stats['stale']}/{stats['eligible_turns']} "
            f"= {stats['stale_rate']:.1%}  95% CI [{ci[0]:.1%}, {ci[1]:.1%}]  "
            f"(correct {stats['correct']}, abstained {stats['abstained']}, "
            f"other wrong {stats['other_wrong']})"
        )


if __name__ == "__main__":
    main()
