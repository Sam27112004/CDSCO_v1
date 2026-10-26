"""create_gin_indexes

Revision ID: f1a2b3c4d5e6
Revises: e0f736a11ec1
Create Date: 2026-10-26 14:07:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e0f736a11ec1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'idx_app_def_schema',
        'application_definitions',
        ['schema_payload'],
        unique=False,
        postgresql_using='gin',
    )
    op.create_index(
        'idx_submissions_regulatory_context',
        'submissions',
        ['regulatory_context'],
        unique=False,
        postgresql_using='gin',
    )


def downgrade() -> None:
    op.drop_index(
        'idx_submissions_regulatory_context',
        table_name='submissions',
        postgresql_using='gin',
    )
    op.drop_index(
        'idx_app_def_schema',
        table_name='application_definitions',
        postgresql_using='gin',
    )
