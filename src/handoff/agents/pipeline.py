"""Single-agent answering loop over one ConvFinQA conversation."""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from handoff.config import MODEL_ID
from handoff.data.convfinqa import Conversation
from handoff.eval.correctness import grade
from handoff.memory.conditions import MemoryPolicy

INSTRUCTIONS = (
    "You are a financial analyst assistant answering questions about company "
    "filings. Reply with a single number and nothing else: no units, no "
    "currency symbols, no commas, no explanation. If the question asks for a "
    "change or a ratio, give the computed value."
)

NO_DOCUMENT_NOTE = (
    "The source filing is not available in this session. Answer from the notes "
    "below and your recollection."
)


@dataclass
class TurnResult:
    index: int
    question: str
    gold: float | str
    prediction: str
    correct: bool
    scale_factor: float | None
    recalled: list[str] = field(default_factory=list)


@dataclass
class SessionResult:
    conversation_id: str
    ticker: str
    year: int
    include_document: bool
    turns: list[TurnResult] = field(default_factory=list)


def _system_message(conversation: Conversation, include_document: bool) -> SystemMessage:
    blocks: list[str | dict] = [{"type": "text", "text": INSTRUCTIONS}]
    if include_document:
        blocks.append(
            {
                "type": "text",
                "text": (
                    f"Filing: {conversation.ticker} {conversation.year}\n\n"
                    f"{conversation.document_text()}"
                ),
                # The same filing is resent every turn, so cache the prefix.
                "cache_control": {"type": "ephemeral"},
            }
        )
    else:
        blocks.append({"type": "text", "text": NO_DOCUMENT_NOTE})
    return SystemMessage(content=blocks)


def run_session(
    conversation: Conversation,
    policy: MemoryPolicy,
    include_document: bool = True,
    model: ChatAnthropic | None = None,
    commit: bool = True,
) -> SessionResult:
    # `model` and `max_tokens` are pydantic aliases; pyright reads the field names.
    llm = model or ChatAnthropic(model=MODEL_ID, max_tokens=1024)  # type: ignore[call-arg]
    system = _system_message(conversation, include_document)
    history: list = []
    result = SessionResult(
        conversation_id=conversation.id,
        ticker=conversation.ticker,
        year=conversation.year,
        include_document=include_document,
    )

    for turn in conversation.turns:
        recalled = policy.recall(turn.question)
        if recalled:
            notes = "\n".join(f"- {note}" for note in recalled)
            prompt = f"Notes from earlier sessions:\n{notes}\n\nQuestion: {turn.question}"
        else:
            prompt = turn.question

        user_message = HumanMessage(content=prompt)
        response = llm.invoke([system, *history, user_message])
        prediction = response.text

        history.extend([user_message, AIMessage(content=prediction)])
        scored = grade(prediction, turn.exe_ans)
        result.turns.append(
            TurnResult(
                index=turn.index,
                question=turn.question,
                gold=turn.exe_ans,
                prediction=prediction.strip(),
                correct=scored.correct,
                scale_factor=scored.factor,
                recalled=recalled,
            )
        )

    if commit:
        policy.commit([m.model_dump() for m in history])
    return result
