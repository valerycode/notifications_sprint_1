"""add social_account

Revision ID: d453211656b8
Revises: f78ec4dde70c
Create Date: 2023-01-29 13:14:43.394639

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d453211656b8"
down_revision = "f78ec4dde70c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "social_account",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("social_net_user_id", sa.String(255), nullable=False),
        sa.Column("social_net_name", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("social_net_user_id", "social_net_name", name="social_pk"),
    )


def downgrade():
    op.drop_table("social_account")
