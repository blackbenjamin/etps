"""
Mock LLM Implementation

Heuristic-based mock LLM for development and testing without API calls.
Returns realistic responses based on keyword detection and pattern matching.
"""

from typing import List, Dict
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
        'governance': [
            "AI governance framework development and implementation",
            "Policy and compliance oversight for AI systems",
            "Risk management and ethical AI practices",
            "Stakeholder alignment on AI ethics standards"
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
            'governance': ['governance', 'policy', 'ethics', 'compliance', 'risk', 'regulation'],
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

        # Get greeting template
        greeting_templates = self.GREETING_TEMPLATES.get(
            tone, self.GREETING_TEMPLATES['formal_corporate']
        )

        # Determine greeting based on context
        company_name = company_context.get('name')
        referral_name = company_context.get('referral_name')

        if referral_name:
            greeting = greeting_templates['with_referral'].format(
                referral_name=referral_name
            )
        elif company_name:
            greeting = greeting_templates['with_company'].format(
                company=company_name
            )
        else:
            greeting = greeting_templates['default']

        # Get closing
        closing = self.CLOSING_TEMPLATES.get(tone, "Sincerely,")

        # Build cover letter body from outline
        intro = outline.get('introduction', '')
        value_prop = outline.get('value_proposition', '')
        alignment = outline.get('alignment', '')
        call_to_action = outline.get('call_to_action', '')

        # Compose the cover letter
        cover_letter_parts = [
            greeting,
            "",
            intro,
            "",
            value_prop,
            "",
            alignment,
            "",
            call_to_action,
            "",
            closing,
            user_name
        ]

        return "\n".join(cover_letter_parts)
