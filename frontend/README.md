# ETPS Frontend

Frontend application for the Enterprise-Grade Talent Positioning System (ETPS).

**Version:** 1.0.0
**Framework:** Next.js 14 (App Router)
**Status:** Phase 1 Complete

## Overview

Next.js-based frontend providing:
- Job intake interface (JD URL/text + context notes)
- Resume and cover letter generation with progress feedback
- Download functionality for DOCX, text, and JSON formats
- Skill-gap analysis with interactive skill selection
- Company profile display with industry/culture insights
- Modern enterprise design system with accessibility support

## Tech Stack

- **Framework:** Next.js 14 (TypeScript, App Router)
- **Styling:** Tailwind CSS + shadcn/ui components
- **State Management:** Zustand
- **Data Fetching:** TanStack Query (React Query)
- **Deployment:** Vercel

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout with providers
│   │   ├── page.tsx            # Main application page
│   │   ├── globals.css         # Global styles & animations
│   │   └── providers.tsx       # React Query provider
│   ├── components/
│   │   ├── analysis/           # Analysis result components
│   │   │   └── AnalysisResults.tsx
│   │   ├── capability/         # Capability cluster display
│   │   │   └── CapabilityClusterPanel.tsx
│   │   ├── generation/         # Document generation UI
│   │   │   ├── GenerateButtons.tsx
│   │   │   ├── DownloadButtons.tsx
│   │   │   └── ResultsPanel.tsx
│   │   ├── hero/               # Landing page hero section
│   │   │   └── HeroSection.tsx
│   │   ├── job-intake/         # Job description input
│   │   │   ├── JobIntakeForm.tsx
│   │   │   ├── JobDetailsCard.tsx
│   │   │   └── ContextNotesField.tsx
│   │   ├── results/            # Results preview components
│   │   │   └── ResultsPreview.tsx
│   │   ├── skeletons/          # Loading skeleton components
│   │   │   └── index.tsx
│   │   ├── skills/             # Skill selection components
│   │   │   ├── SkillSelectionPanel.tsx
│   │   │   └── SkillGroup.tsx
│   │   └── ui/                 # shadcn/ui base components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── collapsible.tsx
│   │       ├── circular-progress.tsx
│   │       ├── progress-bar.tsx
│   │       ├── empty-state.tsx
│   │       ├── sonner.tsx      # Toast notifications
│   │       └── ...
│   ├── hooks/
│   │   └── queries.ts          # TanStack Query hooks
│   ├── lib/
│   │   └── api.ts              # API client functions
│   ├── stores/
│   │   ├── job-store.ts        # Job profile state
│   │   └── generation-store.ts # Generation results state
│   ├── styles/
│   │   └── design-tokens.css   # Design system tokens
│   └── types/
│       └── index.ts            # TypeScript type definitions
├── public/
│   └── assets/                 # Static assets (logo, images)
├── tailwind.config.ts          # Tailwind configuration
├── next.config.js              # Next.js configuration
└── package.json
```

## Getting Started

```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your values

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL |
| `NEXT_PUBLIC_USER_NAME` | No | Display name for single-user mode |

### Example `.env.local`

```bash
# Development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production
# NEXT_PUBLIC_API_URL=https://etps-production.up.railway.app
```

## Design System

The frontend uses a custom enterprise design system with:

### Color Palette
- **Primary:** Teal (#0891b2) - enterprise accent
- **Enterprise Navy:** #334155 - headings, important text
- **Enterprise Slate:** #64748b - body text
- **Success/Warning/Danger:** Semantic colors for status

### Typography
- **Sans:** Inter (Google Fonts)
- **Mono:** JetBrains Mono (code blocks)

### Components
Built on shadcn/ui with custom enhancements:
- CircularProgress - animated score displays
- ProgressBar - horizontal progress indicators
- Collapsible - animated expand/collapse sections
- EmptyState - consistent empty state displays
- Skeletons - loading state placeholders

### Animations
- Fade-in animations for content loading
- Stagger animations for list items
- Collapsible expand/collapse transitions
- Button micro-interactions (scale on press)
- Shimmer effects for skeleton loaders

## Key Features

### Job Intake
- Paste job description text (50+ chars)
- Or provide a job posting URL
- Add optional context notes for personalization

### Skill Selection
- View matched, partial, and missing skills
- Toggle skills on/off for resume inclusion
- Reorder skills by priority

### Document Generation
- Generate tailored resume with progress feedback
- Generate cover letter with style options
- Download as DOCX, plain text, or JSON

### Results Display
- ATS score visualization with CircularProgress
- Skill gap analysis with match percentages
- Company profile insights

## Scripts

```bash
# Development
npm run dev         # Start dev server
npm run build       # Build for production
npm run start       # Start production server
npm run lint        # Run ESLint

# Type checking
npx tsc --noEmit    # Check TypeScript types
```

## Deployment

Deployed on Vercel with automatic deploys from `main` branch.

**Production URL:** [https://etps.benjaminblack.consulting](https://etps.benjaminblack.consulting)

### Vercel Configuration

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next"
}
```

## Accessibility

- Skip link for keyboard navigation
- Focus-visible states for interactive elements
- Screen reader support with semantic HTML
- Reduced motion support via `prefers-reduced-motion`
- High contrast mode support

## License

MIT License - See [LICENSE](../LICENSE) for details.
