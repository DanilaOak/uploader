"""create user and files tables

Revision ID: 3fae2f91a0f6
Revises: 
Create Date: 2018-03-22 19:42:43.245775

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import func


# revision identifiers, used by Alembic.
revision = '3fae2f91a0f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('user_id', sa.Integer, primary_key=True),
    )

    op.create_table(
        'file',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('path', sa.String, nullable=False, unique=True),
        sa.Column('size', sa.BigInteger, nullable=False),
        sa.Column('creation_date', sa.DateTime, server_default=func.now())
    )


def downgrade():
    op.drop_table('user')
    op.drop_table('file ')
