"""Notion collection imports, explicit app consent and durable cleanup."""
from alembic import op
import sqlalchemy as sa
revision='0007'
down_revision='0006'
def owner():
    return sa.Column('user_id',sa.String(80),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
def ident():return sa.Column('id',sa.String(80),primary_key=True)
def upgrade():
    op.create_table('notion_links',ident(),owner(),sa.Column('code',sa.String(80),nullable=False,unique=True),sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('consent_version',sa.String(40),nullable=False),sa.Column('created_at',sa.Float(),nullable=False),sa.UniqueConstraint('user_id'))
    op.create_table('notion_pages',ident(),owner(),sa.Column('code',sa.String(80),nullable=False),sa.Column('consented',sa.Boolean(),nullable=False))
    op.create_table('notion_imports',ident(),owner(),sa.Column('group_key',sa.String(64),nullable=False),sa.Column('source_hash',sa.String(64),nullable=False),sa.Column('contribution_id',sa.String(80),sa.ForeignKey('user_contributions.id',ondelete='SET NULL')),sa.Column('status',sa.String(40),nullable=False),sa.Column('error_code',sa.String(80)),sa.UniqueConstraint('user_id','group_key'))
    for name in ['notion_links','notion_pages','notion_imports']:op.create_index('ix_'+name+'_user_id',name,['user_id'])
    op.create_table('notion_purges',ident(),sa.Column('attempts',sa.Integer(),nullable=False))
    op.create_table('notion_worker_state',ident(),sa.Column('data',sa.JSON(),nullable=False))
def downgrade():
    for name in ['notion_worker_state','notion_purges','notion_imports','notion_pages','notion_links']:op.drop_table(name)
