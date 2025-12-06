# ETPS - Enterprise-Grade Talent Positioning System

An AI-Orchestrated Resume, Cover Letter, and Networking Intelligence Platform

## Overview

ETPS is a multi-agent, AI-driven system that:
- Tailors resumes and cover letters to specific roles while preserving professional `.docx` formatting
- Evaluates role fit and skill gaps against job descriptions
- Surfaces company and networking intelligence (Phase 2)
- Tracks applications and supports follow-up workflows (Phase 3)

## Repository Structure

```
etps/
├── backend/          # FastAPI backend API
├── frontend/         # Next.js frontend application
├── configs/          # Shared configuration files
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── ETPS_PRD.md       # Product Requirements Document
```

## Tech Stack

- **Backend:** Python (FastAPI), SQLite, Qdrant
- **Frontend:** Next.js (TypeScript), Tailwind CSS, shadcn/ui
- **AI Models:** Claude Sonnet/Opus (primary), GPT-4o (fallback)
- **Deployment:** Railway (backend), Vercel (frontend)

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Development Status

- [x] Repository skeleton
- [ ] Database models
- [ ] Resume tailoring service
- [ ] Cover letter generation
- [ ] Critic agent & ATS scoring
- [ ] Skill-gap analysis
- [ ] Company intelligence (Phase 2)
- [ ] Networking suggestions (Phase 2)
- [ ] Application tracking (Phase 3)

## Author

Benjamin Black

## License

Proprietary
