"""Create initial database schema

Revision ID: f7f8002f0734
Revises:
Create Date: 2026-07-08 23:47:18.221893

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7f8002f0734"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "samples",
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(), nullable=False),
        sa.Column("object_name", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_samples")),
        sa.UniqueConstraint("sha256", name=op.f("uq_samples_sha256")),
    )
    op.create_table(
        "users",
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("role", sa.Enum("USER", "ADMIN", name="role"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(
        op.f("ix_users_username"),
        "users",
        [sa.literal_column("lower(username)")],
        unique=True,
    )
    op.create_table(
        "jobs",
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", name="status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["sample_id"],
            ["samples.id"],
            name=op.f("fk_jobs_sample_id_samples"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
    )
    op.create_index(op.f("ix_jobs_sample_id"), "jobs", ["sample_id"], unique=False)
    op.create_index(
        op.f("ix_jobs_sample_id_engine_version_status"),
        "jobs",
        ["sample_id", "engine_version", "status"],
        unique=False,
    )
    op.create_table(
        "job_tasks",
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column(
            "task_type",
            sa.Enum("STATIC", "SANDBOX", "ML", name="task_type"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", name="status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_job_tasks_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_tasks")),
    )
    op.create_index(op.f("ix_job_tasks_job_id"), "job_tasks", ["job_id"], unique=False)
    op.create_table(
        "user_samples",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("current_job_id", sa.Integer(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["current_job_id"],
            ["jobs.id"],
            name=op.f("fk_user_samples_current_job_id_jobs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["sample_id"],
            ["samples.id"],
            name=op.f("fk_user_samples_sample_id_samples"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_samples_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_samples")),
        sa.UniqueConstraint(
            "user_id",
            "sample_id",
            name=op.f("uq_user_samples_user_id_sample_id"),
        ),
    )
    op.create_table(
        "user_sample_jobs",
        sa.Column("user_sample_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column(
            "pinned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_user_sample_jobs_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_sample_id"],
            ["user_samples.id"],
            name=op.f("fk_user_sample_jobs_user_sample_id_user_samples"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_sample_jobs")),
        sa.UniqueConstraint(
            "user_sample_id",
            "job_id",
            name=op.f("uq_user_sample_jobs_user_sample_id_job_id"),
        ),
    )
    op.create_index(
        op.f("ix_user_sample_jobs_user_sample_id"),
        "user_sample_jobs",
        ["user_sample_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_user_sample_jobs_user_sample_id"),
        table_name="user_sample_jobs",
    )
    op.drop_table("user_sample_jobs")
    op.drop_table("user_samples")
    op.drop_index(op.f("ix_job_tasks_job_id"), table_name="job_tasks")
    op.drop_table("job_tasks")
    op.drop_index(op.f("ix_jobs_sample_id_engine_version_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_sample_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
    op.drop_table("samples")
