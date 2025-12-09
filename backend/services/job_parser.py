"""
Job Parser Service

Extracts structured information from job descriptions including skills,
requirements, responsibilities, and capabilities. Integrates with LLM
for core priorities and tone inference.
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from db.models import JobProfile
from services.llm.mock_llm import MockLLM
from services.company_enrichment import enrich_company_profile
from utils.text_processing import fetch_url_content, clean_text, extract_bullets, ExtractionFailedError, parse_workday_url


# Comprehensive skill taxonomy organized by category
SKILL_TAXONOMY = {
    # Programming Languages
    'languages': [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Rust',
        'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'SQL', 'Bash',
        'Shell', 'PowerShell', 'Perl', 'Haskell', 'Clojure', 'Elixir', 'Dart'
    ],

    # Web Frameworks & Libraries
    'web_frameworks': [
        'React', 'Angular', 'Vue', 'Vue.js', 'Next.js', 'Nuxt.js', 'Django',
        'Flask', 'FastAPI', 'Express', 'Express.js', 'Node.js', 'Spring', 'Spring Boot',
        'ASP.NET', '.NET', 'Ruby on Rails', 'Laravel', 'Symfony', 'jQuery'
    ],

    # AI/ML Frameworks & Tools
    'ai_ml': [
        'TensorFlow', 'PyTorch', 'Keras', 'scikit-learn', 'XGBoost', 'LightGBM',
        'Pandas', 'NumPy', 'SciPy', 'NLTK', 'spaCy', 'Hugging Face', 'OpenAI',
        'LangChain', 'LlamaIndex', 'Stable Diffusion', 'BERT', 'GPT', 'Transformer',
        'CNN', 'RNN', 'LSTM', 'GAN', 'Reinforcement Learning', 'Deep Learning',
        'Machine Learning', 'Neural Networks', 'NLP', 'Computer Vision', 'MLOps',
        'Artificial Intelligence', 'AI', 'Data Science', 'Generative AI', 'LLM',
        'Large Language Model', 'GenAI'
    ],

    # Cloud Platforms
    'cloud': [
        'AWS', 'Amazon Web Services', 'Azure', 'Microsoft Azure', 'GCP',
        'Google Cloud Platform', 'Google Cloud', 'IBM Cloud', 'Oracle Cloud',
        'DigitalOcean', 'Heroku', 'Vercel', 'Netlify', 'Cloudflare',
        'Cloud Architecture'
    ],

    # Cloud Services
    'cloud_services': [
        'EC2', 'S3', 'Lambda', 'ECS', 'EKS', 'RDS', 'DynamoDB', 'CloudFormation',
        'CloudWatch', 'IAM', 'SageMaker', 'EMR', 'Redshift', 'Kinesis', 'SNS', 'SQS',
        'Azure Functions', 'Azure DevOps', 'BigQuery', 'Cloud Functions', 'Cloud Run',
        'Dataflow', 'Pub/Sub', 'Cloud Storage', 'Compute Engine', 'App Engine'
    ],

    # DevOps & Infrastructure
    'devops': [
        'Docker', 'Kubernetes', 'K8s', 'Terraform', 'Ansible', 'Jenkins', 'GitLab CI',
        'GitHub Actions', 'CircleCI', 'Travis CI', 'ArgoCD', 'Helm', 'Prometheus',
        'Grafana', 'ELK', 'Elasticsearch', 'Logstash', 'Kibana', 'Datadog', 'New Relic',
        'CI/CD', 'GitOps', 'Infrastructure as Code', 'IaC'
    ],

    # Databases
    'databases': [
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'Oracle',
        'SQL Server', 'SQLite', 'MariaDB', 'Couchbase', 'Neo4j', 'DynamoDB',
        'Snowflake', 'BigQuery', 'Redshift', 'ClickHouse', 'TimescaleDB', 'InfluxDB'
    ],

    # Data Engineering
    'data_engineering': [
        'Apache Spark', 'Spark', 'Hadoop', 'Kafka', 'Apache Kafka', 'Airflow',
        'Apache Airflow', 'Flink', 'Storm', 'Hive', 'Presto', 'dbt', 'Databricks',
        'ETL', 'ELT', 'Data Pipeline', 'Data Warehouse', 'Data Lake', 'Stream Processing'
    ],

    # Analytics & BI
    'analytics': [
        'Tableau', 'Power BI', 'Looker', 'Metabase', 'Superset', 'QlikView',
        'Google Analytics', 'Adobe Analytics', 'Mixpanel', 'Amplitude', 'Segment',
        'Business Intelligence', 'BI', 'Data Visualization', 'Data Analysis'
    ],

    # Version Control & Collaboration
    'version_control': [
        'Git', 'GitHub', 'GitLab', 'Bitbucket', 'SVN', 'Mercurial', 'Perforce'
    ],

    # Testing & Quality
    'testing': [
        'Jest', 'Mocha', 'Pytest', 'JUnit', 'Selenium', 'Cypress', 'TestNG',
        'Postman', 'JMeter', 'LoadRunner', 'Unit Testing', 'Integration Testing',
        'E2E Testing', 'Test Automation', 'TDD', 'BDD'
    ],

    # Security
    'security': [
        'OAuth', 'JWT', 'SSL', 'TLS', 'Encryption', 'PKI', 'SAML',
        'Active Directory', 'LDAP', 'Penetration Testing', 'Vulnerability Assessment',
        'SIEM', 'Firewall', 'VPN', 'Zero Trust', 'SAST', 'DAST', 'Security Auditing'
    ],

    # AI Governance & Ethics
    'ai_governance': [
        'AI Governance', 'AI Ethics', 'Responsible AI', 'Ethical AI', 'AI Risk Management',
        'Algorithmic Fairness', 'Bias Detection', 'Model Governance', 'AI Policy',
        'AI Compliance', 'AI Safety', 'Explainability', 'Interpretability', 'XAI',
        'Model Risk Management', 'AI Auditing', 'AI Transparency'
    ],

    # Data Governance & Management
    'data_governance': [
        'Data Governance', 'Data Stewardship', 'Data Quality', 'Data Lineage',
        'Data Catalog', 'Data Dictionary', 'Metadata Management', 'Master Data Management',
        'MDM', 'Data Standards', 'Data Classification', 'Data Ownership',
        'Collibra', 'Alation', 'Informatica', 'Atlan', 'Data Management',
        'Information Governance', 'Data Policy', 'Data Architecture',
        'Enterprise Data', 'Data Strategy', 'Data Modeling'
    ],

    # Compliance & Regulations
    'compliance': [
        'GDPR', 'CCPA', 'HIPAA', 'SOC 2', 'ISO 27001', 'PCI DSS', 'NIST',
        'FISMA', 'FedRAMP', 'SOX', 'Compliance', 'Regulatory Compliance',
        'Data Privacy', 'Privacy Engineering', 'Risk Management', 'Audit'
    ],

    # Methodologies & Practices
    'methodologies': [
        'Agile', 'Scrum', 'Kanban', 'SAFe', 'Waterfall', 'Lean', 'Six Sigma',
        'ITIL', 'DevOps', 'SRE', 'Site Reliability Engineering', 'Microservices',
        'Event-Driven Architecture', 'Domain-Driven Design', 'DDD', 'CQRS',
        'API Design', 'RESTful API', 'GraphQL', 'gRPC',
        'Solution Architecture', 'System Design', 'Technical Architecture'
    ],

    # Consulting & Business
    'consulting': [
        'Strategy', 'Business Strategy', 'Digital Transformation', 'Change Management',
        'Stakeholder Management', 'Client Management', 'Project Management',
        'Program Management', 'Portfolio Management', 'Business Analysis',
        'Requirements Gathering', 'Process Improvement', 'Operational Excellence',
        'Sales', 'Business Development', 'Marketing', 'Go-to-Market', 'Pre-sales',
        'Account Management',
        'Consulting', 'AI Consulting', 'Business Consulting', 'Technology Consulting',
        'AI Strategy', 'Technology Sales', 'Innovation', 'Problem Solving'
    ],

    # Leadership & Management
    'leadership': [
        'Team Leadership', 'People Management', 'Cross-functional Leadership',
        'Executive Communication', 'Budget Management', 'Resource Planning',
        'Mentorship', 'Coaching', 'Performance Management',
        'Organizational Development', 'Culture Building',
        'Public Speaking', 'Thought Leadership', 'Strategic Communication'
    ],

    # Domain Knowledge
    'domains': [
        'Financial Services', 'FinTech', 'Healthcare', 'HealthTech', 'E-commerce',
        'Retail', 'Manufacturing', 'Supply Chain', 'Logistics', 'Telecommunications',
        'Media', 'Entertainment', 'Gaming', 'EdTech', 'GovTech', 'InsurTech',
        'Real Estate', 'PropTech', 'Energy', 'Climate Tech', 'Automotive'
    ],

    # Business Analysis & Requirements
    'business_analysis': [
        'Requirements Engineering', 'Requirements Gathering', 'User Stories',
        'Use Cases', 'BRD', 'Business Requirements Document', 'FRD',
        'Functional Requirements', 'Gap Analysis', 'Business Analysis',
        'Process Mapping', 'Process Improvement', 'Business Process', 'Workflow Analysis',
        'Elicitation', 'Requirements Elicitation', 'Requirements Analysis',
        'Requirements Management', 'Acceptance Criteria', 'User Acceptance Testing',
        'UAT', 'Requirements Traceability', 'Functional Specification',
        'Technical Specification', 'System Analysis', 'Impact Analysis'
    ],

    # Project Management Tools & Practices
    'project_management': [
        'JIRA', 'Confluence', 'Asana', 'Monday.com', 'Trello', 'Smartsheet',
        'Sprint Planning', 'Sprint', 'Backlog Management', 'Backlog Grooming',
        'Backlog Refinement', 'Story Pointing', 'Velocity Tracking',
        'Burndown Chart', 'Release Planning', 'Roadmap Planning',
        'Project Planning', 'Resource Allocation', 'Risk Planning',
        'Issue Tracking', 'Task Management', 'MS Project', 'Primavera',
        'Gantt Chart', 'Work Breakdown Structure', 'WBS'
    ],

    # Soft Skills & Leadership (explicit mentions only)
    'soft_skills': [
        'Stakeholder Management', 'Stakeholder Engagement', 'Executive Communication',
        'Cross-functional Collaboration', 'Team Collaboration', 'Client Engagement',
        'Relationship Building', 'Influence', 'Negotiation', 'Conflict Resolution',
        'Facilitation', 'Workshop Facilitation', 'Presentation Skills',
        'Public Speaking', 'Written Communication', 'Technical Writing',
        'Change Leadership', 'Organizational Change', 'Training Development',
        'Mentoring', 'Coaching', 'Team Building'
    ],

    # Data Management & Quality
    'data_management': [
        'Data Quality', 'Data Quality Assessment', 'Data Profiling',
        'Data Lineage', 'Data Lineage Tracking', 'Lineage Analysis',
        'Metadata Management', 'Metadata', 'Data Cataloging',
        'Data Stewardship', 'Data Ownership', 'Data Standards',
        'Data Modeling', 'Dimensional Modeling', 'Data Architecture',
        'Data Integration', 'Data Migration', 'Data Cleansing',
        'Data Validation', 'Master Data', 'Reference Data',
        'Data Dictionary', 'Data Mapping', 'Data Transformation'
    ]
}


# Flatten taxonomy for easy searching
ALL_SKILLS = []
for category_skills in SKILL_TAXONOMY.values():
    ALL_SKILLS.extend(category_skills)


def get_skill_category(skill: str) -> Optional[str]:
    """
    Get the category for a given skill.

    Args:
        skill: Skill name

    Returns:
        Category name if found, None otherwise
    """
    skill_lower = skill.lower()
    for category, skills in SKILL_TAXONOMY.items():
        if any(skill_lower == s.lower() for s in skills):
            return category
    return None


def infer_job_domain(jd_text: str, job_title: str = "", extracted_skills: List[str] = None) -> str:
    """
    Infer job domain/role type from job description text.

    Args:
        jd_text: Raw job description text
        job_title: Optional job title
        extracted_skills: Optional list of extracted skills

    Returns:
        Domain identifier: data_analytics, governance, consulting, engineering, product, ai_ml, or general
    """
    jd_lower = (jd_text or "").lower()
    job_title_lower = (job_title or "").lower()
    skills = [s.lower() for s in (extracted_skills or [])]

    # Domain detection patterns (order matters - more specific first)
    domain_patterns = {
        "ai_ml": [
            'ai governance', 'ai ethics', 'responsible ai', 'ai strategy',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'data scientist', 'ml engineer', 'llm', 'genai', 'generative ai'
        ],
        "governance": [
            'governance', 'compliance', 'risk management', 'audit', 'controls',
            'data governance', 'regulatory', 'policy', 'data steward'
        ],
        "data_analytics": [
            'data analyst', 'analytics', 'bi ', 'business intelligence',
            'data engineer', 'tableau', 'power bi', 'sql', 'etl'
        ],
        "consulting": [
            'consultant', 'consulting', 'advisory', 'strategy', 'transformation',
            'engagement manager', 'practice lead'
        ],
        "product": [
            'product manager', 'product owner', 'roadmap', 'product strategy',
            'product management', 'user experience', 'ux '
        ],
        "engineering": [
            'software engineer', 'developer', 'backend', 'frontend', 'full stack',
            'devops', 'sre', 'platform engineer', 'architect'
        ]
    }

    # Score each domain
    domain_scores = {domain: 0 for domain in domain_patterns}

    for domain, patterns in domain_patterns.items():
        for pattern in patterns:
            # Check in job title (highest weight)
            if pattern in job_title_lower:
                domain_scores[domain] += 3

            # Check in JD text
            if pattern in jd_lower:
                domain_scores[domain] += 1

            # Check in extracted skills
            if any(pattern in skill for skill in skills):
                domain_scores[domain] += 2

    # Return domain with highest score, or 'general' if no matches
    max_score = max(domain_scores.values())
    if max_score == 0:
        return "general"

    return max(domain_scores.items(), key=lambda x: x[1])[0]


# Seniority level patterns
SENIORITY_PATTERNS = {
    'intern': r'\b(intern|internship)\b',
    'entry': r'\b(entry[-\s]level|junior|associate|graduate)\b',
    'mid': r'\b(mid[-\s]level|intermediate)\b',
    'senior': r'\b(senior|sr\.?)\b',
    'lead': r'\b(lead|principal|staff|architect)\b',
    'manager': r'\b(manager|mgr\.?|head of)\b',
    'director': r'\b(director|dir\.?)\b',
    'vp': r'\b(vp|vice president|v\.p\.)\b',
    'executive': r'\b(cto|cio|ceo|chief|executive)\b'
}


# Job section header patterns
# Note: Order matters! Check more specific patterns first
SECTION_HEADERS = {
    'responsibilities': [
        r'responsibilities',
        r"what you['']ll do",
        r'your role',
        r'duties',
        r'day[- ]to[- ]day',
        r'role description',
        r'about the role',
        r'the role'
    ],
    'nice_to_haves': [
        r'^nice[- ]to[- ]haves?',  # Line starts with "nice to have"
        r'^preferred\s*(qualifications|skills)?$',  # "Preferred" or "Preferred Qualifications" as header
        r'^bonus\s*(points)?$',  # "Bonus" or "Bonus Points" as header
        r'^ideal\s+candidate',
        r'^it would be great if',
        r'^(a\s+)?plus$',  # "Plus" or "A Plus" as section header
    ],
    'requirements': [
        r'requirements',
        r'minimum qualifications',
        r'required qualifications',
        r'required skills',
        r"what we['']re looking for",
        r"what you['']ll bring",
        r'you have',
        r'your skills',
        r'must[- ]haves?',
        r'qualifications'  # Generic fallback
    ]
}

# Patterns that signal end of job requirements (salary, benefits, company info, etc.)
SECTION_STOP_PATTERNS = [
    r'^\$\d+',  # Salary lines starting with $
    r'\d+[,\d]*\s*(k|K)?\s*(a year|per year|annually)',  # Salary patterns
    r'^(why|about)\s+(us|[a-z]+\s*(company|here))',  # "Why us", "About [Company]"
    r'^(our\s+)?benefits',  # Benefits section
    r'^what we offer',
    r'^perks',
    r'^compensation',
    r'^salary',
    r'^(usa\s+)?employment benefits',
    r'^success metrics',  # End of qualifications, start of metrics
    r'^equal\s+(opportunity|employment)',
    r'^eeo\b',
    r'^we\s+are\s+an?\s+equal',
    r'^diversity',
    r'^location',
    r'^work\s+environment',
]


# Job type tag keywords
JOB_TYPE_KEYWORDS = {
    'ai_governance': [
        'ai governance', 'ai ethics', 'responsible ai', 'ethical ai',
        'algorithmic fairness', 'model governance', 'ai policy', 'ai compliance'
    ],
    'consulting': [
        'consultant', 'consulting', 'advisory', 'client', 'engagement',
        'stakeholder', 'strategy', 'transformation'
    ],
    'product': [
        'product manager', 'product owner', 'product management', 'roadmap',
        'product strategy', 'product development', 'user experience'
    ],
    'cloud': [
        'cloud', 'aws', 'azure', 'gcp', 'cloud infrastructure',
        'cloud architecture', 'cloud engineer', 'cloud platform'
    ],
    'financial_services': [
        'financial services', 'fintech', 'banking', 'investment',
        'trading', 'payments', 'insurance', 'wealth management'
    ],
    'engineering': [
        'software engineer', 'backend', 'frontend', 'full stack',
        'development', 'coding', 'programming', 'technical'
    ],
    'data': [
        'data scientist', 'data analyst', 'data engineer', 'analytics',
        'machine learning', 'ml engineer', 'data science'
    ],
    'security': [
        'security', 'cybersecurity', 'infosec', 'information security',
        'security engineer', 'security analyst', 'threat'
    ],
    'research': [
        'research', 'researcher', 'research scientist', 'phd',
        'publication', 'academic', 'experimental'
    ]
}


def extract_company_name(jd_text: str, job_title: str = None) -> Optional[str]:
    """
    Extract company name from job description.

    Strategies:
    1. Look for "Company: <name>" pattern
    2. Look for "at <Company>" or "join <Company>" patterns
    3. Look for "About [Company]" heading
    4. Look for possessive "[Company]'s [Platform]" patterns
    5. Check first few lines for company name patterns

    Args:
        jd_text: Job description text
        job_title: Optional extracted job title for context

    Returns:
        Company name if found, None otherwise
    """
    lines = jd_text.split('\n')

    # Common false positive words to filter out
    false_positives = [
        'we', 'the', 'our', 'this', 'an', 'a', 'us', 'company', 'the company',
        'as', 'at', 'for', 'to', 'be', 'is', 'are', 'or', 'and', 'it',
        'you', 'your', 'in', 'on', 'by', 'of', 'if', 'so', 'do', 'no',
        'new', 'all', 'can', 'who', 'has', 'had', 'get', 'job', 'now'
    ]

    # Strategy 1: Explicit "Company:" pattern
    company_patterns = [
        r'^company:\s*(.+)$',
        r'^employer:\s*(.+)$',
        r'^organization:\s*(.+)$',
    ]

    for line in lines[:15]:
        line_stripped = line.strip()
        for pattern in company_patterns:
            match = re.search(pattern, line_stripped, re.IGNORECASE)
            if match:
                return match.group(1).strip()

    # Strategy 2: Look for "at <Company>" or "join <Company>" patterns
    # Note: Regex patterns include length limits ({1,30}) to prevent ReDoS attacks
    at_patterns = [
        r'\bat\s+([A-Z][A-Za-z0-9]{1,30}(?:\s+[A-Z][A-Za-z0-9]{1,30})?),\s+we',  # "At AHEAD, we"
        r'\bat\s+([A-Z]{2,20})\b',  # "At AHEAD" (all-caps company names like AHEAD, IBM, etc.)
        r'join\s+([A-Z][A-Za-z0-9]{1,30}(?:\s+[A-Z][A-Za-z0-9]{1,30})?)\s+(?:as|and)',  # "Join AHEAD as"
        r'join\s+([A-Z]{2,20})\b',  # "Join AHEAD" (all-caps company)
        r'^([A-Z][A-Za-z0-9]{1,30}(?:\s+[A-Z][A-Za-z0-9]{1,30})?)\s+(?:builds|is|offers|provides)',  # "AHEAD builds"
        r'\b([A-Z]{2,20})\s+(?:builds|is\s+a|offers|provides|helps)',  # "AHEAD is a" or "AHEAD builds"
        r'about\s+([A-Z][A-Za-z0-9& ]{1,40}?)(?:\s*:|\s*$)',  # "About AHEAD:" or "About Company Name"
        r'(?:work|working)\s+(?:at|for|with)\s+([A-Z][A-Za-z0-9& ]{1,40}?)(?:\s*[.,!]|\s*$)',  # "work at AHEAD"
        r'(?:work|working)\s+(?:at|for|with)\s+([A-Z]{2,20})\b',  # "work at AHEAD" (all-caps)
    ]

    for line in lines[:15]:
        line_stripped = line.strip()
        # Skip very long lines to prevent regex issues
        if len(line_stripped) > 200:
            continue
        for pattern in at_patterns:
            match = re.search(pattern, line_stripped, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if company.lower() not in false_positives and len(company) >= 2:
                    return company

    # Strategy 2b: Look for company name after "posted by" or in job board format
    job_board_patterns = [
        r'posted\s+by\s*:?\s*([A-Z][A-Za-z0-9& ]{1,40})',  # "Posted by Company Name"
        r'hiring\s+company\s*:?\s*([A-Z][A-Za-z0-9& ]{1,40})',  # "Hiring Company: Name"
    ]

    for line in lines[:20]:
        line_stripped = line.strip()
        if len(line_stripped) > 200:
            continue
        for pattern in job_board_patterns:
            match = re.search(pattern, line_stripped, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if company.lower() not in ['we', 'the', 'our', 'this', 'an', 'a', 'us', 'company']:
                    return company

    # Strategy 2c: Look for "About [Company]" pattern (search full text)
    about_pattern = r"\bAbout\s+([A-Z][A-Za-z0-9& ']{2,40}?)(?:\s+Across|\s+We|\s+Our|\s+At|\s+is\s+)"
    match = re.search(about_pattern, jd_text)
    if match:
        company = match.group(1).strip()
        if company.lower() not in false_positives and len(company) >= 2:
            return company

    # Strategy 2d: Look for possessive form "[Company]'s [Product/Platform]" (search full text)
    possessive_pattern = r"\b([A-Z][A-Za-z0-9& ]{2,30})'s\s+(?:Data|Platform|Product|Service|Solution|System|Collibra)"
    match = re.search(possessive_pattern, jd_text)
    if match:
        company = match.group(1).strip()
        if company.lower() not in false_positives and len(company) >= 2:
            return company

    # Strategy 3: Check first line if it looks like a company name (all caps or title case, short)
    if lines:
        first_line = lines[0].strip()
        # Company names are often short and capitalized
        if first_line and len(first_line) <= 50 and first_line[0].isupper():
            # Exclude common form field labels
            field_labels = ['job title', 'job description', 'position', 'role', 'location',
                           'department', 'salary', 'apply', 'requirements', 'qualifications']
            if any(label in first_line.lower() for label in field_labels):
                pass  # Skip field labels
            else:
                # Check if it's NOT a job title (doesn't contain common title words)
                title_words = ['engineer', 'manager', 'consultant', 'analyst', 'developer',
                              'director', 'specialist', 'lead', 'architect', 'designer',
                              'coordinator', 'administrator', 'associate', 'senior', 'junior']
                if not any(word in first_line.lower() for word in title_words):
                    # If it's a short capitalized phrase without title words, it might be company name
                    if len(first_line.split()) <= 4:
                        return first_line

    return None


def extract_job_title(jd_text: str) -> Optional[str]:
    """
    Extract job title from job description text.

    Enhanced patterns to catch various title formats including
    "As an X, you will..." format.

    Args:
        jd_text: Job description text

    Returns:
        Job title if found, None otherwise
    """
    lines = jd_text.split('\n')

    # Title patterns in order of specificity
    title_patterns = [
        # Explicit title labels
        r'^(?:job\s+title|position|role):\s*(.+)$',
        # "As an X, you will..." pattern - common in JDs
        r'^as\s+an?\s+([^,]+),\s+you\s+will',
        # "We are seeking/hiring/looking for..."
        r'^we\s+are\s+(?:seeking|hiring|looking\s+for)\s+an?\s+([^.]+?)(?:\s+to|\s+who|\.|$)',
        # "The <Title> will..."
        r'^the\s+([A-Z][^.]+?)\s+will\s+',
    ]

    # Check lines for title patterns
    for line in lines[:20]:  # Check more lines
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 5:
            continue

        for pattern in title_patterns:
            match = re.search(pattern, line_stripped, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                # Validate it looks like a job title
                if is_likely_job_title(job_title):
                    return job_title

    # Fallback: look for first substantial line that looks like a title
    for line in lines[:10]:
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 5:
            continue

        # Skip lines that are too long (likely descriptions)
        if len(line_stripped) > 100:
            continue

        # Check if line looks like a job title
        if is_likely_job_title(line_stripped):
            return line_stripped

    return None


def is_likely_job_title(text: str) -> bool:
    """
    Check if text looks like a job title.

    Args:
        text: Text to check

    Returns:
        True if text looks like a job title
    """
    # Reject if too long
    if len(text) > 100:
        return False

    # Reject if contains multiple sentences
    if text.count('.') > 1:
        return False

    # Reject if it's a full description sentence (starts lowercase or is very long)
    if text and text[0].islower() and len(text) > 30:
        return False

    # Common job title words
    title_words = [
        'engineer', 'manager', 'consultant', 'analyst', 'developer',
        'director', 'specialist', 'lead', 'architect', 'designer',
        'coordinator', 'administrator', 'associate', 'scientist',
        'advisor', 'strategist', 'officer', 'executive', 'president',
        'head', 'chief', 'vp', 'partner', 'principal'
    ]

    text_lower = text.lower()
    return any(word in text_lower for word in title_words)


def extract_basic_fields(jd_text: str) -> Dict[str, Any]:
    """
    Extract basic job fields from job description text.

    Args:
        jd_text: Job description text

    Returns:
        Dict with job_title, company_name, location, and seniority
    """
    lines = jd_text.split('\n')
    jd_lower = jd_text.lower()

    # Extract job title using enhanced function
    job_title = extract_job_title(jd_text)
    if not job_title:
        job_title = 'Unknown Position'

    # Extract company name
    company_name = extract_company_name(jd_text, job_title)

    # Extract location
    location = None

    # Common non-location words that might match location patterns
    non_location_words = {
        'software', 'delivery', 'business', 'digital', 'cloud', 'analytics',
        'infrastructure', 'automation', 'development', 'engineering', 'design',
        'consulting', 'advisory', 'strategy', 'management', 'technology',
        'at', 'the', 'we', 'an', 'a', 'or', 'and', 'is', 'are', 'in', 'on',
        'ahead', 'join', 'company', 'team', 'our', 'your', 'you'
    }

    location_patterns = [
        r'location:\s*([^\n]{1,100})',  # Length-limited explicit location
        r'\b((?:remote|hybrid|on-?site)[^\n,;]{0,50})',  # Work arrangement with limit
        r'\b([A-Z][a-z]{1,30}(?:\s+[A-Z][a-z]{1,30})?,\s*[A-Z]{2})\b',  # City, ST
    ]

    for pattern in location_patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Validate it's not a false positive
            # Check if any word before the comma is a non-location word
            words_before_comma = candidate.split(',')[0].strip().lower().split()
            is_false_positive = any(word in non_location_words for word in words_before_comma)
            if not is_false_positive:
                location = candidate
                break

    # Default to "unknown" if no location found
    if not location:
        location = "unknown"

    # Extract seniority (check in priority order)
    seniority = None
    # Check in order of specificity (most specific first)
    priority_order = ['executive', 'vp', 'director', 'manager', 'lead', 'senior', 'mid', 'entry', 'intern']
    for level in priority_order:
        pattern = SENIORITY_PATTERNS[level]
        if re.search(pattern, jd_lower):
            seniority = level
            break

    return {
        'job_title': job_title,
        'company_name': company_name,
        'location': location,
        'seniority': seniority
    }


def extract_sections(jd_text: str) -> Dict[str, List[str]]:
    """
    Extract structured sections from job description.

    Args:
        jd_text: Job description text

    Returns:
        Dict with responsibilities, requirements, and nice_to_haves as lists
    """
    sections = {
        'responsibilities': [],
        'requirements': [],
        'nice_to_haves': []
    }

    lines = jd_text.split('\n')
    current_section = None

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        line_stripped = line.strip()

        # Skip empty lines
        if not line_stripped:
            continue

        # Check if we've hit a stop pattern (salary, benefits, company info, etc.)
        is_stop = False
        for pattern in SECTION_STOP_PATTERNS:
            if re.search(pattern, line_lower):
                current_section = None  # Stop collecting
                is_stop = True
                break
        if is_stop:
            continue

        # Check if this line is a section header
        is_header = False
        for section_name, patterns in SECTION_HEADERS.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    current_section = section_name
                    is_header = True
                    break
            if is_header:
                break

        # Skip header lines
        if is_header:
            continue

        # Extract content if we're in a section
        if current_section:
            # Check if this line is a bullet point
            bullet_patterns = [
                r'^[\s]*[-*+•◦▪▫]\s+(.+)$',  # Symbol bullets
                r'^[\s]*\d+[\.)]\s+(.+)$',   # Numbered bullets
            ]

            bullet_text = None
            for pattern in bullet_patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    bullet_text = match.group(1).strip()
                    break

            if bullet_text:
                sections[current_section].append(bullet_text)
            # Or add non-empty lines that look like substantial content
            elif len(line_stripped) > 20:
                # Check it's not a new section header
                is_new_section = False
                for patterns in SECTION_HEADERS.values():
                    for pattern in patterns:
                        if re.search(pattern, line_lower):
                            is_new_section = True
                            break
                    if is_new_section:
                        break

                if not is_new_section:
                    sections[current_section].append(line_stripped)

    return sections


def extract_skills_keywords(jd_text: str) -> List[str]:
    """
    Extract skills from job description using taxonomy.

    Filters out skills that only appear in boilerplate sections (EEO, About Company,
    Benefits) to avoid false positives like "Sales" from company descriptions.

    Args:
        jd_text: Job description text

    Returns:
        List of unique skills found in the text (excluding boilerplate-only mentions)
    """
    jd_lower = jd_text.lower()

    # Identify boilerplate section boundaries
    boilerplate_patterns = [
        r'about\s+(us|[a-z]+\s+company|state\s+street|the\s+company)',
        r'who\s+we\s+are',
        r'equal\s+(opportunity|employment)',
        r'eeo\b',
        r'we\s+are\s+an?\s+equal',
        r'diversity\s+(and|&)\s+inclusion',
        r'our\s+benefits',
        r'what\s+we\s+offer',
        r'perks\s+and\s+benefits',
        r'state\s+street\s+is\s+',  # Company description pattern
        r'across\s+the\s+globe',  # EEO boilerplate
        r'employment\s+opportunity',
        r'our\s+mission',
        r'our\s+values',
        r'our\s+culture',
        r'employee\s+benefits',
        r'we\s+offer\s+a',
        r'compensation\s+package',
        r'salary\s+range',
        r'^\$\d+',  # Salary lines
        r'\d+[,\d]*\s*k\s*(per\s+year|annually)',  # Salary ranges
        r'join\s+us',
        r'apply\s+now',
        r'learn\s+more',
    ]

    # Find where boilerplate starts
    boilerplate_start = len(jd_text)
    for pattern in boilerplate_patterns:
        match = re.search(pattern, jd_lower)
        if match:
            boilerplate_start = min(boilerplate_start, match.start())

    # Extract text before and within boilerplate
    main_text = jd_text[:boilerplate_start].lower()
    boilerplate_text = jd_text[boilerplate_start:].lower() if boilerplate_start < len(jd_text) else ""

    found_skills = set()
    boilerplate_only_skills = set()

    # Case-insensitive matching for each skill in taxonomy
    for skill in ALL_SKILLS:
        skill_lower = skill.lower()
        # Use word boundaries for better matching
        pattern = r'\b' + re.escape(skill_lower) + r'\b'

        in_main = bool(re.search(pattern, main_text))
        in_boilerplate = bool(re.search(pattern, boilerplate_text))

        if in_main:
            # Found in main content - definitely include
            found_skills.add(skill)
        elif in_boilerplate:
            # Only found in boilerplate - mark for potential exclusion
            boilerplate_only_skills.add(skill)

    # Skills that only appear in boilerplate are likely not real requirements
    # Exception: Keep technical skills even if in boilerplate (they're less likely to be false positives)
    non_technical_boilerplate = {
        'Sales', 'Marketing', 'Business Development', 'Account Management',
        'Go-to-Market', 'GTM', 'Pre-sales', 'Revenue', 'Sales Strategy',
        'Account Executive', 'Customer Success', 'Account Growth'
    }
    for skill in boilerplate_only_skills:
        if skill not in non_technical_boilerplate:
            found_skills.add(skill)

    # Special handling for "Go" (Golang)
    # 1. Must be "Go" (Title case) or "Golang" (handled by taxonomy if added, but "Go" is the issue)
    # 2. Must NOT be part of "go-to-market" or "go-getter"
    if re.search(r'\bGo\b', jd_text[:boilerplate_start]):
        # Check for false positive contexts
        # "go-to-market" usually appears as "go-to-market" or "Go-to-Market"
        # If "Go" is followed by "-to-", it's likely a phrase
        if not re.search(r'\bGo-to-\b', jd_text, re.IGNORECASE):
             found_skills.add('Go')

    return sorted(list(found_skills))


def determine_job_type_tags(jd_text: str, skills: List[str], title: str) -> List[str]:
    """
    Determine job type tags based on keywords and skills.

    Args:
        jd_text: Job description text
        skills: List of extracted skills
        title: Job title

    Returns:
        List of relevant job type tags
    """
    jd_lower = jd_text.lower()
    title_lower = title.lower()
    skills_lower = ' '.join([s.lower() for s in skills])

    # Combine all text for matching
    combined_text = f"{jd_lower} {title_lower} {skills_lower}"

    tags = set()

    for tag, keywords in JOB_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined_text:
                tags.add(tag)
                break

    return sorted(list(tags))


def determine_capabilities(
    requirements: List[str],
    responsibilities: List[str],
    nice_to_haves_section: List[str]
) -> Tuple[List[str], List[str]]:
    """
    Extract must-have and nice-to-have capabilities with enhanced detection.

    Enhanced in Task 2.7 to better identify and categorize capabilities:
    - Stronger signal detection for must-haves vs nice-to-haves
    - Extracts specific skills and experiences from requirement text
    - Validates capabilities are substantive
    - Removes duplicates and overly generic statements

    Args:
        requirements: List of requirement strings
        responsibilities: List of responsibility strings
        nice_to_haves_section: List of nice-to-have strings from dedicated section

    Returns:
        Tuple of (must_have_capabilities, nice_to_have_capabilities)
    """
    must_haves = []
    nice_to_haves = []
    seen_capabilities = set()  # Track to avoid duplicates

    # Enhanced keywords indicating must-have requirements
    must_have_indicators = [
        'required', 'must have', 'must be', 'must possess', 'essential', 'mandatory',
        'minimum', 'necessary', 'need to have', 'needs to have', 'critical',
        'you will need', 'you must', 'required to have', 'should have',
        'requires', 'required:', 'requirements:', 'qualifications:'
    ]

    # Enhanced keywords indicating nice-to-have requirements
    nice_to_have_indicators = [
        'preferred', 'nice to have', 'bonus', 'plus', 'ideal', 'ideally',
        'desirable', 'would be great', 'advantage', 'beneficial',
        'a plus', 'is a plus', 'nice-to-have', 'optional',
        'preferred qualifications', 'we would love', 'great if you'
    ]

    # Generic phrases to filter out (too vague to be useful capabilities)
    generic_phrases = [
        'communication skills',
        'strong communication',
        'team player',
        'self-starter',
        'fast-paced environment',
        'detail-oriented',
        'problem solver',
        'problem solving',
        'quick learner',
        'work independently',
        'self-motivated',
        'highly motivated'
    ]

    def is_substantive(capability: str) -> bool:
        """Check if capability is substantive enough to include."""
        # Must be at least 15 characters
        if len(capability) < 15:
            return False

        # Reject if it's a generic phrase
        cap_lower = capability.lower()
        for generic in generic_phrases:
            if generic in cap_lower:
                return False

        # Should contain at least one meaningful word (skill, experience, knowledge)
        meaningful_keywords = [
            'experience', 'knowledge', 'understanding', 'proficiency',
            'expertise', 'degree', 'certification', 'years', 'skill',
            'ability to', 'working with', 'development', 'design',
            'implementation', 'management', 'analysis', 'framework',
            'language', 'tool', 'platform', 'system'
        ]

        return any(keyword in cap_lower for keyword in meaningful_keywords)

    def extract_key_capability(text: str) -> str:
        """Extract the core capability from requirement text."""
        # Clean up common prefixes first (before removing years)
        text = re.sub(r'^(proven|strong|excellent|demonstrated|solid)\s+', '', text, flags=re.IGNORECASE)

        # Remove leading numbers (e.g., "5+ years of Python" -> "Python experience")
        text = re.sub(r'^\d+[\+]?\s+(years?|yrs?)\s+(of\s+)?', '', text, flags=re.IGNORECASE)

        # Truncate at common ending phrases
        for ending in [' in a fast-paced', ' with the ability', ' and ability to']:
            if ending in text.lower():
                text = text[:text.lower().index(ending)]

        return text.strip()

    def normalize_capability(text: str) -> str:
        """Normalize capability for deduplication."""
        # Convert to lowercase and remove extra whitespace
        normalized = ' '.join(text.lower().split())
        # Remove punctuation at the end
        normalized = normalized.rstrip('.,;:')
        return normalized

    # Process requirements with enhanced categorization
    for req in requirements:
        if not req or len(req.strip()) < 10:
            continue

        req_stripped = req.strip()
        req_lower = req.lower()

        # Extract core capability
        capability = extract_key_capability(req_stripped)

        # Skip if not substantive
        if not is_substantive(capability):
            continue

        # Check for duplicates
        normalized = normalize_capability(capability)
        if normalized in seen_capabilities:
            continue
        seen_capabilities.add(normalized)

        # Strong nice-to-have indicators take precedence
        is_nice_to_have = any(indicator in req_lower for indicator in nice_to_have_indicators)
        is_must_have = any(indicator in req_lower for indicator in must_have_indicators)

        if is_nice_to_have:
            nice_to_haves.append(capability)
        elif is_must_have or not is_nice_to_have:
            # Default requirements to must-haves if not explicitly nice-to-have
            must_haves.append(capability)

    # Process nice-to-haves section
    for nth in nice_to_haves_section:
        if not nth or len(nth.strip()) < 10:
            continue

        capability = extract_key_capability(nth.strip())

        if not is_substantive(capability):
            continue

        normalized = normalize_capability(capability)
        if normalized in seen_capabilities:
            continue
        seen_capabilities.add(normalized)

        nice_to_haves.append(capability)

    # Add key responsibilities as must-have capabilities
    # These represent what you'll actually be doing in the role
    for resp in responsibilities[:5]:  # Top 5 responsibilities
        if not resp or len(resp.strip()) < 20:
            continue

        capability = extract_key_capability(resp.strip())

        # Responsibilities should be substantial
        if len(capability) < 20:
            continue

        normalized = normalize_capability(capability)
        if normalized in seen_capabilities:
            continue
        seen_capabilities.add(normalized)

        # Responsibilities are implicit must-haves (you'll be doing this)
        must_haves.append(capability)

    # Validate that we have at least some capabilities
    if not must_haves and not nice_to_haves:
        # Fallback: use raw requirements if extraction failed
        must_haves = [req for req in requirements if len(req) > 15][:10]

    return must_haves[:20], nice_to_haves[:15]  # Cap at reasonable limits


async def extract_skills_hybrid(
    jd_text: str,
    job_title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    llm: Optional[Any] = None,
    use_llm: bool = True
) -> Dict[str, Any]:
    """
    Hybrid skill extraction: Taxonomy + LLM.

    Strategy:
    1. Extract skills via taxonomy matching (fast, high precision)
    2. If LLM available and enabled, run LLM extraction (comprehensive)
    3. Merge results, deduplicating and preserving categorization

    Args:
        jd_text: Job description text
        job_title: Job title (optional, will be inferred if not provided)
        context: Dict with responsibilities, requirements, etc. (optional)
        llm: LLM instance (MockLLM or ClaudeLLM) (optional, will create if needed)
        use_llm: Whether to use LLM extraction

    Returns:
        Dict with:
        - taxonomy_skills: List[str] - skills from taxonomy matching
        - llm_skills: List[str] - all skills from LLM extraction
        - all_skills: List[str] - deduplicated union of both sources
        - overlap: List[str] - skills found by both methods
        - critical_skills: List[str] - must-have skills (from LLM)
        - preferred_skills: List[str] - nice-to-have skills (from LLM)
        - domain_skills: List[str] - domain-specific skills (from LLM)
        - confidence: float - weighted confidence score (0.0-1.0)
    """
    import logging
    logger = logging.getLogger(__name__)

    # Input validation
    if not isinstance(jd_text, str):
        raise TypeError("jd_text must be a string")
    if len(jd_text) > 100000:  # 100KB limit
        raise ValueError("jd_text exceeds maximum length (100KB)")
    if not jd_text.strip():
        raise ValueError("jd_text cannot be empty")

    if context is not None and not isinstance(context, dict):
        raise TypeError("context must be a dict or None")

    # Step 1: Taxonomy extraction (baseline)
    taxonomy_skills = extract_skills_keywords(jd_text)

    result = {
        'taxonomy_skills': taxonomy_skills,
        'llm_skills': [],
        'all_skills': taxonomy_skills.copy(),
        'overlap': [],
        'critical_skills': [],
        'preferred_skills': [],
        'domain_skills': [],
        'confidence': 0.5  # Default to 0.5 if only taxonomy is used
    }

    # Step 2: LLM extraction (if enabled)
    if use_llm:
        try:
            # Create LLM instance if not provided
            if llm is None:
                llm = MockLLM()

            llm_result = await llm.extract_skills_from_jd(
                jd_text=jd_text,
                taxonomy_skills=taxonomy_skills,
                job_title=job_title,
                context=context
            )

            # Get all skills from LLM
            llm_all_skills = llm_result.get('extracted_skills', [])

            # Calculate overlap (skills found by both methods)
            overlap = [s for s in taxonomy_skills if s in llm_all_skills]

            # Combine all skills (deduplicated)
            all_skills = list(set(taxonomy_skills + llm_all_skills))

            # Calculate LLM-only skills for logging
            llm_only_skills = [s for s in llm_all_skills if s not in taxonomy_skills]

            # Calculate weighted confidence
            # Higher confidence when both methods agree
            taxonomy_count = len(taxonomy_skills)
            llm_count = len(llm_all_skills)
            overlap_count = len(overlap)

            if taxonomy_count + llm_count > 0:
                # Confidence based on overlap ratio and LLM confidence
                overlap_ratio = overlap_count / max(taxonomy_count, llm_count) if max(taxonomy_count, llm_count) > 0 else 0
                base_confidence = llm_result.get('confidence', 0.75)
                result['confidence'] = min(1.0, base_confidence * (0.7 + 0.3 * overlap_ratio))
            else:
                result['confidence'] = 0.5

            result['llm_skills'] = llm_all_skills  # All skills from LLM, not just LLM-only
            result['all_skills'] = all_skills
            result['overlap'] = overlap
            result['critical_skills'] = llm_result.get('critical_skills', [])
            result['preferred_skills'] = llm_result.get('preferred_skills', [])
            result['domain_skills'] = llm_result.get('domain_skills', [])

            logger.info(
                f"Hybrid extraction: {len(taxonomy_skills)} taxonomy + "
                f"{len(llm_only_skills)} LLM-only = {len(all_skills)} total "
                f"(overlap: {len(overlap)}, confidence: {result['confidence']:.2f})"
            )

        except Exception as e:
            logger.warning(f"LLM skill extraction failed, using taxonomy only: {e}")

    return result


async def parse_job_description(
    jd_text: Optional[str],
    jd_url: Optional[str],
    user_id: int,
    db: Session
) -> JobProfile:
    """
    Parse job description and create JobProfile in database.

    Main entry point for job description parsing. Extracts structured
    information, analyzes with LLM, and persists to database.

    Args:
        jd_text: Raw job description text (optional if jd_url provided)
        jd_url: URL to fetch job description from (optional if jd_text provided)
        user_id: User ID for associating the job profile
        db: SQLAlchemy database session

    Returns:
        Created JobProfile ORM object

    Raises:
        ValueError: If neither jd_text nor jd_url is provided
        requests.RequestException: If URL fetch fails
    """
    # Validate input
    if not jd_text and not jd_url:
        raise ValueError("Must provide either jd_text or jd_url")

    # Fetch content if URL provided
    if jd_url:
        try:
            jd_text = fetch_url_content(jd_url)
        except ExtractionFailedError:
            # Re-raise with the user-friendly message intact
            raise
        except Exception as e:
            raise ValueError(f"Failed to fetch content from URL: {str(e)}")

    # Clean the text
    jd_text = clean_text(jd_text)

    if not jd_text or len(jd_text) < 50:
        raise ValueError("Job description text is too short or empty")

    # Extract basic fields from content
    basic_fields = extract_basic_fields(jd_text)
    job_title = basic_fields['job_title']
    company_name = basic_fields.get('company_name')
    location = basic_fields['location']
    seniority = basic_fields['seniority']

    # If URL provided, try to extract metadata from URL structure (especially for Workday)
    if jd_url:
        url_metadata = parse_workday_url(jd_url)
        # Use URL metadata to fill in missing or incorrectly extracted fields
        if url_metadata.get('job_title') and (not job_title or job_title == 'Unknown Position'):
            job_title = url_metadata['job_title']

        # Check for bad company extractions (common false positives)
        bad_company_values = ['job title:', 'job description:', 'company:', 'unknown', 'the company']
        if url_metadata.get('company_name'):
            if not company_name or (company_name and company_name.lower() in bad_company_values):
                company_name = url_metadata['company_name']

        # Check for bad location extractions (EEO text, etc.)
        bad_location_indicators = ['opportunity employer', 'equal', 'eeo', 'unknown']
        if url_metadata.get('location'):
            if not location or location == 'unknown' or any(
                bad in location.lower() for bad in bad_location_indicators
            ):
                location = url_metadata['location']

    # Extract sections
    sections = extract_sections(jd_text)
    responsibilities = sections['responsibilities']
    requirements = sections['requirements']
    nice_to_haves = sections['nice_to_haves']

    # Extract skills
    skills = extract_skills_keywords(jd_text)

    # Determine job type tags
    job_type_tags = determine_job_type_tags(jd_text, skills, job_title)

    # Determine capabilities with enhanced extraction
    must_have_capabilities, nice_to_have_capabilities = determine_capabilities(
        requirements, responsibilities, nice_to_haves
    )

    # Validate capabilities are populated (Task 2.7)
    if not must_have_capabilities and not nice_to_have_capabilities:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"No capabilities extracted for job profile: {job_title}. "
            f"Requirements: {len(requirements)}, Responsibilities: {len(responsibilities)}"
        )

        # Fallback: use raw requirements and responsibilities
        if requirements:
            must_have_capabilities = requirements[:10]
        elif responsibilities:
            must_have_capabilities = responsibilities[:10]
        else:
            # Last resort: extract from full JD text
            must_have_capabilities = [
                line.strip() for line in jd_text.split('\n')
                if 15 < len(line.strip()) < 200 and
                any(keyword in line.lower() for keyword in ['experience', 'knowledge', 'skill', 'ability'])
            ][:10]

    # Use LLM for core priorities and tone
    llm = MockLLM()
    context = {
        'job_title': job_title,
        'skills': skills,
        'requirements': requirements,
        'responsibilities': responsibilities
    }

    core_priorities = await llm.generate_core_priorities(jd_text, context)
    tone_style = await llm.infer_tone(jd_text)

    # Create JobProfile ORM object
    job_profile = JobProfile(
        user_id=user_id,
        raw_jd_text=jd_text,
        jd_url=jd_url,
        job_title=job_title,
        company_name=company_name,
        location=location,
        seniority=seniority,
        responsibilities='\n'.join(responsibilities) if responsibilities else None,
        requirements='\n'.join(requirements) if requirements else None,
        nice_to_haves='\n'.join(nice_to_haves) if nice_to_haves else None,
        extracted_skills=skills,
        core_priorities=core_priorities,
        must_have_capabilities=must_have_capabilities,
        nice_to_have_capabilities=nice_to_have_capabilities,
        tone_style=tone_style,
        job_type_tags=job_type_tags
    )

    # Persist to database
    db.add(job_profile)
    db.commit()
    db.refresh(job_profile)

    # Auto-enrich company profile if company name was extracted (Sprint 12)
    if company_name:
        try:
            import logging
            logger = logging.getLogger(__name__)

            company_profile = await enrich_company_profile(
                company_name=company_name,
                jd_text=jd_text,
                db=db,
            )

            # Link the company profile to the job profile
            job_profile.company_id = company_profile.id
            db.commit()
            db.refresh(job_profile)

            logger.info(f"Auto-enriched company profile for {company_name} (id={company_profile.id})")
        except Exception as e:
            # Log but don't fail - company enrichment is optional
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Company enrichment failed for {company_name}: {e}")

    return job_profile
