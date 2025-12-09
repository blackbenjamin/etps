"""
Claude LLM Implementation

Uses the Anthropic Claude API for high-quality cover letter generation.
Implements the style guide rules directly in the prompts for coherent output.
"""

import os
import logging
from typing import List, Dict

import anthropic

from .base import BaseLLM


logger = logging.getLogger(__name__)


# Cover letter style guide rules embedded in system prompt
COVER_LETTER_SYSTEM_PROMPT = """You are an expert cover letter writer for Benjamin Black, a senior consultant with expertise in data strategy, technology consulting, and enterprise transformation.

## CRITICAL ANTI-HALLUCINATION RULES (READ FIRST):
- ONLY mention skills, technologies, or domains that appear in the job requirements provided below
- DO NOT assume the job requires AI, machine learning, or any technology not explicitly mentioned
- If the job is about "Data Governance" - focus on governance frameworks, policies, data quality, metadata management, and Collibra
- DO NOT conflate "Data Governance" with "AI Governance" - these are different domains
- Test every statement: "Is this ACTUALLY mentioned in the job description?" If not, do not include it.
- The job requirements are your source of truth - not your assumptions about what the role might involve

## CRITICAL RULES - VIOLATIONS WILL BE REJECTED

### Banned Phrases (NEVER use these):
- "I am writing to express my interest..."
- "I am excited to apply for..."
- "I believe I would be a great fit..."
- "I am confident that..."
- "passionate" / "passion for"
- "dynamic" / "driven" / "motivated"
- "team player" / "self-starter" / "detail-oriented"
- "I look forward to hearing from you"
- "Please do not hesitate to contact me"
- "Per your job description..."
- "proven track record"

### Banned Punctuation:
- NEVER use em-dashes (--). Use commas, parentheses, or separate sentences instead.
- No excessive exclamation points

### Writing Style:
- Be direct and confident without hedging
- Use active voice ("I led" not "I was responsible for")
- Show, don't tell - use concrete examples with outcomes
- Vary sentence length (mix short punchy with longer explanatory)
- AVOID CONTRACTIONS: Use "I would" not "I'd", "I am" not "I'm", "I have" not "I've"
- Close with a direct professional ask for a meeting/discussion

## LOGICAL COHERENCE RULES (CRITICAL):
- Every bullet and sentence must DIRECTLY relate to the target role's core responsibilities
- DO NOT mention random tools (Postman, VS Code, GitHub) unless they are specifically relevant to the job requirements
- Each bullet must have a clear logical connection: [Context] → [Action] → [Outcome that matters for this role]
- Avoid vague phrases like "demonstrating technical fluency" - instead state the specific capability that matters
- If the role is about Data Governance, bullets should be about governance frameworks, data quality, metadata, policies - NOT generic technical tools
- Test each sentence: "Does this directly address what the hiring manager cares about for THIS specific role?"

## STRUCTURE (Target: 250-275 words - BE CONCISE)

PARAGRAPH 1 - HOOK + POSITIONING (2-3 sentences, prose):
- Name the specific role
- State unique positioning angle
- Signal domain relevance immediately

PARAGRAPH 2 - EXPERIENCE ALIGNMENT (use 2-3 bullets for skimmability):
- Open with ONE brief intro sentence, then use bullet points
- Each bullet: one key qualification DIRECTLY relevant to the role's requirements
- Name specific companies and roles for credibility
- Each bullet should clearly connect to a job requirement
- Keep bullets concise (one line each, ~20-25 words max)
- End each bullet with a period

PARAGRAPH 3 - DIFFERENTIATOR (2-3 sentences, prose - keep tight):
- Highlight ONE distinctive capability that sets you apart
- Connect it to what THIS role specifically needs
- Show strategic thinking, not just execution

PARAGRAPH 4 - COMPANY FIT + CLOSE (2 sentences only):
- Reference company mission/approach specifically
- END WITH DIRECT ASK: "I would welcome the opportunity to discuss how my background can support [Company]'s [specific goal]."

## ACHIEVEMENT FRAMING
Pattern: "At [Company], I [action verb] [what] for [stakeholder], [outcome/impact relevant to target role]."
Example: "At Kessel Run, I led enterprise data governance research for the CIO/CDO, establishing frameworks that informed organization-wide data management policies."

## Strong Action Verbs (prefer these):
Led, Built, Developed, Designed, Created, Supported, Strengthened, Modernized, Enabled, Accelerated, Translated, Delivered, Established, Defined

## Weak Verbs (avoid):
Assisted, Participated, Contributed to, Was responsible for, Played a role in, Demonstrated
"""


