"""Establish the migration baseline.

Revision ID: 0001
Revises:
Create Date: 2026-07-28
"""

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """No business schema is introduced before Phase 2/3."""


def downgrade() -> None:
    """The baseline has no schema objects to remove."""
