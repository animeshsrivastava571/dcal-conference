"""Numeric grading against ConvFinQA's executed answers.

ConvFinQA ships exe_ans, so correctness is checked arithmetically rather than
by an LLM judge.

Answers are graded scale-tolerantly and the matching factor is recorded: the
model reports figures in the units the filing's table states ("1,060" under an
"in thousands" header) while exe_ans is absolute, and percent-versus-ratio
differs the same way. Recording the factor keeps "right number, wrong scale"
measurable instead of collapsing it into plain wrongness -- it is the qualifier
this project exists to study. Staleness detection deliberately does not use
this tolerance; see eval/staleness.py.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from handoff.config import ANSWER_REL_TOL

_NUMBER_RE = re.compile(r"-?\$?\s*\(?\s*-?[\d,]*\.?\d+\s*\)?\s*%?")
_BARE_RE = re.compile(r"^\s*-?\$?\s*\(?\s*-?[\d,]*\.?\d+\s*\)?\s*%?\s*$")

SCALE_FACTORS = (1.0, 0.01, 100.0, 1e-3, 1e3, 1e-6, 1e6, 1e-9, 1e9)


def is_bare_number(text: str) -> bool:
    """True when the reply is a number and nothing else.

    The agent is instructed to reply with a single number. Anything else is a
    refusal or a hedge, and mining a figure out of such a reply manufactures
    answers the model never committed to -- one hedged reply was scored as a
    stale answer before this check existed.
    """
    return bool(_BARE_RE.match(text))


@dataclass(frozen=True)
class Grade:
    correct: bool
    factor: float | None = None
    answered: bool = True

    @property
    def exact(self) -> bool:
        return self.correct and self.factor == 1.0


def _clean(token: str) -> tuple[float, bool] | None:
    had_percent = "%" in token
    negative = token.strip().startswith("(") and token.strip().rstrip("%").endswith(")")
    stripped = re.sub(r"[,$%()\s]", "", token)
    if not stripped or stripped in {"-", "."}:
        return None
    try:
        value = float(stripped)
    except ValueError:
        return None
    return (-value if negative else value), had_percent


def extract_number(text: str) -> tuple[float, bool] | None:
    """Return the final numeric token in ``text`` and whether it carried a %."""
    matches = [_clean(m.group()) for m in _NUMBER_RE.finditer(text)]
    found = [m for m in matches if m is not None]
    return found[-1] if found else None


def to_float(gold: float | str) -> float | None:
    if isinstance(gold, (int, float)):
        return float(gold)
    parsed = _clean(str(gold))
    return parsed[0] if parsed else None


def grade(prediction: str, gold: float | str, rel_tol: float = ANSWER_REL_TOL) -> Grade:
    if not is_bare_number(prediction):
        return Grade(correct=False, answered=False)

    target = to_float(gold)
    parsed = extract_number(prediction)
    if target is None or parsed is None:
        return Grade(correct=False)

    value = parsed[0]
    for factor in SCALE_FACTORS:
        if math.isclose(value * factor, target, rel_tol=rel_tol, abs_tol=1e-9):
            return Grade(correct=True, factor=factor)
    return Grade(correct=False)


def is_correct(prediction: str, gold: float | str, rel_tol: float = ANSWER_REL_TOL) -> bool:
    return grade(prediction, gold, rel_tol).correct
