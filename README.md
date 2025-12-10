# ETPS - Enterprise-Grade Talent Positioning System

An AI-Orchestrated Resume, Cover Letter, and Networking Intelligence Platform

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-711%20Passing-success)](backend/tests/)
[![Railway Deploy](https://img.shields.io/badge/Railway-Deployed-success)](https://railway.app)
[![Vercel Deploy](https://img.shields.io/badge/Vercel-Deployed-success)](https://etps.benjaminblack.consulting)

## About This Project

ETPS is an **open source portfolio project** demonstrating AI-powered document generation and intelligent job application assistance. It showcases:

- **LLM Orchestration** - Multi-agent architecture with Claude and GPT-4o
- **Semantic Search** - Vector embeddings with Qdrant for skill matching
- **Full-Stack Development** - FastAPI backend + Next.js frontend
- **Production Deployment** - Railway, Vercel, PostgreSQL, Qdrant Cloud

> **Note**: This is a portfolio/demonstration project. See [OPEN_SOURCE_STRATEGY.md](docs/OPEN_SOURCE_STRATEGY.md) for the rationale behind open-sourcing this work.

## Live Demo

**Production URL**: [https://etps.benjaminblack.consulting](https://etps.benjaminblack.consulting)

## What It Does

ETPS is a multi-agent, AI-driven system that:

- **Tailors resumes** to specific roles while preserving professional `.docx` formatting
- **Generates cover letters** with multiple style options and quality evaluation loops
- **Analyzes skill gaps** using semantic vector search against job requirements
- **Enriches company profiles** from job descriptions (industry, culture, AI maturity)
- **Evaluates document quality** via critic agent with ATS scoring

### Coming Soon
- Hiring manager inference and warm contact identification (Phase 2)
- Application tracking and follow-up workflows (Phase 3)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python (FastAPI), SQLAlchemy, Pydantic |
| Frontend | Next.js (TypeScript), Tailwind CSS, shadcn/ui |
| AI Models | Claude Sonnet 4 (primary), GPT-4o (fallback) |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | Qdrant (local or cloud) |
| Database | SQLite (dev), PostgreSQL (prod) |
| Deployment | Railway (backend), Vercel (frontend) |

## Repository Structure

```
etps/
├── backend/              # FastAPI backend
│   ├── services/         # AI agents, vector search, embeddings
│   ├── routers/          # API endpoints
│   ├── db/               # Database models
│   └── tests/            # 711+ tests
├── frontend/             # Next.js frontend
├── docs/                 # Documentation
│   ├── OPEN_SOURCE_STRATEGY.md   # Why this is open source
│   ├── ARCHITECTURE.md           # System architecture
│   ├── DATA_MODEL.md             # Database schema
│   └── IMPLEMENTATION_PLAN.md    # Sprint roadmap
├── .claude/              # Claude Code skills (AI-assisted development)
├── CONTRIBUTING.md       # How to contribute
└── ETPS_PRD.md           # Product Requirements Document
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- API Keys: Anthropic, OpenAI
- Qdrant (Docker or cloud) - optional for full semantic search

### Quick Start

```bash
# Clone the repository
git clone https://github.com/benjaminblack/etps.git
cd etps

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup instructions.

### Running Tests

```bash
cd backend
pytest -v
# 711+ tests passing
```

## Development Status

### Phase 1A: Core Quality
- [x] Resume tailoring with semantic bullet selection
- [x] Cover letter generation with multiple styles
- [x] Critic agent & ATS scoring
- [x] Skill-gap analysis with capability clustering
- [x] Qdrant vector search integration
- [x] Pagination-aware layout engine

### Phase 1B: Company Enrichment
- [x] Company profile extraction from job descriptions
- [x] Industry, size, and culture inference
- [x] AI/data maturity assessment

### Phase 1C: Deployment
- [x] Security hardening (rate limiting, CORS, SSRF prevention)
- [x] Cloud deployment (Railway + Vercel)
- [x] PostgreSQL migration
- [x] Qdrant Cloud integration

### Phase 2: Company Intelligence (Planned)
- [ ] Hiring manager inference
- [ ] Warm contact identification
- [ ] Networking suggestions

### Phase 3: Application Tracking (Future)
- [ ] Application status tracking
- [ ] Follow-up workflows
- [ ] Multi-user authentication

## Documentation

| Document | Description |
|----------|-------------|
| [Product Requirements](ETPS_PRD.md) | Full PRD with feature specifications |
| [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) | Sprint roadmap and progress |
| [Architecture](docs/ARCHITECTURE.md) | System design and service map |
| [Data Model](docs/DATA_MODEL.md) | Database schema reference |
| [Open Source Strategy](docs/OPEN_SOURCE_STRATEGY.md) | Why this project is open source |
| [Deployment Guide](docs/DEPLOYMENT_WALKTHROUGH_BEGINNERS.md) | Step-by-step deployment |

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Local development setup
- Code style guidelines
- Pull request process

## Author

**Benjamin Black**
- Portfolio: [benjaminblack.consulting/projects](https://benjaminblack.consulting/projects)
- LinkedIn: [linkedin.com/in/benjaminblack](https://linkedin.com/in/benjaminblack)

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
