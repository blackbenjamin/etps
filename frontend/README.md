# ETPS Frontend

Frontend application for the Enterprise-Grade Talent Positioning System (ETPS).

## Overview

Next.js-based frontend providing:
- Job intake interface (JD URL/text + context notes)
- Resume and cover letter generation triggers
- Download functionality for docx, text, JSON formats
- Skill-gap analysis display
- Company and networking views (Phase 2)
- Application history (Phase 3)

## Tech Stack

- **Framework:** Next.js 14 (TypeScript)
- **Styling:** Tailwind CSS + shadcn/ui
- **Deployment:** Vercel

## Project Structure

```
frontend/
├── src/
│   └── app/
│       ├── layout.tsx    # Root layout
│       ├── page.tsx      # Home page
│       └── globals.css   # Global styles
├── public/               # Static assets
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Configuration

TODO: Document environment variables and configuration options.

## License

Proprietary - Benjamin Black
