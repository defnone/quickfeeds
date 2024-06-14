"""Rename clean_interval to clean_after_days

Revision ID: 0e3c1de12e4a
Revises: 6df7fc38cb49
Create Date: 2024-06-14 09:20:53.005173

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0e3c1de12e4a"
down_revision = "6df7fc38cb49"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("settings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "clean_after_days",
                sa.Integer(),
                nullable=False,
                server_default="30",
            )
        )
        batch_op.drop_column("clean_interval")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("settings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "clean_interval",
                sa.INTEGER(),
                server_default=sa.text("'30'"),
                nullable=False,
            )
        )
        batch_op.drop_column("clean_after_days")

    # ### end Alembic commands ###