class ClaudeLLM(BaseLLM):
    """
    Claude API LLM implementation for high-quality cover letter generation.

    Uses Claude's understanding of context and style to generate cohesive,
    non-repetitive cover letters that follow the style guide.
    """

    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude LLM.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-sonnet-4-20250514)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info(f"Initialized ClaudeLLM with model {model}")

    async def generate_core_priorities(self, jd_text: str, context: Dict) -> List[str]:
        """Extract core priorities from a job description using Claude."""
        prompt = f"""Analyze this job description and extract 3-5 core priorities or themes that the ideal candidate should address.

Job Description:
{jd_text}

Return only a JSON array of 3-5 priority strings, each describing a key theme. Example:
["AI governance and ethics framework development", "Cross-functional stakeholder management", "Technical AI/ML understanding for oversight"]
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response as JSON array
        import json
        try:
            return json.loads(message.content[0].text)
        except json.JSONDecodeError:
            # Fallback: split by newlines if not valid JSON
            lines = message.content[0].text.strip().split('\n')
            return [line.strip('- "\'') for line in lines if line.strip()][:5]

    async def infer_tone(self, jd_text: str) -> str:
        """Infer the tone/style of text using Claude."""
        prompt = f"""Classify the tone of this text into exactly one of these categories:
- formal_corporate
- startup_casual
- consulting_professional
- mission_driven
- technical_precise
- academic_research

Text:
{jd_text[:2000]}

