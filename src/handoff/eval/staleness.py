"""Stale-answer detection for cross-period pairs.

A late-year question is stale when the answer carries the early year's value
instead of the correct one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from handoff.agents.pipeline import SessionResult
from handoff.config import ANSWER_REL_TOL
from handoff.eval.correctness import extract_number, is_bare_number, to_float

Z = 1.96


@dataclass
class StaleTurn:
    conversation_id: str
    index: int
    question: str
    prediction: str
    gold: float | str
    matched_early_value: float


@dataclass
class StalenessReport:
    eligible: int = 0
    stale: int = 0
    correct: int = 0
    abstained: int = 0
    other_wrong: int = 0
    ambiguous: int = 0
    examples: list[StaleTurn] = field(default_factory=list)

    @property
    def rate(self) -> float:
        return self.stale / self.eligible if self.eligible else 0.0

    @property
    def confidence_interval(self) -> tuple[float, float]:
        """Wilson score interval; at n=50 the interval is wide by design."""
        n = self.eligible
        if n == 0:
            return (0.0, 0.0)
        p = self.rate
        denom = 1 + Z**2 / n
        centre = (p + Z**2 / (2 * n)) / denom
        half = Z / denom * math.sqrt(p * (1 - p) / n + Z**2 / (4 * n**2))
        return (max(0.0, centre - half), min(1.0, centre + half))


def _matches(value: float, target: float) -> bool:
    return math.isclose(value, target, rel_tol=ANSWER_REL_TOL, abs_tol=1e-6)


def score_pair(early: SessionResult, late: SessionResult, report: StalenessReport) -> None:
    early_values = [v for v in (to_float(t.gold) for t in early.turns) if v is not None]

    for turn in late.turns:
        gold = to_float(turn.gold)
        if gold is None:
            continue

        # A late answer that coincides with an early value cannot distinguish
        # stale recall from a correct answer, so it is not eligible.
        if any(_matches(gold, early) for early in early_values):
            report.ambiguous += 1
            continue

        report.eligible += 1

        if turn.correct:
            report.correct += 1
            continue

        # A hedge or refusal is an abstention, not a stale answer. Mining it for
        # a figure would credit the model with a commitment it did not make.
        parsed = extract_number(turn.prediction)
        if not is_bare_number(turn.prediction) or parsed is None:
            report.abstained += 1
            continue

        predicted = parsed[0]
        match = next((v for v in early_values if _matches(predicted, v)), None)
        if match is None:
            report.other_wrong += 1
        else:
            report.stale += 1
            report.examples.append(
                StaleTurn(
                    conversation_id=late.conversation_id,
                    index=turn.index,
                    question=turn.question,
                    prediction=turn.prediction,
                    gold=turn.gold,
                    matched_early_value=match,
                )
            )
