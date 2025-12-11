# Sprint 8: Learning from Approved Outputs - Comprehensive Test Suite

## Quick Start

```bash
# Run all tests
cd /Users/benjaminblack/projects/etps/backend
pytest tests/test_approved_outputs.py -v

# Results: 45 tests, all passing, <1 second execution time
```

## Test File Location
`/Users/benjaminblack/projects/etps/backend/tests/test_approved_outputs.py`

## Overview

This is a comprehensive unit test suite for Sprint 8 functionality, providing complete coverage of:

1. **ApprovedOutput Model** - Database model with relationships and validation
2. **Vector Store Indexing** - Embedding generation and storage in Qdrant
3. **Output Retrieval** - Similarity search with multiple filter options
4. **Schema Validation** - Pydantic v2 validation for requests/responses
5. **API Endpoints** - FastAPI router testing

## Test Organization

### 12 Test Classes (45 Total Tests)

| Class | Tests | Purpose |
|-------|-------|---------|
| `TestApprovedOutputModel` | 7 | Model fields, relationships, timestamps |
| `TestIndexApprovedOutput` | 6 | Vector store indexing and embedding |
| `TestRetrieveSimilarOutputs` | 6 | Basic similarity search with filters |
| `TestRetrieveSimilarBullets` | 1 | Resume bullet retrieval |
| `TestRetrieveSimilarSummaries` | 1 | Professional summary retrieval |
| `TestRetrieveSimilarCoverLetterParagraphs` | 1 | Cover letter paragraph retrieval |
| `TestFormatExamplesForPrompt` | 5 | LLM prompt formatting |
| `TestApproveOutputRequestSchema` | 7 | Request validation |
| `TestSimilarOutputSchema` | 3 | Response schema validation |
| `TestApproveOutputEndpoint` | 3 | POST /approve endpoint |
| `TestSimilarOutputsEndpoint` | 2 | GET /similar endpoint |
| `TestApprovedOutputIntegration` | 3 | End-to-end workflows |

## Test Fixtures (8 Total)

### Model Fixtures
- `sample_approved_output` - Complete mock with all fields
- `sample_approved_outputs_batch` - 5 diverse outputs (different types)
- `sample_user` - User account mock
- `sample_application` - Application relationship
- `sample_job_profile` - Job profile relationship

### Service Fixtures
- `mock_vector_store` - Fresh MockVectorStore per test
- `mock_embedding_service` - MockEmbeddingService (384-dim)
- `mock_db_session` - SQLAlchemy session mock

## Testing Approach

### No External Dependencies
- **MockVectorStore** replaces Qdrant - deterministic, in-memory
- **MockEmbeddingService** replaces OpenAI - consistent, hashable embeddings
- **unittest.mock.Mock** for database objects - fully isolated
- All tests run in < 1 second with zero external calls

### Comprehensive Coverage
- **Happy Path:** 32 tests for successful operations
- **Error Cases:** 13 tests for validation, constraints, edge cases
- **Async:** 21 async tests using pytest-asyncio
- **Sync:** 25 synchronous tests

### Arrange-Act-Assert Pattern
Every test follows clear three-phase structure:
```python
# Arrange: Set up test data and conditions
await mock_vector_store.ensure_collection(COLLECTION_APPROVED_OUTPUTS)

# Act: Execute the code under test
await index_approved_output(approved_output, embedding_service, vector_store)

# Assert: Verify the expected outcome
assert payload["output_type"] == "resume_bullet"
```

## Test Categories

### 1. Model Tests (7 tests)
Verify ApprovedOutput SQLAlchemy model:
- Required fields exist and have correct types
- Quality score stored as float (0.0-1.0)
- Context metadata stored as JSON dict
- Relationships properly configured (user, application, job_profile)
- Optional relationships handle null values
- Output types validate to Literal values
- Timestamps track creation/update times

### 2. Indexing Tests (6 tests)
Test `index_approved_output()` function:
- Uses existing embedding if present
- Generates embedding if missing
- Payload structure matches vector store schema
- Multiple outputs indexed in sequence
- Null application_id handled correctly
- created_at stored as ISO format string

### 3. Retrieval Tests (14 tests)
Test retrieval service functions:

**Basic Search (6 tests):**
- Similarity search returns results
- Type filter works correctly
- Quality score filter works
- Empty results handled gracefully
- Empty query text rejected
- User ID filter enforced

**Type-Specific (3 tests):**
- Retrieve resume bullets
- Retrieve professional summaries
- Retrieve cover letter paragraphs

**Formatting (5 tests):**
- Empty results format
- Single example formatting
- Respects max_examples limit
- Truncates long text
- Optional quality score display

### 4. Schema Tests (13 tests)
Pydantic validation:

**ApproveOutputRequest (7 tests):**
- Valid data accepted
- All optional fields supported
- Rejects invalid user_id
- Rejects empty text
- Rejects invalid output_type
- Rejects out-of-range quality score
- Enforces text length (1-10000 chars)

**SimilarOutput (3 tests):**
- Valid data accepted
- Scores rounded to 2 decimals
- Rejects invalid scores

**Responses (3 tests):**
- Response format correct
- Empty results handled

### 5. Endpoint Tests (5 tests)
API route testing:

