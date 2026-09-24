"""Chain ConvFinQA conversations into sessions long enough to trigger summarisation.

Summarisation is token-triggered and ConvFinQA conversations average 3.64
turns, so a single conversation never reaches the threshold. Chaining several
conversations about the same company produces a realistic long session out of
real questions, with no synthetic padding.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from handoff.data.convfinqa import Conversation, Turn, load_conversations

TARGET_MIN_TURNS = 15
TARGET_MAX_TURNS = 20


@dataclass(frozen=True)
class SessionTurn:
    depth: int
    conversation_index: int
    conversation: Conversation
    turn: Turn
    starts_conversation: bool


@dataclass(frozen=True)
class ChainedSession:
    ticker: str
    conversations: tuple[Conversation, ...]

    @property
    def turns(self) -> list[SessionTurn]:
        flattened: list[SessionTurn] = []
        for c_index, conversation in enumerate(self.conversations):
            for t_index, turn in enumerate(conversation.turns):
                flattened.append(
                    SessionTurn(
                        depth=len(flattened),
                        conversation_index=c_index,
                        conversation=conversation,
                        turn=turn,
                        starts_conversation=t_index == 0,
                    )
                )
        return flattened

    @property
    def n_turns(self) -> int:
        return sum(len(c.turns) for c in self.conversations)

    @property
    def years(self) -> tuple[int, ...]:
        return tuple(c.year for c in self.conversations)


def build_sessions(
    min_turns: int = TARGET_MIN_TURNS,
    max_turns: int = TARGET_MAX_TURNS,
) -> list[ChainedSession]:
    by_ticker: dict[str, list[Conversation]] = defaultdict(list)
    for conversation in load_conversations():
        by_ticker[conversation.ticker].append(conversation)

    sessions: list[ChainedSession] = []
    for ticker, conversations in by_ticker.items():
        ordered = sorted(conversations, key=lambda c: (c.year, c.id))
        chain: list[Conversation] = []
        for conversation in ordered:
            chain.append(conversation)
            total = sum(len(c.turns) for c in chain)
            if total > max_turns:
                chain = [conversation]
                continue
            if total >= min_turns:
                sessions.append(ChainedSession(ticker=ticker, conversations=tuple(chain)))
                chain = []
    return sessions


def sample_sessions(n: int, seed: int = 0) -> list[ChainedSession]:
    """Sample at most one session per ticker so no company dominates."""
    sessions = build_sessions()
    rng = random.Random(seed)
    rng.shuffle(sessions)

    seen: set[str] = set()
    sampled = []
    for session in sessions:
        if session.ticker in seen:
            continue
        seen.add(session.ticker)
        sampled.append(session)
        if len(sampled) == n:
            break
    return sampled


if __name__ == "__main__":
    sessions = build_sessions()
    lengths = [s.n_turns for s in sessions]
    print(f"sessions            : {len(sessions)}")
    print(f"distinct companies  : {len({s.ticker for s in sessions})}")
    print(f"turns per session   : min {min(lengths)}, mean {sum(lengths)/len(lengths):.1f}, max {max(lengths)}")
    print(f"conversations chained: mean {sum(len(s.conversations) for s in sessions)/len(sessions):.1f}")
    for session in sample_sessions(5):
        print(f"  {session.ticker}: {session.n_turns} turns over years {session.years}")
