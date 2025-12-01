"""update_topics_to_objects

Revision ID: 6ec02bb3e3fb
Revises: 0677bd7ad865
Create Date: 2025-11-25 21:23:08.457659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ec02bb3e3fb'
down_revision: Union[str, Sequence[str], None] = '0677bd7ad865'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert existing topics from array of strings to array of objects."""
    # Use raw SQL to transform existing data
    op.execute("""
        UPDATE levels
        SET topics = (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'name', topic_value,
                    'completed', false
                )
            )
            FROM jsonb_array_elements_text(topics::jsonb) AS topic_value
        )
        WHERE topics IS NOT NULL AND topics::text != '[]'
    """)


def downgrade() -> None:
    """Convert topics back from array of objects to array of strings."""
    # In case we need to rollback
    op.execute("""
        UPDATE levels
        SET topics = (
            SELECT jsonb_agg(topic->>'name')
            FROM jsonb_array_elements(topics::jsonb) AS topic
        )
        WHERE topics IS NOT NULL
    """)
