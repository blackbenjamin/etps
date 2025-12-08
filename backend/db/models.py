"""
ETPS Database Models

SQLAlchemy ORM models for the Enhanced Talent Positioning System.
Phase 1-2: Core entities for resume generation and job application tracking.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    Date,
    ForeignKey,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class User(Base):
    """
    User account in the ETPS system.

    Each user has their own set of resume templates, experiences, bullets,
    and job applications. The candidate_profile JSON field contains:
    - primary_identity, specializations, target_roles
    - linkedin_meta (headline, about, top_skills, open_to_work_titles)
    - ai_portfolio (projects with tech_stack, fs_relevance, etc.)
    - ai_systems_builder flag
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    location: Mapped[Optional[str]] = mapped_column(String(255))

    # Candidate profile (v1.3.0) - JSON containing specializations, target_roles, linkedin_meta, ai_portfolio
    candidate_profile: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    templates: Mapped[List["Template"]] = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    experiences: Mapped[List["Experience"]] = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    bullets: Mapped[List["Bullet"]] = relationship("Bullet", back_populates="user", cascade="all, delete-orphan")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    log_entries: Mapped[List["LogEntry"]] = relationship("LogEntry", back_populates="user", cascade="all, delete-orphan")
    job_profiles: Mapped[List["JobProfile"]] = relationship("JobProfile", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Template(Base):
    """
    Resume template (DOCX file) used for generating tailored resumes.

    Templates contain placeholders that are filled with selected experiences
    and bullets based on job matching.
    """
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    docx_path: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="templates")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="template")

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class Experience(Base):
    """
    Work experience entry (job role) on a resume.

    Core metadata (title, employer, location) is immutable to maintain consistency
    across resume versions. For consulting roles, contains engagements with clients.
    Non-consulting roles have bullets directly attached.

    v1.3.0 additions:
    - employer_type: independent_consulting, full_time, contract
    - role_summary: brief description of the role
    - ai_systems_built, governance_frameworks_created: for AI-focused roles
    - fs_domain_relevance: financial services relevance score
    - tools_and_technologies: tech stack used in role
    """
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)  # immutable
    employer_name: Mapped[str] = mapped_column(String(255), nullable=False)  # immutable
    location: Mapped[Optional[str]] = mapped_column(String(255))  # immutable
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)  # null = current position
    description: Mapped[Optional[str]] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # for sorting

    # v1.3.0 fields
    employer_type: Mapped[Optional[str]] = mapped_column(String(50))  # independent_consulting, full_time, contract
    role_summary: Mapped[Optional[str]] = mapped_column(Text)  # brief role description
    ai_systems_built: Mapped[Optional[List[str]]] = mapped_column(JSON)  # e.g., ["ETPS", "RAG systems"]
    governance_frameworks_created: Mapped[Optional[List[str]]] = mapped_column(JSON)
    fs_domain_relevance: Mapped[Optional[float]] = mapped_column(Float)  # 0.0-1.0
    tools_and_technologies: Mapped[Optional[List[str]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="experiences")
    engagements: Mapped[List["Engagement"]] = relationship("Engagement", back_populates="experience", cascade="all, delete-orphan")
    bullets: Mapped[List["Bullet"]] = relationship("Bullet", back_populates="experience", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Experience(id={self.id}, job_title='{self.job_title}', employer='{self.employer_name}')>"


class Engagement(Base):
    """
    Client engagement within a consulting role (v1.3.0).

    Represents work done for a specific client within a consulting period.
    Contains its own bullets describing the engagement work.
    For non-consulting roles, engagements are not used (bullets attach directly to experience).
    """
    __tablename__ = "engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experience_id: Mapped[int] = mapped_column(Integer, ForeignKey("experiences.id"), nullable=False, index=True)
    client: Mapped[Optional[str]] = mapped_column(String(255))  # null for internal/non-client work
    project_name: Mapped[Optional[str]] = mapped_column(String(500))  # e.g., "Enterprise Data Strategy & Governance"
    project_type: Mapped[Optional[str]] = mapped_column(String(100))  # advisory, product_build, implementation
    date_range_label: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "2023", "Q1 2024"
    domain_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)  # e.g., ["AI Strategy", "Data Governance"]
    tech_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)  # e.g., ["Python", "Azure"]
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # for sorting within experience
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    experience: Mapped["Experience"] = relationship("Experience", back_populates="engagements")
    bullets: Mapped[List["Bullet"]] = relationship("Bullet", back_populates="engagement", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Engagement(id={self.id}, client='{self.client}', project='{self.project_name}')>"


class Bullet(Base):
    """
    Individual bullet point describing an achievement or responsibility.

    Bullets are tagged and embedded for semantic matching to job requirements.
    Tracks usage statistics and maintains version history for optimization.

    v1.3.0: Bullets can belong to either:
    - An experience directly (non-consulting roles)
    - An engagement within an experience (consulting roles)
    """
    __tablename__ = "bullets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    experience_id: Mapped[int] = mapped_column(Integer, ForeignKey("experiences.id"), nullable=False, index=True)
    engagement_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("engagements.id"), index=True)  # v1.3.0: nullable for non-consulting

    text: Mapped[str] = mapped_column(Text, nullable=False)  # canonical text
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)  # e.g., ["ai_governance", "consulting"]
    seniority_level: Mapped[Optional[str]] = mapped_column(String(50))  # "director", "senior_ic"
    bullet_type: Mapped[Optional[str]] = mapped_column(String(50))  # "achievement", "responsibility", "metric_impact"
    relevance_scores: Mapped[Optional[dict]] = mapped_column(JSON)  # {"ai_governance": 0.85, "consulting": 0.70}
    star_notes: Mapped[Optional[str]] = mapped_column(Text)  # STAR method notes
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    retired: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version_history: Mapped[Optional[dict]] = mapped_column(JSON)  # list of variants
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)  # vector for semantic search

    # v1.3.0 fields
    importance: Mapped[Optional[str]] = mapped_column(String(20))  # high, medium, low
    ai_first_choice: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # prioritize for AI roles
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # for sorting within engagement/experience

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bullets")
    experience: Mapped["Experience"] = relationship("Experience", back_populates="bullets")
    engagement: Mapped[Optional["Engagement"]] = relationship("Engagement", back_populates="bullets")

    # Index for semantic search and filtering
    __table_args__ = (
        Index("ix_bullets_tags", "tags"),
        Index("ix_bullets_retired", "retired"),
        Index("ix_bullets_engagement", "engagement_id"),
    )

    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"<Bullet(id={self.id}, experience_id={self.experience_id}, text='{text_preview}')>"


