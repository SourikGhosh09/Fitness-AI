"""Allow owner-authorized media with no stated expiration."""
from alembic import op
import sqlalchemy as sa
revision='0003'
down_revision='0002'

def upgrade():
    with op.batch_alter_table('media_license_grants') as batch:
        batch.alter_column('expires_at',existing_type=sa.Float(),nullable=True)

def downgrade():
    # Preserve rows; indefinite grants become inactive rather than inventing an expiry.
    op.execute('UPDATE media_license_grants SET expires_at=0, revoked=true WHERE expires_at IS NULL')
    with op.batch_alter_table('media_license_grants') as batch:
        batch.alter_column('expires_at',existing_type=sa.Float(),nullable=False)
