"""
ETPS Constants and Configuration

v1.3.0 schema constants including domain tags, skill categories,
and other vocabulary for consistent tagging and categorization.
"""

# Schema version
SCHEMA_VERSION = "1.3.0"

# Domain tags master vocabulary
# Used for tagging engagements, experiences, and skills
DOMAIN_TAGS_MASTER = [
    "Financial Services",
    "Broker-Dealer",
    "Asset Management",
    "Banking",
    "WealthTech",
    "Core Banking Integration",
    "Regulatory Compliance",
    "SEC Modernization",
    "AI Strategy",
    "AI Governance",
    "Data Governance",
    "Data Architecture",
    "Analytics Modernization",
    "Cloud Platforms",
    "DoD / Defense",
    "Kessel Run",
    "Enterprise Transformations",
]

# Skill categories for grouping in skills section
SKILL_CATEGORIES = [
    "AI/ML",
    "Governance",
    "Architecture",
    "Tech",
    "Cloud",
    "Analytics",
    "Security",
    "BI/Tooling",
]

# Skill levels (for level field)
SKILL_LEVELS = ["expert", "advanced", "intermediate", "basic"]

# Employer types
EMPLOYER_TYPES = ["independent_consulting", "full_time", "contract"]

# Project types for engagements
PROJECT_TYPES = ["advisory", "product_build", "implementation", "strategy"]

# Bullet importance levels
BULLET_IMPORTANCE_LEVELS = ["high", "medium", "low"]

# Seniority levels
SENIORITY_LEVELS = [
    "executive",      # C-suite, VP
    "director",       # Director, Senior Director
    "senior_ic",      # Principal, Senior Manager, Lead
    "mid",            # Manager, Senior IC
    "entry",          # Analyst, Associate
]

# Banned phrases for summary and cover letters
BANNED_PHRASES = [
    "I am writing to express my interest",
    "Passionate",
    "Dynamic professional",
    "I believe I would be a great fit",
    "Per your job description",
    "Synergy",
    "Leverage",
    "Results-driven",
    "Self-starter",
    "Team player",
]

# Resume section order (v1.3.0: Skills before Education)
RESUME_SECTION_ORDER = [
    "header",
    "summary",
    "experience",
    "skills",
    "education",
]

# Benjamin Black Consulting client list (fixed order for BBC roles)
BBC_CLIENTS = [
    {
        "name": "Edward Jones",
        "project_name": "Enterprise Data Strategy & Governance",
        "start": "2/2023",
        "end": "11/2023",
        "domain_tags": ["Financial Services", "Broker-Dealer", "Data Governance"],
    },
    {
        "name": "Darling Consulting Group",
        "project_name": "Data Strategy & Analytics Portal",
        "start": "9/2022",
        "end": "1/2023",
        "domain_tags": ["Financial Services", "Banking", "Analytics Modernization"],
    },
    {
        "name": "Squark (Machine Learning / AI Startup)",
        "project_name": "AI Platform Development",
        "start": "5/2018",
        "end": "7/2020",
        "domain_tags": ["AI Strategy", "AI/ML"],
    },
    {
        "name": "Vestmark, Inc.",
        "project_name": "Data Strategy & Analytics",
        "start": "7/2017",
        "end": "3/2018",
        "domain_tags": ["Financial Services", "WealthTech", "Data Architecture"],
    },
    {
        "name": "John Hancock Investments (through Olmstead Associates)",
        "project_name": "Analytics Modernization",
        "start": "11/2016",
        "end": "1/2017",
        "domain_tags": ["Financial Services", "Asset Management", "Analytics Modernization"],
    },
    {
        "name": "Olmstead Associates",
        "project_name": "Data Management Consulting",
        "start": "1/2017",
        "end": "5/2017",
        "domain_tags": ["Data Governance", "Data Architecture"],
    },
    {
        "name": "Fidelity Investments",
        "project_name": "Asset Management Analytics",
        "start": "8/2016",
        "end": "11/2016",
        "domain_tags": ["Financial Services", "Asset Management", "Analytics Modernization"],
    },
]

# Contact info defaults (can be overridden per user)
DEFAULT_CONTACT = {
    "email": "ben@benjaminblack.consulting",
    "phone": "617-504-5529",
    "portfolio_url": "projects.benjaminblack.consulting",
    "linkedin_url": "linkedin.com/in/benjaminblack",
    "location": "Boston, MA",
}