class CompanyProfile(Base):
    """
    Company profile with business context and AI/data maturity signals.

    Enriched with culture signals and known initiatives to tailor
    application materials and positioning.
    """
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    size_band: Mapped[Optional[str]] = mapped_column(String(50))  # "50-200", "1000-5000"
    headquarters: Mapped[Optional[str]] = mapped_column(String(255))
    business_lines: Mapped[Optional[str]] = mapped_column(Text)
    known_initiatives: Mapped[Optional[str]] = mapped_column(Text)
    culture_signals: Mapped[Optional[List[str]]] = mapped_column(JSON)  # e.g., ["formal", "mission-driven"]
    data_ai_maturity: Mapped[Optional[str]] = mapped_column(String(50))  # "low", "developing", "advanced"
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)  # vector for similarity search
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    job_profiles: Mapped[List["JobProfile"]] = relationship("JobProfile", back_populates="company")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="company")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="company")

    def __repr__(self) -> str:
        return f"<CompanyProfile(id={self.id}, name='{self.name}', industry='{self.industry}')>"


class JobProfile(Base):
    """
    Parsed and analyzed job description with skill extraction and gap analysis.

    Contains both raw JD text and structured extracted information for
    intelligent bullet selection and resume tailoring.
    """
    __tablename__ = "job_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("company_profiles.id"), index=True)
    raw_jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    jd_url: Mapped[Optional[str]] = mapped_column(String(1000))
    job_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # Extracted company name from JD text
    location: Mapped[Optional[str]] = mapped_column(String(255))
    seniority: Mapped[Optional[str]] = mapped_column(String(100))
    responsibilities: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    nice_to_haves: Mapped[Optional[str]] = mapped_column(Text)
    extracted_skills: Mapped[Optional[List[str]]] = mapped_column(JSON)  # e.g., ["Python", "AI Governance"]
    core_priorities: Mapped[Optional[List[str]]] = mapped_column(JSON)  # LLM-distilled priorities
    must_have_capabilities: Mapped[Optional[List[str]]] = mapped_column(JSON)
    nice_to_have_capabilities: Mapped[Optional[List[str]]] = mapped_column(JSON)
    skill_gap_analysis: Mapped[Optional[dict]] = mapped_column(JSON)  # {matched_skills:[], missing_skills:[], positioning_strategies:[]}
    tone_style: Mapped[Optional[str]] = mapped_column(String(50))
    job_type_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)  # e.g., ["ai_governance", "consulting"]
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)  # vector for similarity search

    # User-curated skill selections (Sprint 10E)
    selected_skills: Mapped[Optional[List[dict]]] = mapped_column(
        JSON,
        nullable=True,
        comment="User-ordered list of skills: [{skill: str, match_pct: float, included: bool, order: int}]"
    )
    key_skills: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="3-4 skills to emphasize in cover letter (max 4)"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_profiles")
    company: Mapped[Optional["CompanyProfile"]] = relationship("CompanyProfile", back_populates="job_profiles")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="job_profile")

    def __repr__(self) -> str:
        return f"<JobProfile(id={self.id}, job_title='{self.job_title}', company_id={self.company_id})>"


