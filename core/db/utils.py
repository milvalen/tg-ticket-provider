"""Shared SQLModel base (same idea as main-backend core/db/utils.AbstractModel)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlmodel import Field, SQLModel


class AbstractModel(SQLModel):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=True,
        sa_column_kwargs={"server_default": text("current_timestamp(0)")},
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=True,
        sa_column_kwargs={
            "server_default": text("current_timestamp(0)"),
            "onupdate": text("current_timestamp(0)"),
        },
    )
