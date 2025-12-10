---
name: python-testing
description: Write pytest tests with fixtures, mocking, and async support. Use when writing unit tests, test files, test fixtures, or improving test coverage in backend/tests/.
---

# Python Testing with Pytest

## ETPS Test Structure
- Tests live in `backend/tests/test_*.py`
- Use `pytest` with `pytest-asyncio` for async code
- Mock LLM: `from services.llm.mock_llm import MockLLM`
- Current test count: 700+ passing

## Test Pattern
```python
import pytest
from services.llm.mock_llm import MockLLM

@pytest.mark.asyncio
async def test_my_function():
    mock_llm = MockLLM()
    result = await some_async_function(llm=mock_llm)
    assert result == expected
```

## Running Tests
```bash
cd backend
python -m pytest -v                    # All tests
python -m pytest tests/test_file.py -v # Specific file
python -m pytest --tb=long             # Full tracebacks
python -m pytest -k "keyword"          # Filter by name
```

## Key Test Files
- `test_pagination_allocation.py` - Pagination service
- `test_bullet_rewriter.py` - Bullet operations
- `test_critic.py` - Quality evaluation
- `test_skill_gap.py` - Skill analysis
- `test_text_output.py` - Resume/cover letter text output
- `test_security.py` - Security tests

## Mocking Patterns
```python
# Mock LLM
from services.llm.mock_llm import MockLLM
mock_llm = MockLLM()

# Mock database session
from unittest.mock import MagicMock
mock_db = MagicMock()
```

## Best Practices
1. All tests must pass before commits
2. Use fixtures for shared setup
3. Mock external services (LLM, vector store, APIs)
4. Test async code with @pytest.mark.asyncio
5. Use descriptive assertion messages
6. Test edge cases and error conditions
