"""rename_pr_analyses_to_deployment_analyses

Revision ID: a1b2c3d4e5f6
Revises: 47f04f0cbec8
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '47f04f0cbec8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the table
    op.rename_table('pr_analyses', 'deployment_analyses')
    
    # Rename indexes
    op.drop_index('ix_pr_analyses_api_key_id', table_name='deployment_analyses')
    op.drop_index('ix_pr_analyses_job_id', table_name='deployment_analyses')
    op.drop_index('ix_pr_analyses_user_id', table_name='deployment_analyses')
    op.drop_index('ix_pr_analyses_webhook_event_id', table_name='deployment_analyses')
    
    op.create_index(op.f('ix_deployment_analyses_api_key_id'), 'deployment_analyses', ['api_key_id'], unique=False)
    op.create_index(op.f('ix_deployment_analyses_job_id'), 'deployment_analyses', ['job_id'], unique=False)
    op.create_index(op.f('ix_deployment_analyses_user_id'), 'deployment_analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_deployment_analyses_webhook_event_id'), 'deployment_analyses', ['webhook_event_id'], unique=False)


def downgrade() -> None:
    # Rename indexes back
    op.drop_index(op.f('ix_deployment_analyses_webhook_event_id'), table_name='deployment_analyses')
    op.drop_index(op.f('ix_deployment_analyses_user_id'), table_name='deployment_analyses')
    op.drop_index(op.f('ix_deployment_analyses_job_id'), table_name='deployment_analyses')
    op.drop_index(op.f('ix_deployment_analyses_api_key_id'), table_name='deployment_analyses')
    
    op.create_index('ix_pr_analyses_webhook_event_id', 'deployment_analyses', ['webhook_event_id'], unique=False)
    op.create_index('ix_pr_analyses_user_id', 'deployment_analyses', ['user_id'], unique=False)
    op.create_index('ix_pr_analyses_job_id', 'deployment_analyses', ['job_id'], unique=False)
    op.create_index('ix_pr_analyses_api_key_id', 'deployment_analyses', ['api_key_id'], unique=False)
    
    # Rename the table back
    op.rename_table('deployment_analyses', 'pr_analyses')
