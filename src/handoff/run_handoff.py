"""Measure loss at the agent boundary, with and without summarisation on top.

The single-agent runs isolate compression inside one agent. This adds the
handoff so the two losses can be separated: the ceiling arm has no
summarisation at all, so anything it loses is attributable to the boundary
alone.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from collections import defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv

from handoff.agents.twoagent import run_two_agent_session
from handoff.config import MODEL_ID, RUNS_DIR
from handoff.data.sessions import sample_sessions
from handoff.memory.summarization import ceiling, langmem_default
from handoff.run_stm import _is_fatal

SWEEP = (768, 1536)


def _arms(with_ceiling: bool = True):
    if with_ceiling:
        yield "C", ceiling
    for budget in SWEEP:
        yield f"3a@{budget}", (lambda b=budget: langmem_default(max_tokens=b))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=12)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--no-ceiling",
        action="store_true",
        help="skip the C arm when an identical ceiling already exists for these sessions",
    )
    parser.add_argument("--free", action="store_true", help="permit abstention")
    args = parser.parse_args()

    load_dotenv()
    sessions = sample_sessions(args.sessions, seed=args.seed)
    forced = not args.free

    run_dir = RUNS_DIR / f"handoff-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    transcript = (run_dir / "sessions.jsonl").open("w")

    totals: dict[str, list[bool]] = defaultdict(list)
    silent: dict[str, list[bool]] = defaultdict(list)
    by_depth: dict[str, dict[int, list[bool]]] = defaultdict(lambda: defaultdict(list))

    for i, session in enumerate(sessions, 1):
        print(f"[{i}/{len(sessions)}] {session.ticker} {session.n_turns} turns", flush=True)
        record = {"ticker": session.ticker, "n_turns": session.n_turns, "arms": {}}
        for arm, factory in _arms(not args.no_ceiling):
            try:
                result = run_two_agent_session(session, factory(), forced=forced)
            except Exception as error:
                if _is_fatal(error):
                    transcript.write(json.dumps(record) + "\n")
                    transcript.close()
                    raise SystemExit(f"\nAborting at {i}/{len(sessions)}, arm {arm}.\n  {error}")
                print(f"  {arm} failed: {type(error).__name__}: {error}", flush=True)
                continue

            record["arms"][arm] = dataclasses.asdict(result)
            for turn in result.turns:
                totals[arm].append(turn.correct)
                silent[arm].append(turn.answered and not turn.correct)
                by_depth[arm][(turn.depth // 5) * 5].append(turn.correct)
            print(
                f"  {arm:<10} acc {sum(t.correct for t in result.turns)}/{len(result.turns)}"
                f"  rounds {result.summary_rounds}",
                flush=True,
            )
        transcript.write(json.dumps(record) + "\n")
        transcript.flush()

    transcript.close()

    summary = {
        "sessions": len(sessions),
        "seed": args.seed,
        "model_id": MODEL_ID,
        "forced": forced,
        "pipeline": "two-agent",
        "arms": {
            arm: {
                "n": len(flags),
                "accuracy": round(sum(flags) / len(flags), 4),
                "silent_wrong": round(sum(silent[arm]) / len(flags), 4),
                "accuracy_by_depth": {
                    str(b): round(sum(v) / len(v), 4) for b, v in sorted(by_depth[arm].items())
                },
            }
            for arm, flags in totals.items()
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\nwrote {run_dir}\n")
    for arm, stats in summary["arms"].items():
        print(
            f"  {arm:<10} acc {stats['accuracy']:.1%}  silent {stats['silent_wrong']:.1%}"
            f"  (n={stats['n']})  by depth {stats['accuracy_by_depth']}"
        )


if __name__ == "__main__":
    main()
