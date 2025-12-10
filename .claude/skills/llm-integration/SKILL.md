---
name: llm-integration
description: Integrate Claude and GPT-4o LLMs, manage prompts, handle responses, and implement critic loops. Use when working with LLM services, prompt templates, quality evaluation, or AI-powered features.
---

# LLM Integration for ETPS

## LLM Architecture
- Primary: Claude (via Anthropic API)
- Fallback: GPT-4o
- Embeddings: text-embedding-3-small (OpenAI)
- Mock for testing: backend/services/llm/mock_llm.py

## Key Files
```
backend/services/llm/
├── __init__.py      # create_llm() factory
├── base.py          # Abstract base class
├── mock_llm.py      # Testing mock (no API calls)
└── claude_llm.py    # Claude API implementation
```

## LLM Factory Pattern
```python
from services.llm import create_llm

# Auto-selects based on ANTHROPIC_API_KEY env var
llm = create_llm()  # Returns ClaudeLLM or MockLLM

# Use in async context
response = await llm.generate(prompt="...", max_tokens=500)
```

## Critic Loop Pattern
The critic service evaluates output quality:
```python
from services.critic import evaluate_content

result = await evaluate_content(
    content=generated_text,
    content_type="resume",  # or "cover_letter"
    job_profile=job_profile,
    llm=llm
)
# Returns: CriticResult with scores, issues, suggestions
```

## Quality Dimensions
- **ATS Score**: Keyword matching, format compatibility
- **Style**: Follows docs/cover_letter_style_guide.md
- **Truthfulness**: No hallucinations, matches source data
- **Tone**: Professional, confident, not sycophantic

## Testing with Mock LLM
```python
from services.llm.mock_llm import MockLLM

@pytest.mark.asyncio
async def test_with_mock():
    mock_llm = MockLLM()
    result = await my_service(llm=mock_llm)
    # Mock returns template-based responses
```

## Environment Variables
- `ANTHROPIC_API_KEY` - Enables Claude (required for production)
- `OPENAI_API_KEY` - For embeddings

## Best Practices
1. Always use async/await for LLM calls
2. Pass LLM instance as parameter (dependency injection)
3. Use MockLLM in tests, never call real APIs
4. Implement retry logic for API failures
5. Log prompts/responses for debugging (not in prod)
6. Set appropriate max_tokens to control cost
