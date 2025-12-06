"""
ETPS Pydantic Schemas

Request and response models for API endpoints.
"""

from .job_parser import (
    JobParseRequest,
    JobParseResponse,
    JobProfileDTO
)
from .skill_gap import (
    UserSkillProfile,
    SkillMatch,
    SkillGap,
    WeakSignal,
    SkillGapRequest,
    SkillGapResponse
)
from .resume_tailor import (
    TailorResumeRequest,
    SelectedBullet,
    SelectedRole,
    SelectedSkill,
    TailoringRationale,
    TailoredResume,
    EducationEntry,
    ResumeDocxRequest
)
from .cover_letter import (
    CoverLetterRequest,
    CoverLetterOutline,
    BannedPhraseViolation,
    BannedPhraseCheck,
    ToneComplianceResult,
    ATSKeywordCoverage,
    CoverLetterRationale,
    GeneratedCoverLetter
)
from .critic import (
    CriticEvaluateRequest,
    CriticIssue,
    ATSScoreBreakdown,
    StructureCheckResult,
    CriticResult
)

__all__ = [
    # Job parser schemas
    'JobParseRequest',
    'JobParseResponse',
    'JobProfileDTO',
    # Skill gap schemas
    'UserSkillProfile',
    'SkillMatch',
    'SkillGap',
    'WeakSignal',
    'SkillGapRequest',
    'SkillGapResponse',
    # Resume tailoring schemas
    'TailorResumeRequest',
    'SelectedBullet',
    'SelectedRole',
    'SelectedSkill',
    'TailoringRationale',
    'TailoredResume',
    'EducationEntry',
    'ResumeDocxRequest',
    # Cover letter schemas
    'CoverLetterRequest',
    'CoverLetterOutline',
    'BannedPhraseViolation',
    'BannedPhraseCheck',
    'ToneComplianceResult',
    'ATSKeywordCoverage',
    'CoverLetterRationale',
    'GeneratedCoverLetter',
    # Critic schemas
    'CriticEvaluateRequest',
    'CriticIssue',
    'ATSScoreBreakdown',
    'StructureCheckResult',
    'CriticResult',
]
