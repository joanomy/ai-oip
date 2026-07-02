"""CollectedItem: the normalized shape of one piece of collected raw signal.

Every collector, regardless of source, emits this — it is the contract
between `collectors/` and everything downstream (the Problem Extraction
agent consumes these). Source-specific fields that don't generalize go
in `metadata` rather than growing the schema per source.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CollectedItem(BaseModel):
    """One collected document/post/entry, normalized across sources."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Collector name that produced this (e.g. 'hackernews').")
    external_id: str = Field(description="The item's ID in the source system.")
    title: str
    url: str | None = None
    text: str | None = Field(default=None, description="Body text, when the source provides one.")
    author: str | None = None
    created_at: datetime = Field(description="When the item was created at the source.")
    metadata: dict[str, object] = Field(
        default_factory=dict,
        description="Source-specific extras (score, comment count, ...).",
    )
