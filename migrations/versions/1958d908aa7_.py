"""empty message

Revision ID: 1958d908aa7
Revises: 5a34622b52a
Create Date: 2015-02-25 11:09:16.724433

"""

# revision identifiers, used by Alembic.
revision = '1958d908aa7'
down_revision = '5a34622b52a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'body_html')
    ### end Alembic commands ###
