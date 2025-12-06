"""
LLM Service Layer

Provides LLM implementations for job parsing and skill-gap analysis.
"""

from .base import BaseLLM
from .mock_llm import MockLLM

__all__ = ['BaseLLM', 'MockLLM']
