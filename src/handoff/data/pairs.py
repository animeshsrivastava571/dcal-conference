"""Build cross-period conversation pairs for the staleness measurement."""

from __future__ import annotations

import itertools
import random
from collections import defaultdict
from dataclasses import dataclass

from handoff.config import MIN_YEAR_GAP
from handoff.data.convfinqa import Conversation, load_conversations


@dataclass(frozen=True)
class CrossPeriodPair:
    ticker: str
    early: Conversation
    late: Conversation

    @property
    def gap(self) -> int:
        return self.late.year - self.early.year


def year_pairs(min_gap: int = MIN_YEAR_GAP) -> list[tuple[str, int, int]]:
    by_ticker: dict[str, set[int]] = defaultdict(set)
    for conversation in load_conversations():
        by_ticker[conversation.ticker].add(conversation.year)

    return [
        (ticker, early, late)
        for ticker, years in by_ticker.items()
        for early, late in itertools.combinations(sorted(years), 2)
        if late - early >= min_gap
    ]


def conversation_pairs(min_gap: int = MIN_YEAR_GAP) -> list[CrossPeriodPair]:
    by_key: dict[tuple[str, int], list[Conversation]] = defaultdict(list)
    for conversation in load_conversations():
        by_key[(conversation.ticker, conversation.year)].append(conversation)

    pairs = []
    for ticker, early_year, late_year in year_pairs(min_gap):
        for early in by_key[(ticker, early_year)]:
            for late in by_key[(ticker, late_year)]:
                pairs.append(CrossPeriodPair(ticker=ticker, early=early, late=late))
    return pairs


def sample_pairs(n: int, seed: int = 0, min_gap: int = MIN_YEAR_GAP) -> list[CrossPeriodPair]:
    """Sample at most one pair per ticker so no company dominates the estimate."""
    pairs = conversation_pairs(min_gap)
    rng = random.Random(seed)
    rng.shuffle(pairs)

    seen: set[str] = set()
    sampled = []
    for pair in pairs:
        if pair.ticker in seen:
            continue
        seen.add(pair.ticker)
        sampled.append(pair)
        if len(sampled) == n:
            break
    return sampled


if __name__ == "__main__":
    yps = year_pairs()
    cps = conversation_pairs()
    print(f"year pairs (>={MIN_YEAR_GAP}y gap) : {len(yps)}")
    print(f"companies with such a span   : {len({t for t, _, _ in yps})}")
    print(f"conversation pairs           : {len(cps)}")
    sample = sample_pairs(50)
    print(f"sampled (one per ticker)     : {len(sample)}")
    for pair in sample[:5]:
        print(f"  {pair.ticker}: {pair.early.year} -> {pair.late.year} (gap {pair.gap})")
