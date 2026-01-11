"""add_index_to_total_exp

Revision ID: ae37b0d5d772
Revises: c04b511e060b
Create Date: 2026-01-08 23:02:25.579208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae37b0d5d772'
down_revision: Union[str, Sequence[str], None] = 'c04b511e060b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_users_total_exp', 'users', ['total_exp'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_users_total_exp', 'users')
