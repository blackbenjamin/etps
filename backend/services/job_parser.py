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
from utils.text_processing import fetch_url_content, clean_text, extract_bullets


# Comprehensive skill taxonomy organized by category
SKILL_TAXONOMY = {
    # Programming Languages
    'languages': [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
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
        'Machine Learning', 'Neural Networks', 'NLP', 'Computer Vision', 'MLOps'
    ],

    # Cloud Platforms
    'cloud': [
        'AWS', 'Amazon Web Services', 'Azure', 'Microsoft Azure', 'GCP',
        'Google Cloud Platform', 'Google Cloud', 'IBM Cloud', 'Oracle Cloud',
        'DigitalOcean', 'Heroku', 'Vercel', 'Netlify', 'Cloudflare'
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
        'OAuth', 'JWT', 'SSL', 'TLS', 'HTTPS', 'Encryption', 'PKI', 'SAML',
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
        'API Design', 'RESTful API', 'GraphQL', 'gRPC'
    ],

    # Consulting & Business
    'consulting': [
        'Strategy', 'Business Strategy', 'Digital Transformation', 'Change Management',
        'Stakeholder Management', 'Client Management', 'Project Management',
        'Program Management', 'Portfolio Management', 'Business Analysis',
        'Requirements Gathering', 'Process Improvement', 'Operational Excellence'
    ],

    # Leadership & Management
    'leadership': [
        'Team Leadership', 'People Management', 'Cross-functional Leadership',
        'Executive Communication', 'Budget Management', 'Resource Planning',
        'Hiring', 'Mentorship', 'Coaching', 'Performance Management',
        'Organizational Development', 'Culture Building'
    ],

    # Domain Knowledge
    'domains': [
        'Financial Services', 'FinTech', 'Healthcare', 'HealthTech', 'E-commerce',
        'Retail', 'Manufacturing', 'Supply Chain', 'Logistics', 'Telecommunications',
        'Media', 'Entertainment', 'Gaming', 'EdTech', 'GovTech', 'InsurTech',
        'Real Estate', 'PropTech', 'Energy', 'Climate Tech', 'Automotive'
    ]
}


# Flatten taxonomy for easy searching
ALL_SKILLS = []
for category_skills in SKILL_TAXONOMY.values():
    ALL_SKILLS.extend(category_skills)


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
        r'nice[- ]to[- ]haves?',
        r'preferred qualifications',
        r'preferred',
        r'bonus',
        r'plus',
        r'ideal',
        r'it would be great if'
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


def extract_basic_fields(jd_text: str) -> Dict[str, Any]:
    """
    Extract basic job fields from job description text.

    Args:
        jd_text: Job description text

    Returns:
        Dict with job_title, location, and seniority
    """
    lines = jd_text.split('\n')

    # Extract job title (usually first non-empty line or after "Job Title:", "Position:", etc.)
    job_title = None
    title_patterns = [
        r'^(?:job\s+title|position|role):\s*(.+)$',
        r'^(.+?)(?:\s*[-–—]\s*|$)'  # First line up to dash or end
    ]

    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Check explicit title patterns
        for pattern in title_patterns[:-1]:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                break

        # If no explicit pattern, use first substantial line
        if not job_title and len(line) > 10 and len(line) < 100:
            job_title = line
            break

    # Extract location
    location = None
    location_patterns = [
        r'location:\s*([^\n]+)',
        r'\b((?:remote|hybrid|on-?site)[^\n,;]*)',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*[A-Z]{2})\b',  # City, ST
        r'\b([A-Z][a-z]+,\s*[A-Z][a-z]+)\b'  # City, Country
    ]

    jd_lower = jd_text.lower()
    for pattern in location_patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            break

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
        'job_title': job_title or 'Unknown Position',
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

    Args:
        jd_text: Job description text

    Returns:
        List of unique skills found in the text
    """
    jd_lower = jd_text.lower()
    found_skills = set()

    # Case-insensitive matching for each skill in taxonomy
    for skill in ALL_SKILLS:
        skill_lower = skill.lower()
        # Use word boundaries for better matching
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, jd_lower):
            found_skills.add(skill)

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
    Extract must-have and nice-to-have capabilities.

    Args:
        requirements: List of requirement strings
        responsibilities: List of responsibility strings
        nice_to_haves_section: List of nice-to-have strings from dedicated section

    Returns:
        Tuple of (must_have_capabilities, nice_to_have_capabilities)
    """
    must_haves = []
    nice_to_haves = []

    # Keywords indicating must-have requirements
    must_have_indicators = [
        'required', 'must have', 'must be', 'essential', 'mandatory',
        'minimum', 'necessary', 'need to have', 'needs to have'
    ]

    # Keywords indicating nice-to-have requirements
    nice_to_have_indicators = [
        'preferred', 'nice to have', 'bonus', 'plus', 'ideal',
        'desirable', 'would be great', 'advantage'
    ]

    # Process requirements
    for req in requirements:
        req_lower = req.lower()

        # Check for nice-to-have indicators first
        if any(indicator in req_lower for indicator in nice_to_have_indicators):
            nice_to_haves.append(req)
        else:
            # Default requirements to must-haves
            must_haves.append(req)

    # Add items from nice-to-haves section
    nice_to_haves.extend(nice_to_haves_section)

    # Add key responsibilities as capabilities
    for resp in responsibilities[:5]:  # Top 5 responsibilities
        if len(resp) > 30:  # Only substantial responsibilities
            must_haves.append(resp)

    return must_haves, nice_to_haves


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
        except Exception as e:
            raise ValueError(f"Failed to fetch content from URL: {str(e)}")

    # Clean the text
    jd_text = clean_text(jd_text)

    if not jd_text or len(jd_text) < 50:
        raise ValueError("Job description text is too short or empty")

    # Extract basic fields
    basic_fields = extract_basic_fields(jd_text)
    job_title = basic_fields['job_title']
    location = basic_fields['location']
    seniority = basic_fields['seniority']

    # Extract sections
    sections = extract_sections(jd_text)
    responsibilities = sections['responsibilities']
    requirements = sections['requirements']
    nice_to_haves = sections['nice_to_haves']

    # Extract skills
    skills = extract_skills_keywords(jd_text)

    # Determine job type tags
    job_type_tags = determine_job_type_tags(jd_text, skills, job_title)

    # Determine capabilities
    must_have_capabilities, nice_to_have_capabilities = determine_capabilities(
        requirements, responsibilities, nice_to_haves
    )

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

    return job_profile
