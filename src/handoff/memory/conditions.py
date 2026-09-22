"""Memory policies, one per experimental condition.

Milestone 1 implements the floor and LangMem's shipped defaults. The remaining
conditions attach here without changing the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_anthropic import ChatAnthropic
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langmem import create_memory_store_manager

from handoff.config import MODEL_ID, Condition

EMBEDDING_MODEL = "openai:text-embedding-3-small"
EMBEDDING_DIMS = 1536

# LangMem's own default; mirrored here so recall matches what the manager sees.
DEFAULT_QUERY_LIMIT = 5

USER_ID = "analyst"


@dataclass
class MemoryPolicy:
    condition: Condition
    user_id: str = USER_ID
    store: BaseStore | None = None
    manager: Any | None = None
    namespace: tuple[str, ...] = field(default=())

    @property
    def config(self) -> dict:
        return {"configurable": {"langgraph_user_id": self.user_id}}

    def recall(self, query: str) -> list[str]:
        if self.store is None:
            return []
        items = self.store.search(self.namespace, query=query, limit=DEFAULT_QUERY_LIMIT)
        return [str(item.value.get("content", item.value)) for item in items]

    def commit(self, messages: list[dict]) -> None:
        if self.manager is None:
            return
        self.manager.invoke({"messages": messages}, config=self.config)

    def dump(self) -> list[str]:
        if self.store is None:
            return []
        items = self.store.search(self.namespace, limit=1000)
        return [str(item.value.get("content", item.value)) for item in items]


def _model() -> ChatAnthropic:
    # `model` and `max_tokens` are pydantic aliases; pyright reads the field names.
    return ChatAnthropic(model=MODEL_ID, max_tokens=4096)  # type: ignore[call-arg]


def build_policy(condition: Condition, user_id: str = USER_ID) -> MemoryPolicy:
    if condition is Condition.FLOOR:
        return MemoryPolicy(condition=condition, user_id=user_id)

    if condition is Condition.LANGMEM_DEFAULT:
        store = InMemoryStore(index={"embed": EMBEDDING_MODEL, "dims": EMBEDDING_DIMS})
        # Every argument but model and store is left at its shipped default, so
        # the measured rate is the default's rate.
        manager = create_memory_store_manager(_model(), store=store)
        return MemoryPolicy(
            condition=condition,
            user_id=user_id,
            store=store,
            manager=manager,
            namespace=("memories", user_id),
        )

    raise NotImplementedError(f"{condition} arrives in milestone 2")
