"""add_user_xp_and_level

Revision ID: 4fc77c6224a9
Revises: 6ec02bb3e3fb
Create Date: 2025-12-01 00:56:23.501091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fc77c6224a9'
down_revision: Union[str, Sequence[str], None] = '6ec02bb3e3fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add total_exp column to users table."""
    op.add_column('users', sa.Column('total_exp', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove total_exp column from users table."""
    op.drop_column('users', 'total_exp')
