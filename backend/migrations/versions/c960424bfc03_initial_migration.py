"""Initial migration

Revision ID: c960424bfc03
Revises: 
Create Date: 2026-05-10 17:59:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c960424bfc03'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create extension for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create businesses table
    op.create_table(
        'businesses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ceo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='building'),
        sa.Column('current_phase', sa.String(length=50), nullable=False, server_default='initialization'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('launched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ai_tasks table
    op.create_table(
        'ai_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_name', sa.String(length=50), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_by_ceo_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create approval_requests table
    op.create_table(
        'approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('proposed_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('impact_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('urgency', sa.String(length=50), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('ceo_decision', sa.Text(), nullable=True),
        sa.Column('decided_by_ceo_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['ai_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create metrics_snapshots table
    op.create_table(
        'metrics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recorded_by_role', sa.String(length=50), nullable=False),
        sa.Column('daily_revenue', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('weekly_revenue', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('monthly_revenue', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('users_count', sa.Integer(), nullable=True),
        sa.Column('active_users_count', sa.Integer(), nullable=True),
        sa.Column('churn_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('bug_count', sa.Integer(), nullable=True),
        sa.Column('support_tickets_count', sa.Integer(), nullable=True),
        sa.Column('open_support_tickets', sa.Integer(), nullable=True),
        sa.Column('conversion_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('customer_acquisition_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('lifetime_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('custom_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_feedback table
    op.create_table(
        'user_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('feedback_type', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sentiment_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('processed_by_ai', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('environment', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('triggered_by_role', sa.String(length=50), nullable=True),
        sa.Column('approved_by_ceo_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rollback_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent_executions table
    op.create_table(
        'agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_name', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_businesses_status', 'businesses', ['status'], unique=False)
    op.create_index('idx_businesses_ceo_id', 'businesses', ['ceo_id'], unique=False)
    op.create_index('idx_ai_tasks_business_id', 'ai_tasks', ['business_id'], unique=False)
    op.create_index('idx_ai_tasks_status', 'ai_tasks', ['status'], unique=False)
    op.create_index('idx_approval_requests_business_id', 'approval_requests', ['business_id'], unique=False)
    op.create_index('idx_approval_requests_status', 'approval_requests', ['status'], unique=False)
    op.create_index('idx_metrics_business_id_recorded_at', 'metrics_snapshots', ['business_id', 'recorded_at'], unique=False, postgresql_using='btree')
    op.create_index('idx_feedback_business_id', 'user_feedback', ['business_id'], unique=False)
    op.create_index('idx_deployments_business_id', 'deployments', ['business_id'], unique=False)
    
    # Create trigger function and trigger for updated_at
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)
    
    op.execute("""
    CREATE TRIGGER update_businesses_updated_at BEFORE UPDATE ON businesses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    # Drop trigger
    op.execute('DROP TRIGGER IF EXISTS update_businesses_updated_at ON businesses')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column')
    
    # Drop tables in reverse order to avoid foreign key constraints
    op.drop_table('agent_executions')
    op.drop_table('deployments')
    op.drop_table('user_feedback')
    op.drop_table('metrics_snapshots')
    op.drop_table('approval_requests')
    op.drop_table('ai_tasks')
    op.drop_table('businesses')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')