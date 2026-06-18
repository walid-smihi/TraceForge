"""Add LLM justification to trace links

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-18
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE trace_links ADD COLUMN justification TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE trace_links DROP COLUMN justification")
