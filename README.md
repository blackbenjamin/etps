# ETPS - Enterprise-Grade Talent Positioning System

An AI-Orchestrated Resume, Cover Letter, and Networking Intelligence Platform

[![Railway Deploy](https://img.shields.io/badge/Railway-Deployed-success)](https://railway.app)
[![Vercel Deploy](https://img.shields.io/badge/Vercel-Deployed-success)](https://projects.benjaminblack.consulting)

## 🌐 Live Demo

**Production URL**: [https://projects.benjaminblack.consulting](https://projects.benjaminblack.consulting)

## Overview

ETPS is a multi-agent, AI-driven system that:
- Tailors resumes and cover letters to specific roles while preserving professional `.docx` formatting
- Evaluates role fit and skill gaps against job descriptions using semantic vector search
- Enriches company profiles from job descriptions
- Surfaces company and networking intelligence (Phase 2 - Coming Soon)
- Tracks applications and supports follow-up workflows (Phase 3 - Future)

## Repository Structure

```
etps/
├── backend/          # FastAPI backend API
│   ├── services/     # AI agents, vector search, embeddings
│   ├── routers/      # API endpoints
│   ├── db/           # Database models and migrations
│   └── tests/        # 711 passing tests
├── frontend/         # Next.js frontend application
├── docs/             # Documentation
│   ├── DEPLOYMENT_WALKTHROUGH_BEGINNERS.md  # Step-by-step deployment guide
│   ├── ENV_VARIABLES_REFERENCE.md           # Environment variables reference
│   ├── DATABASE_MIGRATION_GUIDE.md          # SQLite to PostgreSQL migration
│   └── IMPLEMENTATION_PLAN.md               # Sprint roadmap
├── scripts/          # Utility scripts
└── ETPS_PRD.md       # Product Requirements Document
```

## Tech Stack

- **Backend:** Python (FastAPI), PostgreSQL, Qdrant Cloud
- **Frontend:** Next.js (TypeScript), Tailwind CSS, shadcn/ui
- **AI Models:** Claude Sonnet 4 (primary), GPT-4o (fallback)
- **Embeddings:** OpenAI text-embedding-3-small
- **Deployment:** Railway (backend), Vercel (frontend), Qdrant Cloud (vectors)

## 🚀 Deployment

### Production (Live)

The application is deployed and running:
- **Backend**: Railway (FastAPI + PostgreSQL)
- **Frontend**: Vercel (Next.js)
- **Vector Store**: Qdrant Cloud (free tier)

**For deployment instructions**, see:
- [`docs/DEPLOYMENT_WALKTHROUGH_BEGINNERS.md`](docs/DEPLOYMENT_WALKTHROUGH_BEGINNERS.md) - Complete beginner-friendly guide
- [`docs/ENV_VARIABLES_REFERENCE.md`](docs/ENV_VARIABLES_REFERENCE.md) - Environment variables reference
- [`docs/DATABASE_MIGRATION_GUIDE.md`](docs/DATABASE_MIGRATION_GUIDE.md) - Database migration guide

## Getting Started (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- Qdrant (Docker or local install)
- API Keys: Anthropic, OpenAI

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env and add your API keys

# Run backend
uvicorn main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_USER_NAME=Your Name" >> .env.local

# Run frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Running Tests

```bash
cd backend
pytest -v
# 711 tests passing ✅
```

## Development Status

### ✅ Phase 1A: Core Quality (Complete)
- [x] Resume tailoring with semantic bullet selection
- [x] Cover letter generation with multiple styles
- [x] Critic agent & ATS scoring
- [x] Skill-gap analysis with capability clustering
- [x] Qdrant vector search integration
- [x] Pagination-aware layout engine
- [x] Frontend MVP with job intake UI

### ✅ Phase 1B: Company Enrichment (Complete)
- [x] Company profile extraction from job descriptions
- [x] Industry, size, and culture inference
- [x] AI/data maturity assessment

### ✅ Phase 1C: Deployment (Complete)
- [x] Security hardening (rate limiting, CORS, SSRF prevention)
- [x] Cloud deployment (Railway + Vercel)
- [x] PostgreSQL migration
- [x] Qdrant Cloud integration

### 🔜 Phase 2: Company Intelligence (Planned)
- [ ] Hiring manager inference
- [ ] Warm contact identification
- [ ] Networking suggestions & outreach drafts

### 🔮 Phase 3: Application Tracking (Future)
- [ ] Application status tracking
- [ ] Contact management
- [ ] Follow-up workflows
- [ ] Multi-user authentication

## Documentation

- **[Product Requirements](ETPS_PRD.md)** - Full PRD with feature specifications
- **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md)** - Sprint roadmap and progress
- **[Deployment Guide](docs/DEPLOYMENT_WALKTHROUGH_BEGINNERS.md)** - Step-by-step deployment
- **[Database Migration](docs/DATABASE_MIGRATION_GUIDE.md)** - SQLite to PostgreSQL migration

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Author

Benjamin Black

## License

Proprietary