class Application(Base):
    """
    Job application tracking with generated materials and quality scores.

    Links together job profile, company, template, and generated resume/cover letter.
    Tracks application status through the hiring pipeline.
    """
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_profiles.id"), nullable=False, index=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("company_profiles.id"), index=True)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("templates.id"))
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)  # draft/applied/screening/interviewing/offer/rejected/withdrawn
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resume_path: Mapped[Optional[str]] = mapped_column(String(500))
    cover_letter_path: Mapped[Optional[str]] = mapped_column(String(500))
    resume_json: Mapped[Optional[dict]] = mapped_column(JSON)  # structured resume data
    cover_letter_json: Mapped[Optional[dict]] = mapped_column(JSON)  # structured cover letter data
    ats_score: Mapped[Optional[float]] = mapped_column(Float)
    critic_scores: Mapped[Optional[dict]] = mapped_column(JSON)  # {relevance: 0.9, clarity: 0.85, ...}
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    job_profile: Mapped["JobProfile"] = relationship("JobProfile", back_populates="applications")
    company: Mapped[Optional["CompanyProfile"]] = relationship("CompanyProfile", back_populates="applications")
    template: Mapped[Optional["Template"]] = relationship("Template", back_populates="applications")
    log_entries: Mapped[List["LogEntry"]] = relationship("LogEntry", back_populates="application", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, job_profile_id={self.job_profile_id}, status='{self.status}')>"


class Contact(Base):
    """
    Professional contact with relationship strength and role compatibility.

    Used for network-based job search: identifying hiring managers,
    referral opportunities, and warm introduction paths.

    This is the authoritative PII store for contact information.
    Personal identifiers are sanitized before being used in prompts/logs.
    """
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("company_profiles.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    relationship_type: Mapped[Optional[str]] = mapped_column(String(50))  # shared_school/shared_employer/alumni/2nd_degree/former_colleague
    relationship_strength: Mapped[Optional[float]] = mapped_column(Float)  # 0.0-1.0
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)
    role_compatibility_score: Mapped[Optional[float]] = mapped_column(Float)
    shared_connections: Mapped[Optional[dict]] = mapped_column(JSON)
    shared_schools: Mapped[Optional[dict]] = mapped_column(JSON)
    shared_employers: Mapped[Optional[dict]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_hiring_manager_candidate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hiring_manager_confidence: Mapped[Optional[float]] = mapped_column(Float)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)  # Soft deletion for GDPR compliance
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="contacts")
    company: Mapped[Optional["CompanyProfile"]] = relationship("CompanyProfile", back_populates="contacts")

    # Indexes for contact search and filtering
    __table_args__ = (
        Index("ix_contacts_company_hiring", "company_id", "is_hiring_manager_candidate"),
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, full_name='{self.full_name}', company_id={self.company_id})>"


