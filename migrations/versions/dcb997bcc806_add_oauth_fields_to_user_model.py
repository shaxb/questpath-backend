"""add oauth fields to user model

Revision ID: dcb997bcc806
Revises: 4fc77c6224a9
Create Date: 2025-12-05 23:16:50.219308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcb997bcc806'
down_revision: Union[str, Sequence[str], None] = '4fc77c6224a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make password_hash nullable (for OAuth users)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=True)
    
    # Add OAuth fields
    op.add_column('users', sa.Column('google_id', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('display_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(length=500), nullable=True))
    
    # Add unique constraint and index on google_id
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])
    op.create_index('ix_users_google_id', 'users', ['google_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index and constraint
    op.drop_index('ix_users_google_id', 'users')
    op.drop_constraint('uq_users_google_id', 'users', type_='unique')
    
    # Remove OAuth columns
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'display_name')
    op.drop_column('users', 'google_id')
    
    # Make password_hash not nullable again
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(length=255),
                    nullable=False)
