"""
LLM Service Layer

Provides LLM implementations for job parsing, skill-gap analysis, and cover letter generation.
"""

import os
import logging

from .base import BaseLLM
from .mock_llm import MockLLM

logger = logging.getLogger(__name__)

# Lazy import ClaudeLLM to avoid import errors if anthropic not installed
_claude_llm_class = None


def _get_claude_llm_class():
    """Lazily import ClaudeLLM to handle missing anthropic dependency."""
    global _claude_llm_class
    if _claude_llm_class is None:
        try:
            from .claude_llm import ClaudeLLM
            _claude_llm_class = ClaudeLLM
        except ImportError as e:
            logger.warning(f"ClaudeLLM not available: {e}")
            _claude_llm_class = False  # Mark as unavailable
    return _claude_llm_class if _claude_llm_class else None


def create_llm(use_mock: bool = False) -> BaseLLM:
    """
    Factory function to create the appropriate LLM instance.

    Automatically selects ClaudeLLM if ANTHROPIC_API_KEY is set,
    otherwise falls back to MockLLM.

    Args:
        use_mock: Force use of MockLLM even if API key is available

    Returns:
        BaseLLM instance (ClaudeLLM or MockLLM)
    """
    if use_mock:
        logger.info("Using MockLLM (forced)")
        return MockLLM()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        ClaudeLLM = _get_claude_llm_class()
        if ClaudeLLM:
            logger.info("Using ClaudeLLM with Anthropic API")
            return ClaudeLLM(api_key=api_key)
        else:
            logger.warning("ClaudeLLM unavailable, falling back to MockLLM")
            return MockLLM()
    else:
        logger.info("Using MockLLM (no ANTHROPIC_API_KEY set)")
        return MockLLM()


__all__ = ['BaseLLM', 'MockLLM', 'create_llm']
