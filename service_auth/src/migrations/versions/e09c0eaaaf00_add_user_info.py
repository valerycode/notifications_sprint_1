"""add user info

Revision ID: e09c0eaaaf00
Revises: d453211656b8
Create Date: 2023-03-10 14:00:06.919467

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e09c0eaaaf00"
down_revision = "d453211656b8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("time_zone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("reject_notice", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("reject_notice")
        batch_op.drop_column("phone")
        batch_op.drop_column("time_zone")