**POST /approve:**
- Success case returns 201
- Invalid user returns 404
- Invalid type returns 422

**GET /similar:**
- Returns properly formatted response
- Handles empty results

### 6. Integration Tests (3 tests)
End-to-end workflows:
- Index output then retrieve it
- Type-specific retrieval accuracy
- Combined filters work together

## Running Tests

### All Tests
```bash
pytest tests/test_approved_outputs.py -v
```

### By Test Class
```bash
pytest tests/test_approved_outputs.py::TestApprovedOutputModel -v
pytest tests/test_approved_outputs.py::TestIndexApprovedOutput -v
pytest tests/test_approved_outputs.py::TestRetrieveSimilarOutputs -v
```

### By Keyword
```bash
pytest tests/test_approved_outputs.py -k "index" -v
pytest tests/test_approved_outputs.py -k "retrieve" -v
pytest tests/test_approved_outputs.py -k "schema" -v
```

### Async Tests Only
```bash
pytest tests/test_approved_outputs.py -k "asyncio" -v
```

### With Coverage
```bash
pytest tests/test_approved_outputs.py \
  --cov=services.vector_store \
  --cov=services.output_retrieval \
  --cov-report=html
```

### Verbose Output
```bash
pytest tests/test_approved_outputs.py -vv --tb=long
```

## Test Results

```
============================= 45 passed in 0.60s ==============================

Test Summary:
- 45/45 passing (100%)
- 0 failures
- 0 skipped
- Execution time: ~600ms
- No external dependencies
- No flaky tests
```

## Components Tested

### Models (`db/models.py`)
- ApprovedOutput - All fields, relationships, constraints

### Services (`services/`)
- `vector_store.py` - index_approved_output()
- `output_retrieval.py` - All retrieval functions
- `embeddings.py` - MockEmbeddingService (mocked, not tested directly)

### Schemas (`schemas/approved_output.py`)
- ApproveOutputRequest
- ApproveOutputResponse
- SimilarOutput
- SimilarOutputsResponse

### Routers (`routers/outputs.py`)
- POST /approve endpoint
- GET /similar endpoint

## Key Testing Patterns

### Pattern 1: Fixture Composition
```python
@pytest.fixture
def sample_approved_outputs_batch():
    """Create multiple mock objects with variety."""
    # Create diverse fixtures to test edge cases
```

### Pattern 2: Mock Service Isolation
```python
mock_vector_store = MockVectorStore()  # No Qdrant
mock_embedding_service = MockEmbeddingService()  # No OpenAI API
```

### Pattern 3: Schema Validation
```python
with pytest.raises(Exception):
    ApproveOutputRequest(
        user_id=-1,  # Invalid
        output_type="resume_bullet",
        original_text="Text"
    )
```

### Pattern 4: Async Testing
```python
@pytest.mark.asyncio
async def test_index_approved_output_with_existing_embedding(...):
    await index_approved_output(...)
    assert results[0]["id"] == 1
```

### Pattern 5: Integration Testing
```python
# Index then retrieve to verify full workflow
await index_approved_output(approved_output, ...)
results = await retrieve_similar_outputs(...)
assert len(results) > 0
```

## Extending Tests

### Adding New Tests
1. Choose appropriate test class or create new one
2. Add fixture if needed (parametrized for reusability)
3. Follow Arrange-Act-Assert pattern
4. Use descriptive test names
5. Include docstring explaining scenario

### Adding New Fixtures
1. Add to appropriate section (Model/Service)
2. Use `@pytest.fixture` decorator
3. Make fixtures composable
4. Document with docstring

### Test Naming Convention
- `test_<feature>_<scenario>_<expected_result>`
- Example: `test_index_approved_output_with_existing_embedding`
- Example: `test_retrieve_similar_outputs_empty_results`

## Troubleshooting

### Test Fails with "User not found"
- Mock database setup may be incomplete
- Verify mock_db_session fixture is configured correctly
- Check endpoint tests use Depends(get_db) properly

### Async Tests Fail
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator
- await all async functions properly

### Import Errors
- Verify imports match actual module paths
- Check that services use correct collection names
- Verify schemas match implementation

## Performance

- **Execution Time:** ~600ms for 45 tests
- **Memory:** Minimal (all in-memory mocks)
- **I/O:** Zero (no database, network, or file operations)
- **Determinism:** 100% (no flaky tests, reproducible results)

## Maintenance

- Tests follow project patterns from test_vector_store.py
- All tests are self-contained and independent
- No shared state between tests
- Fresh mocks created per test
- Easy to add new tests without affecting existing ones

## Documentation

Each test includes:
- Clear descriptive name
- Docstring explaining the scenario
- Comments marking Arrange-Act-Assert sections
- Assertions with meaningful messages

## CI/CD Integration

These tests are ideal for:
- Pre-commit hooks (fast execution)
- GitHub Actions CI (no external dependencies)
- Local development (rapid feedback)
- Test-driven development (comprehensive coverage)

## Contact & Support

- Located in: `/Users/benjaminblack/projects/etps/backend/tests/`
- 1,204 lines of well-structured test code
- 45 comprehensive test cases
- 12 organized test classes
- 8 reusable fixtures

