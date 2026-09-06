from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from backend.app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    github_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    github_account: Mapped[Optional[GitHubAccount]] = relationship(
        "GitHubAccount",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    contributions: Mapped[List[Contribution]] = relationship(
        "Contribution",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class GitHubAccount(Base):
    __tablename__ = "github_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    access_token_encrypted: Mapped[str] = mapped_column(String(2048))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user: Mapped[User] = relationship("User", back_populates="github_account")

class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    github_repo_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    html_url: Mapped[str] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stargazers_count: Mapped[int] = mapped_column(Integer, default=0)
    forks_count: Mapped[int] = mapped_column(Integer, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    issues: Mapped[List[Issue]] = relationship(
        "Issue",
        back_populates="repository",
        cascade="all, delete-orphan"
    )
    opportunities: Mapped[List[Opportunity]] = relationship(
        "Opportunity",
        back_populates="repository",
        cascade="all, delete-orphan"
    )
    contributions: Mapped[List[Contribution]] = relationship(
        "Contribution",
        back_populates="repository",
        cascade="all, delete-orphan"
    )
    indexes: Mapped[List[RepositoryIndex]] = relationship(
        "RepositoryIndex",
        back_populates="repository",
        cascade="all, delete-orphan"
    )

class RepositoryIndex(Base):
    __tablename__ = "repository_indexes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True
    )
    branch: Mapped[str] = mapped_column(String(100))
    commit_sha: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, in_progress, completed, failed
    error_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    repository: Mapped[Repository] = relationship("Repository", back_populates="indexes")
    files: Mapped[List[RepositoryFile]] = relationship(
        "RepositoryFile",
        back_populates="repository_index",
        cascade="all, delete-orphan"
    )

class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    repository_index_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_indexes.id", ondelete="CASCADE"),
        index=True
    )
    path: Mapped[str] = mapped_column(String(1024), index=True)
    size_kb: Mapped[float] = mapped_column(Float, default=0.0)
    content_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    repository_index: Mapped[RepositoryIndex] = relationship("RepositoryIndex", back_populates="files")
    symbols: Mapped[List[RepositorySymbol]] = relationship(
        "RepositorySymbol",
        back_populates="repository_file",
        cascade="all, delete-orphan"
    )

class RepositorySymbol(Base):
    __tablename__ = "repository_symbols"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    repository_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_files.id", ondelete="CASCADE"),
        index=True
    )
    name: Mapped[str] = mapped_column(String(512), index=True)
    type: Mapped[str] = mapped_column(String(100)) # class, function, method, interface, etc.
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    start_column: Mapped[int] = mapped_column(Integer)
    end_column: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    repository_file: Mapped[RepositoryFile] = relationship("RepositoryFile", back_populates="symbols")

class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    github_issue_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True
    )
    number: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(512))
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    labels: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    state: Mapped[str] = mapped_column(String(50)) # open, closed
    author: Mapped[str] = mapped_column(String(255))
    html_url: Mapped[str] = mapped_column(String(1024))
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    repository: Mapped[Repository] = relationship("Repository", back_populates="issues")
    opportunities: Mapped[List[Opportunity]] = relationship(
        "Opportunity",
        back_populates="issue",
        cascade="all, delete-orphan"
    )

class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True
    )
    issue_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(100)) # bug, feature, refactor, documentation, etc.
    impact: Mapped[str] = mapped_column(String(50)) # low, medium, high
    difficulty: Mapped[str] = mapped_column(String(50)) # easy, intermediate, hard
    reproducibility: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duplicate_risk: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    scoring_reasoning: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    repository: Mapped[Repository] = relationship("Repository", back_populates="opportunities")
    issue: Mapped[Optional[Issue]] = relationship("Issue", back_populates="opportunities")
    contributions: Mapped[List[Contribution]] = relationship(
        "Contribution",
        back_populates="opportunity",
        cascade="all, delete-orphan"
    )

class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="started") # started, in_progress, pull_request_created, merged, failed
    branch_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user: Mapped[User] = relationship("User", back_populates="contributions")
    repository: Mapped[Repository] = relationship("Repository", back_populates="contributions")
    opportunity: Mapped[Opportunity] = relationship("Opportunity", back_populates="contributions")
    agent_runs: Mapped[List[AgentRun]] = relationship(
        "AgentRun",
        back_populates="contribution",
        cascade="all, delete-orphan"
    )
    test_runs: Mapped[List[TestRun]] = relationship(
        "TestRun",
        back_populates="contribution",
        cascade="all, delete-orphan"
    )
    code_reviews: Mapped[List[CodeReview]] = relationship(
        "CodeReview",
        back_populates="contribution",
        cascade="all, delete-orphan"
    )
    solution_plan: Mapped[Optional[SolutionPlan]] = relationship(
        "SolutionPlan",
        back_populates="contribution",
        uselist=False,
        cascade="all, delete-orphan"
    )

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contributions.id", ondelete="CASCADE"),
        index=True
    )
    agent_type: Mapped[str] = mapped_column(String(100)) # coder, reviewer, documentation, etc.
    status: Mapped[str] = mapped_column(String(50), default="queued") # pending, running, completed, failed
    current_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    error_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    contribution: Mapped[Contribution] = relationship("Contribution", back_populates="agent_runs")
    events: Mapped[List[AgentEvent]] = relationship(
        "AgentEvent",
        back_populates="agent_run",
        cascade="all, delete-orphan"
    )

class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        index=True
    )
    event_type: Mapped[str] = mapped_column(String(100)) # log, action, tool_use, thought, error, etc.
    message: Mapped[str] = mapped_column(Text)
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    agent_run: Mapped[AgentRun] = relationship("AgentRun", back_populates="events")

class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contributions.id", ondelete="CASCADE"),
        index=True
    )
    command: Mapped[str] = mapped_column(String(1024))
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50)) # success, failure, error, etc.

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    contribution: Mapped[Contribution] = relationship("Contribution", back_populates="test_runs")

class CodeReview(Base):
    __tablename__ = "code_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contributions.id", ondelete="CASCADE"),
        index=True
    )
    decision: Mapped[str] = mapped_column(String(50)) # approve, request_changes, comment
    summary: Mapped[str] = mapped_column(Text)
    review_issues: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(String(50)) # low, medium, high, critical
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    contribution: Mapped[Contribution] = relationship("Contribution", back_populates="code_reviews")

class SolutionPlan(Base):
    __tablename__ = "solution_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    contribution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contributions.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )

    problem: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text)
    relevant_files: Mapped[List[str]] = mapped_column(JSON)
    relevant_symbols: Mapped[List[str]] = mapped_column(JSON)
    implementation_steps: Mapped[List[str]] = mapped_column(JSON)
    testing_strategy: Mapped[str] = mapped_column(Text)
    risks: Mapped[str] = mapped_column(Text)
    expected_diff_size: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, approved, rejected

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    contribution: Mapped[Contribution] = relationship("Contribution", back_populates="solution_plan")

class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(255), index=True)
    task: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    duration: Mapped[float] = mapped_column(Float) # in seconds

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(50)) # success, failed
    error_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
