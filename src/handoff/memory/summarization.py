"""Short-term memory policies wrapping LangMem's running-summary machinery."""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate
from langmem.short_term.summarization import (
    DEFAULT_EXISTING_SUMMARY_PROMPT,
    DEFAULT_INITIAL_SUMMARY_PROMPT,
    RunningSummary,
    summarize_messages,
)

# The shipped prompts are "Create a summary of the conversation above:" and
# "Extend this summary...". Neither mentions numbers, periods or units. These
# replacements name the three qualifiers explicitly and tell the summariser to
# drop a figure it cannot fully qualify, which should push failures back toward
# abstention rather than bare figures.
_QUALIFIER_RULE = (
    " Every figure you carry forward must keep the company it belongs to, the "
    "fiscal period it covers, and its unit or scale. If you cannot record a "
    "figure with all three, omit that figure rather than recording it bare."
)

QUALIFIER_INITIAL_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("placeholder", "{messages}"),
        ("user", "Create a summary of the conversation above:" + _QUALIFIER_RULE),
    ]
)

QUALIFIER_EXISTING_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("placeholder", "{messages}"),
        (
            "user",
            "This is summary of the conversation so far: {existing_summary}\n\n"
            "Extend this summary by taking into account the new messages above."
            + _QUALIFIER_RULE
            + " This applies to figures already present in the summary as well.",
        ),
    ]
)

from handoff.config import MODEL_ID

# LangMem's own default, restated so the ceiling and the swept arms are
# explicit about what they hold fixed.
DEFAULT_MAX_SUMMARY_TOKENS = 256


@dataclass
class SummarizationPolicy:
    """One short-term memory arm.

    ``enabled=False`` is the ceiling: full history, nothing compressed.
    """

    label: str
    enabled: bool
    max_tokens: int = 4096
    max_tokens_before_summary: int | None = None
    max_summary_tokens: int = DEFAULT_MAX_SUMMARY_TOKENS
    model: LanguageModelLike | None = None
    initial_prompt: ChatPromptTemplate = field(
        default_factory=lambda: DEFAULT_INITIAL_SUMMARY_PROMPT
    )
    existing_prompt: ChatPromptTemplate = field(
        default_factory=lambda: DEFAULT_EXISTING_SUMMARY_PROMPT
    )
    running_summary: RunningSummary | None = None
    rounds: int = 0
    summaries: list[str] = field(default_factory=list)

    def prepare(self, messages: list[AnyMessage]) -> list[AnyMessage]:
        if not self.enabled:
            return messages
        if self.model is None:
            raise ValueError("a summarising policy needs a model")

        result = summarize_messages(
            messages,
            running_summary=self.running_summary,
            model=self.model,
            max_tokens=self.max_tokens,
            max_tokens_before_summary=self.max_tokens_before_summary,
            max_summary_tokens=self.max_summary_tokens,
            initial_summary_prompt=self.initial_prompt,
            existing_summary_prompt=self.existing_prompt,
        )

        latest = result.running_summary
        if latest is not None and (
            self.running_summary is None or latest.summary != self.running_summary.summary
        ):
            self.rounds += 1
            self.summaries.append(latest.summary)

        self.running_summary = latest
        return result.messages

    @property
    def summary_text(self) -> str | None:
        return self.running_summary.summary if self.running_summary else None


def ceiling() -> SummarizationPolicy:
    return SummarizationPolicy(label="C", enabled=False)


def langmem_default(
    max_tokens: int = 4096,
    max_tokens_before_summary: int | None = None,
    model: LanguageModelLike | None = None,
) -> SummarizationPolicy:
    """LangMem's shipped summarisation, with only the trigger budget varied."""
    from langchain_anthropic import ChatAnthropic

    return SummarizationPolicy(
        label="3a",
        enabled=True,
        max_tokens=max_tokens,
        # shipped prompts left untouched
        max_tokens_before_summary=max_tokens_before_summary,
        # `model` and `max_tokens` are pydantic aliases; pyright reads field names.
        model=model or ChatAnthropic(model=MODEL_ID, max_tokens=1024),  # type: ignore[call-arg]
    )


def langmem_prompted(
    max_tokens: int = 4096,
    max_tokens_before_summary: int | None = None,
    model: LanguageModelLike | None = None,
) -> SummarizationPolicy:
    """Condition 3b: the same machinery with qualifier-preserving prompts.

    Separates an instructional failure from a structural one. If the loss is
    instructional this closes the gap; if the flat summary string and the fixed
    budget are what cost the qualifiers, it will not.
    """
    from langchain_anthropic import ChatAnthropic

    return SummarizationPolicy(
        label="3b",
        enabled=True,
        max_tokens=max_tokens,
        max_tokens_before_summary=max_tokens_before_summary,
        initial_prompt=QUALIFIER_INITIAL_PROMPT,
        existing_prompt=QUALIFIER_EXISTING_PROMPT,
        # `model` and `max_tokens` are pydantic aliases; pyright reads field names.
        model=model or ChatAnthropic(model=MODEL_ID, max_tokens=1024),  # type: ignore[call-arg]
    )
