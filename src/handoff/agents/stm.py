"""Answering loop over a chained session, under a short-term memory policy.

Filings arrive as turn-level messages rather than a pinned system block, so
that compression can reach them. LangMem exempts the system message from
summarisation, so a document parked there would never be compressed and the
measurement would be vacuous.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from handoff.config import MODEL_ID
from handoff.data.sessions import ChainedSession
from handoff.eval.correctness import grade
from handoff.memory.summarization import SummarizationPolicy

INSTRUCTIONS = (
    "You are a financial analyst assistant answering questions about company "
    "filings. Reply with a single number and nothing else: no units, no "
    "currency symbols, no commas, no explanation. If the question asks for a "
    "change or a ratio, give the computed value."
)

# Abstention is free under INSTRUCTIONS, which may be why compression produced
# loud refusals rather than wrong figures. This variant removes that escape so
# the silent-error rate can be measured when the agent must commit.
FORCED_INSTRUCTIONS = INSTRUCTIONS + (
    " You must always reply with a number. Never say that you cannot answer, "
    "that information is missing or unavailable, and never ask for "
    "clarification. If you are unsure, give your best estimate as a number."
)


@dataclass
class STMTurnResult:
    depth: int
    conversation_index: int
    ticker: str
    year: int
    question: str
    gold: float | str
    prediction: str
    correct: bool
    answered: bool
    scale_factor: float | None
    is_computed: bool
    summary_rounds: int
    messages_sent: int
    summary_active: bool


@dataclass
class STMSessionResult:
    ticker: str
    arm: str
    n_turns: int
    years: list[int]
    model_id: str = MODEL_ID
    forced: bool = False
    summary_rounds: int = 0
    summaries: list[str] = field(default_factory=list)
    turns: list[STMTurnResult] = field(default_factory=list)


def run_chained_session(
    session: ChainedSession,
    policy: SummarizationPolicy,
    model: ChatAnthropic | None = None,
    instructions: str = INSTRUCTIONS,
) -> STMSessionResult:
    # `model` and `max_tokens` are pydantic aliases; pyright reads field names.
    llm = model or ChatAnthropic(model=MODEL_ID, max_tokens=1024)  # type: ignore[call-arg]
    # summarize_messages tracks what it has already compressed by message id.
    system = SystemMessage(content=instructions, id="system")
    history: list = []
    result = STMSessionResult(
        ticker=session.ticker,
        arm=policy.label,
        n_turns=session.n_turns,
        years=list(session.years),
        model_id=llm.model,
        forced=instructions is FORCED_INSTRUCTIONS,
    )

    for step in session.turns:
        text = step.turn.question
        if step.starts_conversation:
            text = (
                f"Filing: {step.conversation.ticker} {step.conversation.year}\n\n"
                f"{step.conversation.document_text()}\n\n"
                f"Question: {text}"
            )
        user_message = HumanMessage(content=text, id=f"u{step.depth}")

        # Compress the history, then ask. Including the pending question in the
        # window lets a tight budget summarise it away, leaving a request with
        # no user message at all.
        prepared = [*policy.prepare([system, *history]), user_message]
        response = llm.invoke(prepared)
        prediction = response.text

        scored = grade(prediction, step.turn.exe_ans)
        result.turns.append(
            STMTurnResult(
                depth=step.depth,
                conversation_index=step.conversation_index,
                ticker=step.conversation.ticker,
                year=step.conversation.year,
                question=step.turn.question,
                gold=step.turn.exe_ans,
                prediction=prediction.strip(),
                correct=scored.correct,
                answered=scored.answered,
                scale_factor=scored.factor,
                is_computed=step.turn.is_computed,
                summary_rounds=policy.rounds,
                messages_sent=len(prepared),
                summary_active=policy.summary_text is not None,
            )
        )
        history.extend(
            [user_message, AIMessage(content=prediction, id=f"a{step.depth}")]
        )

    result.summary_rounds = policy.rounds
    result.summaries = list(policy.summaries)
    return result
