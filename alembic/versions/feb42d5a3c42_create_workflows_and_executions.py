from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'feb42d5a3c42'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()
    if 'workflows' not in tables:
        op.create_table(
            'workflows',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('steps', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_workflows_id'), 'workflows', ['id'], unique=False)

    if 'executions' not in tables:
        op.create_table(
            'executions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('input', sa.Text(), nullable=False),
            sa.Column('output', sa.Text(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False),
            sa.Column('step_results', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_executions_id'), 'executions', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_executions_id'), table_name='executions')
    op.drop_table('executions')
    op.drop_index(op.f('ix_workflows_id'), table_name='workflows')
    op.drop_table('workflows')
