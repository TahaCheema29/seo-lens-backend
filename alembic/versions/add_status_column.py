"""add status column to tables

Revision ID: add_status_column
Revises: efe27befbe47
Create Date: 2024-03-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_status_column'
down_revision: Union[str, None] = 'efe27befbe47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    op.execute("CREATE TYPE analysisstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')")
    
    # Add status column to seo_insight_results
    op.add_column('seo_insight_results', 
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'), 
                  nullable=False, server_default='COMPLETED'))
    
    # Add status column to keyword_suggestions
    op.add_column('keyword_suggestions',
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'),
                  nullable=False, server_default='COMPLETED'))
    
    # Add status column to keyword_rank_results
    op.add_column('keyword_rank_results',
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'),
                  nullable=False, server_default='COMPLETED'))


def downgrade() -> None:
    op.drop_column('keyword_rank_results', 'status')
    op.drop_column('keyword_suggestions', 'status')
    op.drop_column('seo_insight_results', 'status')
    op.execute("DROP TYPE analysisstatus")