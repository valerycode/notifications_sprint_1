"""partition user_actions

Revision ID: f78ec4dde70c
Revises: 524c15620232
Create Date: 2023-01-23 20:30:29.625477

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f78ec4dde70c"
down_revision = "524c15620232"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_actions_new (
            id uuid NOT NULL,
            user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            device_name VARCHAR (255),
            action_type VARCHAR (255),
            action_time timestamp with time zone,
            PRIMARY KEY (id, user_id)
        ) PARTITION BY HASH (user_id); 
        """
    )
    op.execute("""CREATE TABLE user_actions_0 PARTITION OF user_actions_new FOR VALUES WITH (MODULUS 3,REMAINDER 0)""")
    op.execute("""CREATE TABLE user_actions_1 PARTITION OF user_actions_new FOR VALUES WITH (MODULUS 3,REMAINDER 1)""")
    op.execute("""CREATE TABLE user_actions_2 PARTITION OF user_actions_new FOR VALUES WITH (MODULUS 3,REMAINDER 2)""")
    op.execute("""INSERT INTO user_actions_new SELECT * FROM user_actions""")
    op.drop_table("user_actions")
    op.rename_table("user_actions_new", "user_actions")


def downgrade():
    op.create_table(
        "user_actions_old",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column("action_type", sa.String(255), nullable=True),
        sa.Column("action_time", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.execute("""INSERT INTO user_actions_old SELECT * FROM user_actions""")
    op.drop_table("user_actions")
    op.rename_table("user_actions_old", "user_actions")
