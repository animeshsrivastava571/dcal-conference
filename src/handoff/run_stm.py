"""Run the short-term memory experiment: dilution across a long session.

Each session runs under a ceiling (full history) and under LangMem's shipped
summarisation at several trigger budgets, so accuracy can be read against turn
depth and against how many compression rounds have happened.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import traceback
from collections import defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv

from handoff.agents.stm import FORCED_INSTRUCTIONS, INSTRUCTIONS, run_chained_session
from handoff.config import MODEL_ID, RUNS_DIR
from handoff.data.sessions import sample_sessions
from handoff.memory.summarization import ceiling, langmem_default, langmem_prompted

# Sessions measure 3.1k-5.6k tokens, so these budgets bracket the point where
# summarisation first fires and then fires repeatedly. @3072 was dropped: it
# triggers barely one compression round and lands within a few points of the
# ceiling, so it consumed a quarter of every run to restate the control. The
# completed runs already carry it for the published dose-response.
SWEEP = (768, 1536)

# A dead key or an empty balance fails every remaining call. Without this the
# runner spends the whole grid printing tracebacks and writes a summary that
# looks like an experiment.
FATAL = ("credit balance is too low", "authentication_error", "invalid x-api-key")


def _is_fatal(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in FATAL)


def _arms(condition: str, with_ceiling: bool = True):
    factory = langmem_default if condition == "3a" else langmem_prompted
    if with_ceiling:
        yield "C", ceiling
    for budget in SWEEP:
        yield f"{condition}@{budget}", (lambda b=budget: factory(max_tokens=b))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--no-ceiling",
        action="store_true",
        help="skip the C arm when an identical ceiling already exists for these sessions",
    )
    parser.add_argument(
        "--condition",
        choices=("3a", "3b"),
        default="3a",
        help="3a = shipped summary prompts; 3b = qualifier-preserving prompts",
    )
    parser.add_argument(
        "--forced",
        action="store_true",
        help="forbid abstention, to test whether refusal is what keeps silent errors flat",
    )
    args = parser.parse_args()
    instructions = FORCED_INSTRUCTIONS if args.forced else INSTRUCTIONS
    suffix = "/forced" if args.forced else ""

    load_dotenv()
    sessions = sample_sessions(args.sessions, seed=args.seed)

    tag = f"stm{args.condition}{'-forced' if args.forced else ''}"
    run_dir = RUNS_DIR / f"{tag}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    transcript = (run_dir / "sessions.jsonl").open("w")

    # arm -> depth bucket -> [correct flags]
    by_depth: dict[str, dict[int, list[bool]]] = defaultdict(lambda: defaultdict(list))
    by_rounds: dict[str, dict[int, list[bool]]] = defaultdict(lambda: defaultdict(list))
    totals: dict[str, list[bool]] = defaultdict(list)
    rounds_seen: dict[str, list[int]] = defaultdict(list)
    failures = 0

    for i, session in enumerate(sessions, 1):
        print(f"[{i}/{len(sessions)}] {session.ticker} {session.n_turns} turns", flush=True)
        record = {"ticker": session.ticker, "n_turns": session.n_turns, "arms": {}}
        for base_arm, factory in _arms(args.condition, not args.no_ceiling):
            arm = f"{base_arm}{suffix}"
            try:
                result = run_chained_session(
                    session, factory(), instructions=instructions
                )
            except Exception as error:
                if _is_fatal(error):
                    transcript.write(json.dumps(record) + "\n")
                    transcript.close()
                    raise SystemExit(
                        f"\nAborting at session {i}/{len(sessions)}, arm {arm}.\n"
                        f"  {error}\n"
                        f"Partial transcript: {run_dir / 'sessions.jsonl'}"
                    )
                failures += 1
                print(f"  {arm} failed: {traceback.format_exc(limit=1).strip()}", flush=True)
                continue

            record["arms"][arm] = dataclasses.asdict(result)
            rounds_seen[arm].append(result.summary_rounds)
            for turn in result.turns:
                bucket = (turn.depth // 5) * 5
                by_depth[arm][bucket].append(turn.correct)
                by_rounds[arm][turn.summary_rounds].append(turn.correct)
                totals[arm].append(turn.correct)
            print(
                f"  {arm:<10} acc {sum(t.correct for t in result.turns)}/{len(result.turns)}"
                f"  summary rounds {result.summary_rounds}",
                flush=True,
            )
        transcript.write(json.dumps(record) + "\n")
        transcript.flush()

    transcript.close()

    def pct(flags: list[bool]) -> str:
        return f"{sum(flags)}/{len(flags)} = {sum(flags)/len(flags):.1%}" if flags else "n/a"

    summary = {
        "sessions": len(sessions),
        "failures": failures,
        "seed": args.seed,
        "model_id": MODEL_ID,
        "condition": args.condition,
        "forced": args.forced,
        "arms": {
            arm: {
                "overall": {"n": len(flags), "correct": sum(flags), "accuracy": round(sum(flags) / len(flags), 4)},
                "mean_summary_rounds": round(sum(rounds_seen[arm]) / len(rounds_seen[arm]), 2) if rounds_seen[arm] else 0,
                "accuracy_by_depth": {
                    str(b): round(sum(v) / len(v), 4) for b, v in sorted(by_depth[arm].items())
                },
                "accuracy_by_summary_round": {
                    str(r): round(sum(v) / len(v), 4) for r, v in sorted(by_rounds[arm].items())
                },
            }
            for arm, flags in totals.items()
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\nwrote {run_dir}\n")
    for arm, flags in totals.items():
        stats = summary["arms"][arm]
        print(f"  {arm:<10} overall {pct(flags):<18} rounds~{stats['mean_summary_rounds']}")
        print(f"  {'':<10} by depth: {stats['accuracy_by_depth']}")


if __name__ == "__main__":
    main()
