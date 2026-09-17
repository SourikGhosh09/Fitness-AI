"""Initial schema snapshot. Do not change this metadata after release."""
from alembic import op
from fitness.schema_v1 import metadata
revision='0001'
down_revision=None
def upgrade():metadata.create_all(op.get_bind())
def downgrade():metadata.drop_all(op.get_bind())
