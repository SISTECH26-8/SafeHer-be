"""Add trips table

Revision ID: 8c8117b6c136
Revises: 121336d408fe
Create Date: 2026-08-02 20:35:46.127972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c8117b6c136'
down_revision: Union[str, None] = '121336d408fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
