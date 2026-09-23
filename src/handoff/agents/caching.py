"""Prompt caching for the growing conversation prefix.

Every turn resends the whole session so far, and the filings inside it dominate
the token count. Marking the end of the stable prefix lets the API serve those
tokens from cache at a tenth of the price; only the new turn is charged in
full. Measured over the 12-session grid this is about 80% of input spend.
"""

from __future__ import annotations

from langchain_core.messages import AnyMessage

# Below this the API silently declines to cache, so marking a short prefix
# costs a cache-write with no read to follow.
MIN_CACHEABLE_TOKENS = 2048


def mark_cache_breakpoint(messages: list[AnyMessage]) -> list[AnyMessage]:
    """Put a cache breakpoint at the end of ``messages``.

    Returns the same list with its final message rewritten to block form
    carrying ``cache_control``. Earlier messages are untouched, so the cached
    prefix keeps matching as the conversation grows.
    """
    if not messages:
        return messages

    last = messages[-1]
    content = last.content
    if isinstance(content, str):
        blocks: list = [{"type": "text", "text": content}]
    elif isinstance(content, list):
        blocks = [
            {"type": "text", "text": block} if isinstance(block, str) else dict(block)
            for block in content
        ]
    else:
        return messages

    if not blocks:
        return messages

    blocks[-1] = {**blocks[-1], "cache_control": {"type": "ephemeral"}}
    marked = last.model_copy(update={"content": blocks})
    return [*messages[:-1], marked]
