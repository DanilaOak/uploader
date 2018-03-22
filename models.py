import sqlalchemy as sa
from sqlalchemy import func

User = sa.Table(
    'user',
    sa.MetaData(),
    sa.Column('user_id', sa.Integer, primary_key=True),
)

File = sa.Table(
    'file',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False),
    sa.Column('name', sa.String, nullable=False),
    sa.Column('path', sa.String, nullable=False, unique=True),
    sa.Column('size', sa.BigInteger, nullable=False),
    sa.Column('creation_date', sa.DateTime, server_default=func.now())
)

_models = {'user': User, 'file': File}


def get_model_by_name(name: str) -> sa.Table:
    return _models.get(name, None)
