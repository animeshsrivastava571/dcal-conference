"""Load ConvFinQA conversations and parse their TICKER/YEAR identifiers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from handoff.config import DATA_DIR

# ConvFinQA ids carry a Single_/Double_ prefix that the underlying FinQA ids do
# not; it must come off before the TICKER/YEAR match.
_ID_RE = re.compile(r"([A-Z0-9.\-]+)/(\d{4})/")

# Test answers are withheld upstream, so only these two splits are usable.
SPLITS = ("train", "dev")


def parse_id(raw_id: str) -> tuple[str, int]:
    core = raw_id.split("_", 1)[1] if "_" in raw_id.split("/")[0] else raw_id
    match = _ID_RE.match(core)
    if match is None:
        raise ValueError(f"unparseable ConvFinQA id: {raw_id!r}")
    return match.group(1), int(match.group(2))


@dataclass(frozen=True)
class Turn:
    index: int
    question: str
    exe_ans: float | str
    program: str

    @property
    def is_computed(self) -> bool:
        """True when the answer comes from arithmetic rather than a lookup.

        Computation turns need every operand correctly qualified, so they are
        the harder half of the difficulty axis.
        """
        return "(" in self.program


@dataclass(frozen=True)
class Conversation:
    id: str
    ticker: str
    year: int
    split: str
    turns: tuple[Turn, ...]
    table: tuple[tuple[str, ...], ...]
    pre_text: tuple[str, ...]
    post_text: tuple[str, ...]

    def document_text(self) -> str:
        rows = "\n".join(" | ".join(cell for cell in row) for row in self.table)
        return "\n\n".join(
            [
                " ".join(self.pre_text).strip(),
                rows,
                " ".join(self.post_text).strip(),
            ]
        ).strip()


def _build(record: dict, split: str) -> Conversation:
    ticker, year = parse_id(record["id"])
    annotation = record["annotation"]
    questions = annotation["dialogue_break"]
    answers = annotation["exe_ans_list"]
    programs = annotation["turn_program"]

    turns = tuple(
        Turn(index=i, question=q, exe_ans=a, program=p)
        for i, (q, a, p) in enumerate(zip(questions, answers, programs))
    )
    return Conversation(
        id=record["id"],
        ticker=ticker,
        year=year,
        split=split,
        turns=turns,
        table=tuple(tuple(row) for row in record["table"]),
        pre_text=tuple(record["pre_text"]),
        post_text=tuple(record["post_text"]),
    )


@lru_cache(maxsize=1)
def load_conversations(data_dir: Path = DATA_DIR) -> tuple[Conversation, ...]:
    conversations: list[Conversation] = []
    for split in SPLITS:
        records = json.loads((data_dir / "data" / f"{split}.json").read_text())
        conversations.extend(_build(record, split) for record in records)
    return tuple(conversations)


if __name__ == "__main__":
    convs = load_conversations()
    turns = sum(len(c.turns) for c in convs)
    tickers = {c.ticker for c in convs}
    print(f"conversations : {len(convs)}")
    print(f"turns         : {turns} (mean {turns / len(convs):.2f})")
    print(f"companies     : {len(tickers)}")
