# Contributing to ETPS

Thank you for your interest in ETPS! This is a portfolio project demonstrating AI-powered resume and cover letter tailoring. Contributions and feedback are welcome.

## About This Project

ETPS is primarily a **portfolio/demonstration project**. While contributions are welcome, please note:
- Feature requests may be selectively accepted based on project goals
- The project demonstrates specific AI engineering patterns
- Major architectural changes would need discussion first

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker** (optional, for local Qdrant)
- **API Keys**:
  - Anthropic API key (for Claude)
  - OpenAI API key (for embeddings)

### Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/etps.git
cd etps
```

#### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY=your_key_here
# - OPENAI_API_KEY=your_key_here

# Run backend
uvicorn main:app --reload --port 8000
```

The backend will be available at http://localhost:8000

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
# Edit .env.local:
# - NEXT_PUBLIC_API_URL=http://localhost:8000
# - NEXT_PUBLIC_USER_NAME=Your Name

# Run frontend
npm run dev
```

The frontend will be available at http://localhost:3000

#### 4. Vector Store (Optional)

For full semantic search functionality:

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or use Qdrant Cloud (free tier available)
```

### Running Tests

```bash
cd backend
pytest -v
# Target: 711+ tests passing
```

For specific test files:
```bash
pytest tests/test_resume_tailor.py -v
pytest tests/test_security.py -v
```

## Code Style

### Python (Backend)
- Follow patterns in existing `backend/services/` files
- Use type hints
- Use Pydantic for schemas
- Async functions for LLM/IO operations

### TypeScript (Frontend)
- Follow patterns in `frontend/src/components/`
- Use TypeScript interfaces for props
- Use shadcn/ui components
- Use TanStack Query for API calls

### Documentation
- Update relevant docs when making changes
- Use markdown with proper formatting
- Keep line length reasonable (~80 chars)

## Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Run tests**: `cd backend && pytest -v`
5. **Commit with clear message**: `git commit -m "feat: add your feature"`
6. **Push to your fork**: `git push origin feature/your-feature`
7. **Open a Pull Request**

### Commit Message Format

```
type: brief description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- refactor: Code refactoring
- test: Test additions/changes
- chore: Maintenance tasks
```

## Security

Before submitting:
- [ ] No hardcoded API keys or secrets
- [ ] Input validation on user-facing parameters
- [ ] No bare `except:` statements
- [ ] Database queries use ORM (no raw SQL)

See [CLAUDE.md](CLAUDE.md) for the full security checklist.

## Project Structure

```
etps/
├── backend/
│   ├── services/      # AI agents, vector search, embeddings
│   ├── routers/       # API endpoints
│   ├── schemas/       # Pydantic models
│   ├── db/            # Database models
│   └── tests/         # Test suite
├── frontend/
│   ├── src/app/       # Next.js pages
│   ├── src/components/# React components
│   ├── src/hooks/     # Custom hooks
│   └── src/lib/       # Utilities
├── docs/              # Documentation
└── .claude/           # Claude Code skills (AI-assisted dev workflow)
```

## Key Documentation

- [README.md](README.md) - Project overview
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md) - Database schema
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) - Sprint roadmap
- [CLAUDE.md](CLAUDE.md) - Development workflow and patterns

## Questions?

Open an issue for questions or discussions about the project.

---

Thank you for contributing!
