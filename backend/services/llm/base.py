"""
Base LLM Interface

Abstract base class for LLM implementations used in ETPS job parsing
and skill-gap analysis.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseLLM(ABC):
    """
    Abstract base class for LLM implementations.

    Defines the interface for LLM-based operations including job description
    analysis, tone inference, and general text generation.
    """

    @abstractmethod
    async def generate_core_priorities(self, jd_text: str, context: Dict) -> List[str]:
        """
        Extract and generate core priorities from a job description.

        Args:
            jd_text: The job description text
            context: Additional context (e.g., company info, parsed requirements)

        Returns:
            List of 3-5 core priorities/themes extracted from the JD

        Example:
            ["AI governance and ethics framework development",
             "Cross-functional stakeholder management",
             "Technical AI/ML understanding for oversight"]
        """
        pass

    @abstractmethod
    async def infer_tone(self, jd_text: str) -> str:
        """
        Infer the tone and style of the job description.

        Args:
            jd_text: The job description text

        Returns:
            Tone category string (e.g., "formal", "startup", "mission-driven")

        Example tone categories:
            - "formal_corporate"
            - "startup_casual"
            - "mission_driven"
            - "technical_precise"
            - "consulting_professional"
        """
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Generate text based on a prompt.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
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
        Generate cover letter from structured outline.

        Args:
            outline: Dict with intro/value_proposition/alignment/call_to_action
            job_context: Job details (title, priorities, skills)
            company_context: Company details (name, initiatives, culture)
            tone: Target tone style
            user_name: User's full name for signature
            max_words: Target word count

        Returns:
            Complete cover letter text
        """
        pass
