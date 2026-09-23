"""Two-agent pipeline: a retrieval agent hands figures to an analysis agent.

The handoff is the point the paper is named for. A retrieval agent reads the
filing and states what it found; an analysis agent answers using that statement
and never sees the filing. Whatever the retrieval agent leaves out is gone.

Two things protect this from the reviewer's fair objection that we designed the
result. The transfer uses LangGraph's documented handoff primitive
(``Command(goto=...)``) rather than a bespoke protocol, and the payload is the
retrieval agent's own message - there is no separate "summarise for handoff"
step that we could have tuned. The compression at the boundary is whatever an
agent naturally produces when asked to report what it found.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict

from handoff.agents.caching import mark_cache_breakpoint
from handoff.config import MODEL_ID
from handoff.data.sessions import ChainedSession
from handoff.eval.correctness import grade
from handoff.memory.summarization import SummarizationPolicy

RETRIEVAL_INSTRUCTIONS = (
    "You are a retrieval agent working on company filings. Another agent will "
    "answer the analyst's question using only what you report, and it cannot "
    "see the filing. Report the figures relevant to the question. Do not "
    "answer the question yourself."
)

ANALYSIS_INSTRUCTIONS = (
    "You are an analysis agent. You cannot see the source filing. Answer the "
    "analyst's question using only the retrieval agent's report and the "
    "conversation so far. Reply with a single number and nothing else: no "
    "units, no currency symbols, no commas, no explanation. If the question "
    "asks for a change or a ratio, give the computed value."
)

FORCED_CLAUSE = (
    " You must always reply with a number. Never say that you cannot answer, "
    "that information is missing or unavailable, and never ask for "
    "clarification. If you are unsure, give your best estimate as a number."
)


class HandoffState(TypedDict):
    history: list
    filing: str
    question: str
    digest: str
    answer: str
    forced: bool


def _build_graph(llm: ChatAnthropic):
    def retrieval(state: HandoffState) -> Command[Literal["analysis"]]:
        prompt = state["question"]
        if state["filing"]:
            prompt = f"{state['filing']}\n\nThe analyst asks: {state['question']}"
        response = llm.invoke(
            mark_cache_breakpoint(
                [
                    SystemMessage(content=RETRIEVAL_INSTRUCTIONS),
                    *state["history"],
                    HumanMessage(content=prompt),
                ]
            )
        )
        return Command(goto="analysis", update={"digest": response.text})

    def analysis(state: HandoffState) -> HandoffState:
        instructions = ANALYSIS_INSTRUCTIONS + (FORCED_CLAUSE if state["forced"] else "")
        response = llm.invoke(
            [
                SystemMessage(content=instructions),
                *state["history"],
                HumanMessage(
                    content=(
                        f"Retrieval agent's report:\n{state['digest']}\n\n"
                        f"Question: {state['question']}"
                    )
                ),
            ]
        )
        return {**state, "answer": response.text}

    graph = StateGraph(HandoffState)
    graph.add_node("retrieval", retrieval)
    graph.add_node("analysis", analysis)
    graph.add_edge(START, "retrieval")
    graph.add_edge("analysis", END)
    return graph.compile()


@dataclass
class HandoffTurnResult:
    depth: int
    ticker: str
    year: int
    question: str
    gold: float | str
    digest: str
    prediction: str
    correct: bool
    answered: bool
    scale_factor: float | None
    is_computed: bool
    summary_rounds: int


@dataclass
class HandoffSessionResult:
    ticker: str
    arm: str
    n_turns: int
    model_id: str
    forced: bool
    summary_rounds: int = 0
    summaries: list[str] = field(default_factory=list)
    turns: list[HandoffTurnResult] = field(default_factory=list)


def run_two_agent_session(
    session: ChainedSession,
    policy: SummarizationPolicy,
    forced: bool = True,
    model: ChatAnthropic | None = None,
) -> HandoffSessionResult:
    # `model` and `max_tokens` are pydantic aliases; pyright reads field names.
    llm = model or ChatAnthropic(model=MODEL_ID, max_tokens=1024)  # type: ignore[call-arg]
    app = _build_graph(llm)
    system = SystemMessage(content=ANALYSIS_INSTRUCTIONS, id="system")
    history: list = []
    result = HandoffSessionResult(
        ticker=session.ticker,
        arm=f"{policy.label}+handoff",
        n_turns=session.n_turns,
        model_id=llm.model,
        forced=forced,
    )

    for step in session.turns:
        # The retrieval agent is the one holding the documents, so it keeps the
        # current filing on every turn. Only the analysis agent is cut off from
        # the source, which is what isolates the boundary.
        filing = (
            f"Filing: {step.conversation.ticker} {step.conversation.year}\n\n"
            f"{step.conversation.document_text()}"
        )

        compressed = policy.prepare([system, *history])[1:]
        state = app.invoke(
            {
                "history": compressed,
                "filing": filing,
                "question": step.turn.question,
                "digest": "",
                "answer": "",
                "forced": forced,
            }
        )
        prediction = state["answer"]
        scored = grade(prediction, step.turn.exe_ans)
        result.turns.append(
            HandoffTurnResult(
                depth=step.depth,
                ticker=step.conversation.ticker,
                year=step.conversation.year,
                question=step.turn.question,
                gold=step.turn.exe_ans,
                digest=state["digest"],
                prediction=prediction.strip(),
                correct=scored.correct,
                answered=scored.answered,
                scale_factor=scored.factor,
                is_computed=step.turn.is_computed,
                summary_rounds=policy.rounds,
            )
        )
        # The shared memory holds what the agents exchanged, not just the final
        # answer: the retrieval report is what a later turn has to fall back on
        # once the filing is no longer in view, and it is what compression eats.
        history.extend(
            [
                HumanMessage(content=step.turn.question, id=f"u{step.depth}"),
                AIMessage(
                    content=f"[retrieval] {state['digest']}\n\n[analysis] {prediction}",
                    id=f"a{step.depth}",
                ),
            ]
        )

    result.summary_rounds = policy.rounds
    result.summaries = list(policy.summaries)
    return result
