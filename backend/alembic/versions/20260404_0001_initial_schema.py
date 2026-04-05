"""initial production schema

Revision ID: 20260404_0001
Revises:
Create Date: 2026-04-04 02:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("session_version", sa.Integer(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'staff_scheduler', 'viewer')", name="user_role_check"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_active"), "users", ["active"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("subject_tags", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teachers")),
        sa.UniqueConstraint("email", name=op.f("uq_teachers_email")),
    )
    op.create_index(op.f("ix_teachers_active"), "teachers", ["active"], unique=False)
    op.create_index(op.f("ix_teachers_full_name"), "teachers", ["full_name"], unique=False)

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("parent_name", sa.String(length=255), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_students")),
        sa.UniqueConstraint("contact_email", name=op.f("uq_students_contact_email")),
    )
    op.create_index(op.f("ix_students_active"), "students", ["active"], unique=False)
    op.create_index(op.f("ix_students_full_name"), "students", ["full_name"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL", name=op.f("fk_audit_logs_actor_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    for index in ["actor_user_id", "actor_email", "action", "entity_type", "entity_id", "outcome"]:
        op.create_index(op.f(f"ix_audit_logs_{index}"), "audit_logs", [index], unique=False)

    op.create_table(
        "availability_slots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("end_minute", sa.Integer(), nullable=False),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="availability_weekday_range"),
        sa.CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="availability_minute_range"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE", name=op.f("fk_availability_slots_teacher_id_teachers")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_availability_slots")),
        sa.UniqueConstraint("teacher_id", "weekday", "start_minute", "end_minute", name="uq_availability_slot"),
    )
    op.create_index(op.f("ix_availability_slots_teacher_id"), "availability_slots", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_availability_slots_weekday"), "availability_slots", ["weekday"], unique=False)

    op.create_table(
        "student_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("end_minute", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="student_preference_weekday_range"),
        sa.CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="student_preference_minute_range"),
        sa.CheckConstraint("priority >= 1 AND priority <= 5", name="student_preference_priority_range"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE", name=op.f("fk_student_preferences_student_id_students")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_student_preferences")),
        sa.UniqueConstraint("student_id", "weekday", "start_minute", "end_minute", name="uq_student_preference"),
    )
    op.create_index(op.f("ix_student_preferences_student_id"), "student_preferences", ["student_id"], unique=False)
    op.create_index(op.f("ix_student_preferences_weekday"), "student_preferences", ["weekday"], unique=False)

    op.create_table(
        "student_blocked_times",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("end_minute", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="student_blocked_weekday_range"),
        sa.CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="student_blocked_minute_range"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE", name=op.f("fk_student_blocked_times_student_id_students")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_student_blocked_times")),
        sa.UniqueConstraint("student_id", "weekday", "start_minute", "end_minute", name="uq_student_blocked_time"),
    )
    op.create_index(op.f("ix_student_blocked_times_student_id"), "student_blocked_times", ["student_id"], unique=False)
    op.create_index(op.f("ix_student_blocked_times_weekday"), "student_blocked_times", ["weekday"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("end_minute", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="session_weekday_range"),
        sa.CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="session_minute_range"),
        sa.CheckConstraint("duration_minutes = end_minute - start_minute", name="session_duration_matches_range"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="session_status_check"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL", name=op.f("fk_sessions_created_by_user_id_users")),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name=op.f("fk_sessions_student_id_students")),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="RESTRICT", name=op.f("fk_sessions_teacher_id_teachers")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("teacher_id", "student_id", "weekday", "start_minute", "end_minute", "start_date", name="uq_session_template"),
    )
    for index in ["teacher_id", "student_id", "weekday", "subject", "status", "start_date", "end_date"]:
        op.create_index(op.f(f"ix_sessions_{index}"), "sessions", [index], unique=False)

    op.create_table(
        "session_occurrence_exceptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("occurrence_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rescheduled_date", sa.Date(), nullable=True),
        sa.Column("rescheduled_start_minute", sa.Integer(), nullable=True),
        sa.Column("rescheduled_end_minute", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('cancelled', 'completed', 'rescheduled', 'missed', 'holiday_affected')", name="occurrence_exception_status_check"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL", name=op.f("fk_session_occurrence_exceptions_changed_by_user_id_users")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE", name=op.f("fk_session_occurrence_exceptions_session_id_sessions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_occurrence_exceptions")),
        sa.UniqueConstraint("session_id", "occurrence_date", name="uq_session_occurrence_exception"),
    )
    for index in ["session_id", "occurrence_date", "status", "rescheduled_date"]:
        op.create_index(op.f(f"ix_session_occurrence_exceptions_{index}"), "session_occurrence_exceptions", [index], unique=False)

    op.create_table(
        "centre_closures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("closure_type", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("closure_type IN ('holiday', 'closure')", name="centre_closure_type_check"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_centre_closures")),
    )
    op.create_index(op.f("ix_centre_closures_closure_type"), "centre_closures", ["closure_type"], unique=False)
    op.create_index(op.f("ix_centre_closures_start_date"), "centre_closures", ["start_date"], unique=False)
    op.create_index(op.f("ix_centre_closures_end_date"), "centre_closures", ["end_date"], unique=False)

    op.create_table(
        "teacher_leave_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=True),
        sa.Column("end_minute", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE", name=op.f("fk_teacher_leave_blocks_teacher_id_teachers")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teacher_leave_blocks")),
    )
    for index in ["teacher_id", "start_date", "end_date"]:
        op.create_index(op.f(f"ix_teacher_leave_blocks_{index}"), "teacher_leave_blocks", [index], unique=False)

    op.create_table(
        "student_absence_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=True),
        sa.Column("end_minute", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE", name=op.f("fk_student_absence_blocks_student_id_students")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_student_absence_blocks")),
    )
    for index in ["student_id", "start_date", "end_date"]:
        op.create_index(op.f(f"ix_student_absence_blocks_{index}"), "student_absence_blocks", [index], unique=False)

    op.create_table(
        "calendar_feed_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_type", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL", name=op.f("fk_calendar_feed_tokens_created_by_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_calendar_feed_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_calendar_feed_tokens_token_hash")),
    )
    op.create_index(op.f("ix_calendar_feed_tokens_owner_type"), "calendar_feed_tokens", ["owner_type"], unique=False)
    op.create_index(op.f("ix_calendar_feed_tokens_owner_id"), "calendar_feed_tokens", ["owner_id"], unique=False)
    op.create_index(op.f("ix_calendar_feed_tokens_active"), "calendar_feed_tokens", ["active"], unique=False)


def downgrade() -> None:
    for table, columns in [
        ("calendar_feed_tokens", ["active", "owner_id", "owner_type"]),
        ("student_absence_blocks", ["end_date", "start_date", "student_id"]),
        ("teacher_leave_blocks", ["end_date", "start_date", "teacher_id"]),
        ("centre_closures", ["end_date", "start_date", "closure_type"]),
        ("session_occurrence_exceptions", ["rescheduled_date", "status", "occurrence_date", "session_id"]),
        ("sessions", ["end_date", "start_date", "status", "subject", "weekday", "student_id", "teacher_id"]),
        ("student_blocked_times", ["weekday", "student_id"]),
        ("student_preferences", ["weekday", "student_id"]),
        ("availability_slots", ["weekday", "teacher_id"]),
        ("audit_logs", ["outcome", "entity_id", "entity_type", "action", "actor_email", "actor_user_id"]),
        ("students", ["full_name", "active"]),
        ("teachers", ["full_name", "active"]),
        ("users", ["role", "email", "active"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)

    op.drop_table("calendar_feed_tokens")
    op.drop_table("student_absence_blocks")
    op.drop_table("teacher_leave_blocks")
    op.drop_table("centre_closures")
    op.drop_table("session_occurrence_exceptions")
    op.drop_table("sessions")
    op.drop_table("student_blocked_times")
    op.drop_table("student_preferences")
    op.drop_table("availability_slots")
    op.drop_table("audit_logs")
    op.drop_table("students")
    op.drop_table("teachers")
    op.drop_table("users")
