"""updated prestador

Revision ID: 8d0f575e5df5
Revises: f02368db0683
Create Date: 2023-09-11 15:32:33.618566

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d0f575e5df5'
down_revision = 'f02368db0683'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Prestador', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_server_update', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Prestador', schema=None) as batch_op:
        batch_op.drop_column('last_server_update')

    # ### end Alembic commands ###
