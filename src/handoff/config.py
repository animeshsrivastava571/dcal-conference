"""Pinned run configuration for the Lost in Handoff experiments."""

from __future__ import annotations

import enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RUNS_DIR = PROJECT_ROOT / "runs"

# Dated snapshot, not the floating alias: API models change silently behind an
# unversioned name, which would make the reported numbers unreproducible.
MODEL_ID = "claude-haiku-4-5-20251001"

# Annual reports carry 2-3 years of comparatives, so below this gap the "stale"
# figure is legitimately present in the later document and the test is vacuous.
MIN_YEAR_GAP = 5

ANSWER_REL_TOL = 0.01


class Condition(enum.Enum):
    FLOOR = "F"
    LANGMEM_DEFAULT = "3a"
    LANGMEM_PROMPTED = "3b"
    LANGMEM_TYPED = "3c"
    CEILING = "C"
