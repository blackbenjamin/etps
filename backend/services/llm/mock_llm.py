"""
Mock LLM Implementation

Heuristic-based mock LLM for development and testing without API calls.
Returns realistic responses based on keyword detection and pattern matching.
"""

from typing import List, Dict, Any, Optional
from .base import BaseLLM


class MockLLM(BaseLLM):
    """
    Mock LLM implementation using heuristic rules.

    Provides realistic responses for development and testing without
    requiring actual LLM API calls. Uses keyword detection and
    predefined templates.
    """

    # Priority templates organized by domain
    PRIORITY_TEMPLATES = {
        'ai_governance': [
            "AI governance framework development and implementation",
            "Policy and compliance oversight for AI systems",
            "Risk management and ethical AI practices",
            "Stakeholder alignment on AI ethics standards"
        ],
        'data_governance': [
            "Data governance framework development and policy enforcement",
            "Data quality management and stewardship programs",
            "Regulatory compliance and data privacy oversight",
            "Metadata management and data lineage tracking"
        ],
        'cloud': [
            "Cloud infrastructure architecture and optimization",
            "Scalable system design and deployment",
            "Platform reliability and performance",
            "DevOps and CI/CD pipeline management"
        ],
        'ai_ml': [
            "Machine learning model development and deployment",
            "AI/ML system integration and productionization",
            "Data pipeline and MLOps infrastructure",
            "Model performance monitoring and optimization"
        ],
        'product': [
            "Product strategy and roadmap development",
            "Cross-functional team collaboration",
            "User experience and customer success",
            "Data-driven product decision making"
        ],
        'consulting': [
            "Client relationship management and consulting delivery",
            "Strategic advisory and recommendations",
            "Executive stakeholder communication",
            "Project scoping and solution design"
        ],
        'data': [
            "Data analytics and insights generation",
            "Business intelligence and reporting",
            "Data strategy and architecture",
            "Analytics platform development"
        ],
        'security': [
            "Security architecture and threat modeling",
            "Compliance and regulatory requirements",
            "Security operations and incident response",
            "Privacy and data protection"
        ],
        'leadership': [
            "Team leadership and people management",
            "Strategic planning and execution",
            "Budget and resource management",
            "Organizational culture development"
        ],
        'research': [
            "Research methodology and experimental design",
            "Academic publication and knowledge sharing",
            "Innovation and emerging technology exploration",
            "Technical thought leadership"
        ],
        'engineering': [
            "Software engineering best practices",
            "Technical architecture and system design",
            "Code quality and technical debt management",
            "Engineering team mentorship"
        ]
    }

    # Tone categories with keyword patterns
    TONE_PATTERNS = {
        'mission_driven': [
            'mission', 'impact', 'social good', 'purpose', 'change the world',
            'make a difference', 'meaningful work', 'values', 'vision'
        ],
        'startup_casual': [
            'fast-paced', 'agile', 'scrappy', 'wear many hats', 'dynamic',
            'startup', 'fast-growing', 'move fast', 'iterate quickly', 'fun'
        ],
        'formal_corporate': [
            'enterprise', 'fortune 500', 'established', 'comprehensive',
            'structured', 'professional', 'corporate', 'policy', 'framework'
        ],
        'technical_precise': [
            'algorithm', 'architecture', 'scalability', 'performance',
            'optimization', 'engineering', 'technical', 'system design'
        ],
        'consulting_professional': [
            'client', 'advisory', 'consulting', 'engagement', 'stakeholder',
            'strategic', 'recommendations', 'executive', 'presentation'
        ],
        'academic_research': [
            'research', 'publication', 'phd', 'academic', 'peer-reviewed',
            'methodology', 'experimental', 'theory', 'analysis'
        ]
    }

    def __init__(self):
        """Initialize the mock LLM."""
        pass

    async def generate_core_priorities(self, jd_text: str, context: Dict) -> List[str]:
        """
        Generate core priorities based on keyword detection.

        Args:
            jd_text: The job description text
            context: Additional context (ignored in mock implementation)

        Returns:
            List of 3-5 relevant priorities based on detected domains
        """
        jd_lower = jd_text.lower()
        priorities = []
        domain_scores = {}

        # Score each domain based on keyword matches
        for domain, templates in self.PRIORITY_TEMPLATES.items():
            score = 0
            keywords = self._get_domain_keywords(domain)
            for keyword in keywords:
                if keyword in jd_lower:
                    score += jd_lower.count(keyword)
            if score > 0:
                domain_scores[domain] = score

        # Sort domains by score and select top 3-5
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        top_domains = [domain for domain, _ in sorted_domains[:5]]

        # Pick priorities from top domains
        for domain in top_domains[:3]:
            # Select 1-2 priorities per domain
            domain_priorities = self.PRIORITY_TEMPLATES[domain]
            priorities.extend(domain_priorities[:2])

        # Limit to 3-5 priorities
        if len(priorities) > 5:
            priorities = priorities[:5]
        elif len(priorities) < 3:
            # Add generic priorities if not enough found
            priorities.extend([
                "Strategic planning and execution",
                "Cross-functional collaboration",
                "Data-driven decision making"
            ])
            priorities = priorities[:5]

        return priorities

    async def infer_tone(self, jd_text: str) -> str:
        """
        Infer tone based on keyword patterns.

        Args:
            jd_text: The job description text

        Returns:
            Tone category with highest keyword match score
        """
        jd_lower = jd_text.lower()
        tone_scores = {}

        # Score each tone based on keyword matches
        for tone, keywords in self.TONE_PATTERNS.items():
            score = 0
            for keyword in keywords:
                if keyword in jd_lower:
                    score += jd_lower.count(keyword)
            if score > 0:
                tone_scores[tone] = score

        if not tone_scores:
            return 'formal_corporate'  # Default tone

        # Return tone with highest score
        return max(tone_scores.items(), key=lambda x: x[1])[0]

    async def generate_text(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Generate generic text response.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate (ignored in mock)

        Returns:
            Simple acknowledgment response
        """
        return "This is a mock LLM response for development purposes."

    def _get_domain_keywords(self, domain: str) -> List[str]:
        """
        Get keywords associated with a domain for matching.

        Args:
            domain: The domain name

        Returns:
            List of keywords associated with the domain
        """
        keyword_map = {
            'ai_governance': ['ai governance', 'ai ethics', 'responsible ai', 'model governance', 'ai policy'],
            'data_governance': ['data governance', 'data steward', 'data quality', 'metadata', 'data lineage', 'data catalog'],
            'cloud': ['cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'infrastructure', 'devops'],
            'ai_ml': ['machine learning', 'ml', 'ai', 'artificial intelligence', 'model', 'neural'],
            'product': ['product', 'roadmap', 'user experience', 'ux', 'customer', 'feature'],
            'consulting': ['consulting', 'consultant', 'client', 'advisory', 'engagement'],
            'data': ['data', 'analytics', 'insights', 'business intelligence', 'bi', 'metrics'],
            'security': ['security', 'cybersecurity', 'threat', 'vulnerability', 'privacy'],
            'leadership': ['leadership', 'manager', 'director', 'vp', 'lead', 'team', 'people'],
            'research': ['research', 'phd', 'publication', 'academic', 'experiment', 'study'],
            'engineering': ['engineering', 'software', 'development', 'architecture', 'code']
        }
        return keyword_map.get(domain, [])

    # Cover letter greeting templates by tone
    GREETING_TEMPLATES = {
        'formal_corporate': {
            'with_company': "Dear {company} Hiring Team,",
            'with_referral': "Dear {referral_name},",
            'default': "Dear Hiring Team,"
        },
        'startup_casual': {
            'with_company': "Hello {company} Team,",
            'with_referral': "Hi {referral_name},",
            'default': "Hello!"
        },
        'consulting_professional': {
            'with_company': "Dear {company} Talent Acquisition Team,",
            'with_referral': "Dear {referral_name},",
            'default': "Dear Hiring Team,"
        },
        'mission_driven': {
            'with_company': "Dear {company} Team,",
            'with_referral': "Dear {referral_name},",
            'default': "Dear Hiring Team,"
        },
        'technical_precise': {
            'with_company': "Dear {company} Engineering Team,",
            'with_referral': "Dear {referral_name},",
            'default': "Dear Hiring Team,"
        },
        'academic_research': {
            'with_company': "Dear {company} Search Committee,",
            'with_referral': "Dear {referral_name},",
            'default': "Dear Search Committee,"
        }
    }

    # Closing templates by tone
    CLOSING_TEMPLATES = {
        'formal_corporate': "Sincerely,",
        'startup_casual': "Best,",
        'consulting_professional': "Best regards,",
        'mission_driven': "With enthusiasm,",
        'technical_precise': "Best regards,",
        'academic_research': "Respectfully,"
    }

    async def generate_cover_letter(
        self,
        outline: Dict,
        job_context: Dict,
        company_context: Dict,
        tone: str,
        user_name: str,
        max_words: int = 300
    ) -> str:
        """
        Generate cover letter from structured outline using templates.

        Args:
            outline: Dict with intro/value_proposition/alignment/call_to_action
            job_context: Job details (title, priorities, skills)
            company_context: Company details (name, initiatives, culture)
            tone: Target tone style
            user_name: User's full name for signature
            max_words: Target word count (advisory in mock)

        Returns:
            Complete cover letter text
        """
        # Near the start of the method, add:
        context_notes = company_context.get('context_notes') if company_context else None
        # For MockLLM, we acknowledge but don't need to modify behavior
        # Real LLM implementations would use this in their prompts

        # Build cover letter body from outline
        # Note: Greeting and closing are added by the output generators (DOCX/TXT),
        # so we only return the body content here to avoid duplication.
        intro = outline.get('introduction', '')
        value_prop = outline.get('value_proposition', '')
        alignment = outline.get('alignment', '')
        call_to_action = outline.get('call_to_action', '')

        # Compose the cover letter body (no greeting/closing - added by output generators)
        cover_letter_parts = [
            intro,
            "",
            value_prop,
            "",
            alignment,
            "",
            call_to_action,
        ]

        return "\n".join(cover_letter_parts)

    # Banned phrase replacements for mock revision
    PHRASE_REPLACEMENTS = {
        "i am writing to express my interest": "My background in {skill} aligns well with",
        "i am excited to apply for": "The {title} role presents an opportunity to apply my expertise in",
        "i am excited to apply": "This role offers a compelling opportunity to leverage my experience in",
        "i believe i would be a great fit": "My experience demonstrates strong alignment with",
        "i am confident i would be a great fit": "My track record shows clear alignment with",
        "i am confident that": "My experience indicates that",
        "please find attached": "I have included",
        "i am the perfect candidate": "My qualifications position me well for",
        "i look forward to hearing from you": "I welcome the opportunity to discuss this further",
        "please do not hesitate to contact me": "I am available to discuss at your convenience",
        "i am available at your convenience": "I am available to connect at a time that works for you",
        "per your job description": "Based on the role requirements",
        "as listed in the posting": "As outlined in the position",
        "your requirements state": "The role requirements indicate",
        "dear hiring manager": "Dear {company} Team",
        "i am very interested in": "I am drawn to",
        "i came across this position": "This position caught my attention because",
        "passionate": "committed to",
        "passion for": "dedication to",
        "dynamic": "adaptable",
        "motivated": "driven by results",
        "driven": "focused",
        "fast-paced": "high-velocity",
        "results-oriented": "outcome-focused",
        "proven track record": "demonstrated history",
        "team player": "collaborative professional",
        "detail-oriented": "meticulous",
        "self-starter": "proactive",
        "think outside the box": "approach problems creatively",
        "go-getter": "proactive achiever",
        "hard worker": "dedicated professional",
        "leverage": "utilize",
        "synergy": "collaboration",
        "best-in-class": "industry-leading",
        "world-class": "exceptional",
        "cutting-edge": "innovative",
        "innovative solutions": "effective solutions",
        "hit the ground running": "contribute immediately",
        "dynamic environment": "evolving environment",
    }

    async def revise_cover_letter(
        self,
        current_draft: str,
        critic_feedback: Dict,
        job_context: Dict,
        company_context: Dict,
        tone: str,
        user_name: str,
        max_words: int = 300
    ) -> str:
        """
        Revise a cover letter draft based on critic feedback.

        For MockLLM, this performs simple text replacements to address
        banned phrase issues while maintaining the overall structure.

        Args:
            current_draft: The current cover letter text to revise
            critic_feedback: Dict containing issues and suggestions
            job_context: Job details (title, priorities, skills)
            company_context: Company details (name, initiatives, culture)
            tone: Target tone style
            user_name: User's full name for signature
            max_words: Target word count (advisory in mock)

        Returns:
            Revised cover letter text
        """
        import re

        revised = current_draft
        company_name = company_context.get('name', 'the company')
        job_title = job_context.get('title', 'this role')
        skills_list = job_context.get('skills', ['this domain']) or ['this domain']
        top_skill = skills_list[0] if skills_list else 'this domain'

        # Get issues from feedback
        issues = critic_feedback.get('issues', [])

        # Process banned phrase issues
        for issue in issues:
            if isinstance(issue, dict) and issue.get('category') == 'banned_phrase':
                description = issue.get('description', '')
                # Extract the phrase from "Found banned phrase: 'phrase'"
                match = re.search(r"Found banned phrase: '([^']+)'", description)
                if match:
                    banned_phrase = match.group(1).lower()

                    # Find replacement
                    replacement = self.PHRASE_REPLACEMENTS.get(banned_phrase)
                    if replacement:
                        # Format replacement with context
                        replacement = replacement.format(
                            skill=top_skill,
                            title=job_title,
                            company=company_name
                        )

                        # Replace in text (case-insensitive)
                        pattern = re.compile(re.escape(banned_phrase), re.IGNORECASE)
                        revised = pattern.sub(replacement, revised)

        # Handle em-dash replacement
        revised = revised.replace('—', ' - ')

        # If ATS coverage is an issue, try to add missing keywords naturally
        improvement_suggestions = critic_feedback.get('improvement_suggestions', [])
        for suggestion in improvement_suggestions:
            if 'missing critical keywords' in suggestion.lower():
                # Extract keywords from suggestion
                match = re.search(r'keywords?: (.+)$', suggestion, re.IGNORECASE)
                if match:
                    keywords = [k.strip() for k in match.group(1).split(',')]
                    # Add keywords to the value proposition section if not present
                    for keyword in keywords[:2]:  # Limit to 2 keywords
                        if keyword.lower() not in revised.lower():
                            # Insert keyword mention before closing
                            closing_markers = ["Sincerely,", "Best,", "Best regards,", "Respectfully,", "With enthusiasm,"]
                            for marker in closing_markers:
                                if marker in revised:
                                    keyword_sentence = f"\n\nMy experience with {keyword} further supports my candidacy.\n\n"
                                    revised = revised.replace(marker, keyword_sentence + marker)
                                    break

        return revised

    async def extract_skills_from_jd(
        self,
        jd_text: str,
        taxonomy_skills: Optional[List[str]] = None,
        job_title: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mock LLM skill extraction using enhanced heuristics.

        Production implementation (ClaudeLLM) will use actual LLM reasoning.
        Mock uses keyword patterns and taxonomy as baseline.

        Args:
            jd_text: Full job description text
            taxonomy_skills: Skills found via taxonomy matching
            job_title: Extracted job title
            context: Dict with 'requirements' and 'responsibilities' lists

        Returns:
            Dict with extracted_skills, critical_skills, preferred_skills, domain_skills, confidence
        """
        import re
        jd_lower = jd_text.lower()

        # If taxonomy_skills not provided, extract them
        if taxonomy_skills is None:
            from services.job_parser import extract_skills_keywords
            taxonomy_skills = extract_skills_keywords(jd_text)

        # If context not provided, create a minimal one by parsing the JD
        if context is None:
            # Simple extraction of requirements/responsibilities from text
            lines = jd_text.split('\n')
            context = {
                'requirements': [line for line in lines if any(kw in line.lower() for kw in ['require', 'must', 'need', 'experience'])],
                'responsibilities': [line for line in lines if any(kw in line.lower() for kw in ['responsible', 'will', 'lead', 'manage'])]
            }

        # If job_title not provided, try to infer it
        if job_title is None:
            # Simple title extraction (first line or line with "engineer", "manager", etc.)
            title_keywords = ['engineer', 'manager', 'director', 'analyst', 'developer', 'scientist', 'architect']
            for line in jd_text.split('\n')[:10]:  # Check first 10 lines
                if any(kw in line.lower() for kw in title_keywords):
                    job_title = line.strip()
                    break
            if job_title is None:
                job_title = "Unknown Position"

        # Enhanced pattern matching for common skills not in taxonomy
        skill_patterns = {
            # Project Management
            r'\b(roadmap|roadmapping)\b': 'Roadmap Planning',
            r'\b(okr|objectives?\s+and\s+key\s+results?)\b': 'OKR Framework',
            r'\b(kpi|key\s+performance\s+indicators?)\b': 'KPI Management',
            r'\b(kpi\s+metrics?|metrics?\s+reporting)\b': 'KPI Reporting',

            # Business Analysis
            r'\b(requirements?\s+gathering|requirements?\s+elicitation)\b': 'Requirements Gathering',
            r'\b(user\s+stor(y|ies))\b': 'User Stories',
            r'\b(acceptance\s+criteria)\b': 'Acceptance Criteria',
            r'\b(process\s+mapping|process\s+flows?)\b': 'Process Mapping',
            r'\b(gap\s+analysis)\b': 'Gap Analysis',
            r'\b(use\s+cases?)\b': 'Use Cases',
            r'\b(functional\s+requirements?)\b': 'Functional Requirements',
            r'\b(system\s+implementation)\b': 'System Implementation',
            r'\b(platform\s+implementation)\b': 'Platform Implementation',

            # Data & Analytics
            r'\b(data\s+quality)\b': 'Data Quality',
            r'\b(data\s+lineage)\b': 'Data Lineage',
            r'\b(metadata)\b': 'Metadata Management',
            r'\b(master\s+data)\b': 'Master Data Management',
            r'\b(data\s+catalog)\b': 'Data Catalog',

            # Leadership & Soft Skills
            r'\b(stakeholder\s+management|stakeholder\s+engagement)\b': 'Stakeholder Management',
            r'\b(cross[- ]functional\s+collaboration|cross[- ]functional\s+teams?)\b': 'Cross-functional Collaboration',
            r'\b(executive\s+communication|c[- ]level\s+communication)\b': 'Executive Communication',
            r'\b(training\s+and\s+support|user\s+training)\b': 'Training & Support',

            # Domain
            r'\b(financial\s+services|banking|capital\s+markets)\b': 'Financial Services',
            r'\b(fintech|financial\s+technology)\b': 'FinTech',
            r'\b(regulatory\s+compliance|regulations?)\b': 'Regulatory Compliance',
            r'\b(investment\s+management|asset\s+management)\b': 'Investment Management',
        }

        extracted_skills = list(taxonomy_skills)  # Start with taxonomy matches

        # Pattern-based extraction
        for pattern, skill_name in skill_patterns.items():
            if re.search(pattern, jd_lower):
                if skill_name not in extracted_skills:
                    extracted_skills.append(skill_name)

        # Categorize by importance
        requirements_text = ' '.join(context.get('requirements', [])).lower() if context.get('requirements') else jd_lower

        critical_skills = []
        preferred_skills = []
        domain_skills = []

        critical_indicators = ['required', 'must have', 'essential', 'mandatory', 'minimum', 'need']
        preferred_indicators = ['preferred', 'nice to have', 'bonus', 'plus', 'ideal', 'desired']
        domain_keywords = ['financial services', 'fintech', 'healthcare', 'regulatory', 'compliance', 'investment', 'banking']

        for skill in extracted_skills:
            skill_lower = skill.lower()

            # Check for domain skills
            if any(kw in skill_lower for kw in domain_keywords):
                domain_skills.append(skill)

            # Check surrounding context for importance
            if skill_lower in requirements_text:
                # Find context around skill mention
                idx = requirements_text.find(skill_lower)
                context_window = requirements_text[max(0, idx-100):idx+100]

                is_critical = any(ind in context_window for ind in critical_indicators)
                is_preferred = any(ind in context_window for ind in preferred_indicators)

                if is_critical and not is_preferred:
                    critical_skills.append(skill)
                elif is_preferred:
                    preferred_skills.append(skill)
                else:
                    critical_skills.append(skill)  # Default to critical if in requirements
            elif skill_lower in jd_lower:
                preferred_skills.append(skill)  # Mentioned but not in requirements = preferred

        # Ensure lists don't exceed reasonable limits
        return {
            'extracted_skills': extracted_skills[:30],
            'critical_skills': critical_skills[:15],
            'preferred_skills': preferred_skills[:10],
            'domain_skills': domain_skills[:5],
            'confidence': 0.75
        }

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 2048
    ) -> Dict:
        """
        Mock JSON generation - returns a sensible response for skills categorization.

        For real LLM, this would parse the prompt and generate actual JSON.
        MockLLM returns a basic categorization structure.
        """
        # For skills formatting prompts, return a mock categorization
        if "categorize" in prompt.lower() and "skills" in prompt.lower():
            # Extract skills from prompt (they appear after "SKILLS TO CATEGORIZE:")
            skills_match = prompt.find("SKILLS TO CATEGORIZE:")
            if skills_match != -1:
                skills_section = prompt[skills_match:prompt.find("\n\nAVAILABLE")]
                # Simple extraction of comma-separated skills
                skills_line = skills_section.split("\n")[1] if "\n" in skills_section else ""
                skills = [s.strip() for s in skills_line.split(",") if s.strip()]

                # Use fallback categorization logic to build response
                return {"categories": self._mock_categorize_skills(skills)}

        # Default: return empty categories
        return {"categories": []}

    def _mock_categorize_skills(self, skills: List[str]) -> List[Dict]:
        """Mock skill categorization using keyword matching."""
        category_patterns = {
            "AI/ML": ["ai", "ml", "machine learning", "deep learning", "nlp", "llm",
                      "rag", "vector", "embedding", "prompt", "neural", "transformer",
                      "generative", "gpt", "claude", "artificial intelligence"],
            "Programming Languages & Frameworks": [
                "python", "sql", "r ", "java", "scala", "spark", "pandas",
                "numpy", "scikit", "tensorflow", "pytorch", "javascript", "typescript"
            ],
            "Data Engineering & Analytics": [
                "data", "etl", "pipeline", "warehouse", "lake", "hadoop", "kafka",
                "snowflake", "databricks", "dbt", "airflow", "analytics"
            ],
            "Cloud & Infrastructure": [
                "aws", "azure", "gcp", "cloud", "docker",
                "kubernetes", "terraform", "devops", "ci/cd"
            ],
            "Governance & Strategy": [
                "governance", "strategy", "compliance", "policy",
                "framework", "architecture", "leadership", "management"
            ],
            "Visualization & BI": [
                "tableau", "power bi", "looker", "dashboard",
                "visualization", "reporting", "qlik"
            ],
        }

        categorized: Dict[str, List[str]] = {}
        uncategorized: List[str] = []

        for skill in skills:
            skill_lower = skill.lower()
            matched = False

            for category, patterns in category_patterns.items():
                if any(pattern in skill_lower for pattern in patterns):
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(skill)
                    matched = True
                    break

            if not matched:
                uncategorized.append(skill)

        # Build response
        result = []
        for category_name, skill_list in categorized.items():
            result.append({
                "category_name": category_name,
                "skills": skill_list
            })

        if uncategorized:
            result.append({
                "category_name": "Other Technical Skills",
                "skills": uncategorized
            })

        return result
