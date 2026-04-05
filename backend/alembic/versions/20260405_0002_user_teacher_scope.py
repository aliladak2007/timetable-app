"""add teacher linkage for scoped users

Revision ID: 20260405_0002
Revises: 20260404_0001
Create Date: 2026-04-05 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0002"
down_revision = "20260404_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("linked_teacher_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_users_linked_teacher_id"), "users", ["linked_teacher_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_users_linked_teacher_id_teachers"),
        "users",
        "teachers",
        ["linked_teacher_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_users_linked_teacher_id_teachers"), "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_linked_teacher_id"), table_name="users")
    op.drop_column("users", "linked_teacher_id")
