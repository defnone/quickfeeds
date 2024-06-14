"""Remove last_clean

Revision ID: 115d3c7b5769
Revises: 0e3c1de12e4a
Create Date: 2024-06-14 15:02:20.884764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '115d3c7b5769'
down_revision = '0e3c1de12e4a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_clean')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_clean', sa.DATETIME(), nullable=True))

    # ### end Alembic commands ###