class LogEntry(Base):
    """
    System audit log for tracking generations, evaluations, and errors.

    Provides observability into AI agent actions, quality scores,
    and system performance for debugging and optimization.
    """
    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    application_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("applications.id"), index=True)
    log_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # critic_evaluation/ats_score/generation/error/revision
    level: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # debug/info/warning/error
    message: Mapped[str] = mapped_column(Text, nullable=False)
    log_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # flexible JSON for context
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="log_entries")
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="log_entries")

    # Composite index for efficient log querying
    __table_args__ = (
        Index("ix_log_entries_type_level", "log_type", "level"),
    )

    def __repr__(self) -> str:
        return f"<LogEntry(id={self.id}, log_type='{self.log_type}', level='{self.level}', created_at={self.created_at})>"


class CriticLog(Base):
    """
    Critic evaluation log for cover letter generation iterations.

    Stores the full history of critic evaluations for each cover letter
    generation session, enabling analysis of improvement patterns and
    debugging of the iteration loop.
    """
    __tablename__ = "critic_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_profiles.id"), nullable=False, index=True)
    application_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("applications.id"), index=True)

    # Session tracking
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)  # UUID for grouping iterations
    iteration: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-indexed iteration number
    total_iterations: Mapped[int] = mapped_column(Integer, nullable=False)  # Total iterations in session

    # Evaluation results
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    should_retry: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Issue summary
    issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    major_issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Detailed data (JSON)
    issues: Mapped[Optional[List[dict]]] = mapped_column(JSON)  # List of CriticIssue dicts
    improvement_suggestions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    retry_reasons: Mapped[Optional[List[str]]] = mapped_column(JSON)

    # Score components
    banned_phrase_violations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tone_compliance_score: Mapped[Optional[float]] = mapped_column(Float)
    ats_coverage_percentage: Mapped[Optional[float]] = mapped_column(Float)

    # Delta tracking
    score_delta: Mapped[Optional[float]] = mapped_column(Float)  # Change from previous iteration
    issues_resolved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Draft content (optional, for debugging)
    draft_text: Mapped[Optional[str]] = mapped_column(Text)  # Can be null to save space

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_critic_logs_session", "session_id", "iteration"),
        Index("ix_critic_logs_user_job", "user_id", "job_profile_id"),
        Index("ix_critic_logs_quality", "quality_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<CriticLog(id={self.id}, session_id='{self.session_id[:8]}...', "
            f"iteration={self.iteration}/{self.total_iterations}, score={self.quality_score:.1f})>"
        )


class ApprovedOutput(Base):
    """
    Approved output stored for learning and reference.

    Stores user-approved generations (bullets, paragraphs, summaries)
    with embeddings for semantic retrieval. Used to guide future
    generation by providing successful examples.
    """
    __tablename__ = "approved_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    application_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("applications.id"), index=True)
    job_profile_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_profiles.id"), index=True)

    # Output content
    output_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'resume_bullet', 'cover_letter_paragraph', 'professional_summary', 'full_resume', 'full_cover_letter'
    original_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata and scoring
    context_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # {job_title, requirements_snippet, tags, seniority}
    quality_score: Mapped[Optional[float]] = mapped_column(Float)  # 0.0-1.0, from critic or manual

    # Vector embedding for similarity search
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", backref="approved_outputs")
    application: Mapped[Optional["Application"]] = relationship("Application", backref="approved_outputs")
    job_profile: Mapped[Optional["JobProfile"]] = relationship("JobProfile", backref="approved_outputs")

    # Indexes
    __table_args__ = (
        Index("ix_approved_outputs_user_type", "user_id", "output_type"),
        Index("ix_approved_outputs_quality", "quality_score"),
    )

    def __repr__(self) -> str:
        return f"<ApprovedOutput(id={self.id}, type='{self.output_type}', quality={self.quality_score})>"