Return only the category name, nothing else."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )

        tone = message.content[0].text.strip().lower()
        valid_tones = ['formal_corporate', 'startup_casual', 'consulting_professional',
                       'mission_driven', 'technical_precise', 'academic_research']
        return tone if tone in valid_tones else 'formal_corporate'

    async def generate_text(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate generic text using Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

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
        Generate a complete, cohesive cover letter using Claude.

        Unlike the heuristic approach, Claude sees all context at once and
        generates a flowing narrative without repetition.
        """
        # Build the user prompt with all context
        company_name = company_context.get('name') or 'the company'
        job_title = job_context.get('title') or 'the position'

        # Format skills and priorities
        skills = job_context.get('skills', [])
        priorities = job_context.get('priorities', [])
        must_have = job_context.get('must_have', [])

        # Format company info
        initiatives = company_context.get('initiatives') or ''
        culture = company_context.get('culture') or []
        referral_name = company_context.get('referral_name')
        context_notes = company_context.get('context_notes') or ''
        examples_context = company_context.get('examples_context') or ''

        # Build evidence from outline (these come from resume bullets)
        intro_context = outline.get('introduction', '')
        value_prop = outline.get('value_proposition', '')
        alignment = outline.get('alignment', '')

        user_prompt = f"""Write a cover letter for Benjamin Black applying to the {job_title} position at {company_name}.

## TARGET TONE: {tone}

## JOB REQUIREMENTS:
- Key Skills Needed: {', '.join(skills[:10]) if skills else 'See priorities below'}
- Core Priorities: {', '.join(priorities[:5]) if priorities else 'General alignment with role'}
- Must-Have Capabilities: {', '.join(must_have[:5]) if must_have else 'See skills above'}

## COMPANY CONTEXT:
- Company: {company_name}
- Known Initiatives: {initiatives if initiatives else 'Research and reference their specific mission'}
- Culture Signals: {', '.join(culture) if culture else 'Professional environment'}

## BENJAMIN'S RELEVANT BACKGROUND (use this to write authentic content):
{value_prop}

{alignment}

## ADDITIONAL CONTEXT:
{f'Referral: This application is via referral from {referral_name}. Mention this naturally in the opening.' if referral_name else ''}
{f'User Notes: {context_notes}' if context_notes else ''}

{f'## EXAMPLE APPROVED PARAGRAPHS (for style reference):{chr(10)}{examples_context}' if examples_context else ''}

## INSTRUCTIONS:
1. Write EXACTLY 250-275 words (not more!) across 4 tight paragraphs
2. DO NOT repeat the same skill or achievement in multiple paragraphs
3. DO NOT use any banned phrases from the system prompt
4. DO NOT use em-dashes (--), use commas or periods instead
5. DO NOT use contractions (use "I would" not "I'd", "I am" not "I'm")
6. DO NOT mention generic tools (Postman, VS Code, GitHub) unless the job specifically requires them
7. Every bullet must directly connect to a specific job requirement - no filler content
8. Be specific about companies and outcomes that matter for THIS role
9. Use 2-3 bullet points in paragraph 2 (end each with a period, keep under 25 words each)
10. End with a direct ask: "I would welcome the opportunity to discuss..."
11. QUALITY CHECK: Before finalizing, verify each bullet answers "Why does this matter for the Data Governance Solution Lead role?"

Return ONLY the cover letter body (no greeting like "Dear..." or signature like "Sincerely"). Those will be added separately."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=COVER_LETTER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )

        cover_letter = message.content[0].text.strip()

        # Post-process: remove any em-dashes that slipped through
        cover_letter = cover_letter.replace('—', ', ')
        cover_letter = cover_letter.replace('--', ', ')

        logger.info(f"Generated cover letter with Claude: {len(cover_letter.split())} words")
        return cover_letter

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
        Revise a cover letter based on critic feedback using Claude.
        """
        # Format issues for the prompt
        issues = critic_feedback.get('issues', [])
        suggestions = critic_feedback.get('improvement_suggestions', [])
        quality_score = critic_feedback.get('quality_score', 0)

        issues_text = '\n'.join([
            f"- [{issue.get('severity', 'unknown').upper()}] {issue.get('description', '')}: {issue.get('suggestion', '')}"
            for issue in issues
        ])

        suggestions_text = '\n'.join([f"- {s}" for s in suggestions])

        user_prompt = f"""Revise this cover letter to fix the identified issues.

## CURRENT DRAFT (Quality Score: {quality_score}/100):
{current_draft}

## ISSUES TO FIX:
{issues_text}

## IMPROVEMENT SUGGESTIONS:
{suggestions_text}

## INSTRUCTIONS:
1. Fix ALL identified issues, especially banned phrases
2. Remove any em-dashes (--) and replace with commas or periods
3. DO NOT use contractions (use "I would" not "I'd", "I am" not "I'm")
4. Maintain the overall structure and meaning
5. Keep it EXACTLY 250-275 words (not more!)
6. Remove any generic tool mentions (Postman, VS Code, GitHub) unless job-specific
7. Ensure every bullet directly relates to the target role's requirements
8. Ensure no repetition of skills/achievements across paragraphs
9. End with a direct ask: "I would welcome the opportunity to discuss..."

Return ONLY the revised cover letter body (no greeting or signature)."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=COVER_LETTER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )

        revised = message.content[0].text.strip()

        # Post-process: remove any em-dashes
        revised = revised.replace('—', ', ')
        revised = revised.replace('--', ', ')

        logger.info(f"Revised cover letter with Claude: {len(revised.split())} words")
        return revised
