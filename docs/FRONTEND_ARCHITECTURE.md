# ETPS Frontend Architecture

**Version:** 1.0
**Last Updated:** December 2025
**Target Sprints:** 9-10 (Frontend MVP)

---

## Overview

The ETPS frontend is a Next.js 14+ application using the App Router, styled with Tailwind CSS and shadcn/ui components. It provides a streamlined interface for the resume and cover letter generation workflow.

### Design Principles

1. **Minimal Friction**: Paste JD → Generate → Download in under 60 seconds
2. **Progressive Disclosure**: Show essential controls first, advanced options on demand
3. **Real-time Feedback**: Loading states, progress indicators, and immediate validation
4. **Responsive Design**: Desktop-first with mobile compatibility

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | Next.js 14+ (App Router) | Server components, streaming, optimized builds |
| Language | TypeScript | Type safety with backend schema alignment |
| Styling | Tailwind CSS | Utility-first, rapid prototyping |
| Components | shadcn/ui | Accessible, customizable primitives |
| State | Zustand | Simple global state, no boilerplate, handles complex resume state |
| Forms | React Hook Form + Zod | Declarative validation, synced with backend schemas |
| Data Fetching | TanStack Query (React Query) | Caching, loading states, optimistic updates |
| Drag & Drop | dnd-kit (Phase 2+) | Modern, accessible reordering for editor features |
| Testing | Vitest + Testing Library | Fast unit/integration tests |

---

## Directory Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── layout.tsx                # Root layout with providers
│   │   ├── page.tsx                  # Main job intake page
│   │   ├── applications/             # Application tracking (Phase 3)
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   └── api/                      # API routes (if needed)
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── tabs.tsx
│   │   │   └── ...
│   │   │
│   │   ├── job-intake/               # Job intake feature
│   │   │   ├── JobIntakeForm.tsx     # Main form component
│   │   │   ├── JDTextArea.tsx        # JD input with URL fetch
│   │   │   ├── ContextNotesField.tsx # Optional context notes
│   │   │   └── URLFetchButton.tsx    # Fetch JD from URL
│   │   │
│   │   ├── generation/               # Generation workflow
│   │   │   ├── GenerateButtons.tsx   # Resume/CL generation triggers
│   │   │   ├── GenerationProgress.tsx# Progress indicator
│   │   │   ├── DownloadButtons.tsx   # DOCX/TXT/JSON downloads
│   │   │   └── ResultsPanel.tsx      # Output display
│   │   │
│   │   ├── analysis/                 # Analysis displays
│   │   │   ├── SkillGapPanel.tsx     # Skill gap visualization
│   │   │   ├── ATSScoreCard.tsx      # ATS score with color coding
│   │   │   └── MatchIndicator.tsx    # Overall match display
│   │   │
│   │   └── layout/                   # Layout components
│   │       ├── Header.tsx
│   │       ├── Footer.tsx
│   │       └── Sidebar.tsx
│   │
│   ├── lib/
│   │   ├── api.ts                    # API client with typed responses
│   │   ├── utils.ts                  # Utility functions
│   │   └── validators.ts             # Zod schemas for forms
│   │
│   ├── stores/                       # Zustand stores
│   │   ├── job-store.ts              # Job profile state
│   │   ├── generation-store.ts       # Generation workflow state
│   │   └── user-store.ts             # User preferences
│   │
│   ├── types/                        # TypeScript definitions
│   │   ├── api.ts                    # API response types
│   │   ├── job-profile.ts            # JobProfile type
│   │   ├── resume.ts                 # TailoredResume type
│   │   ├── cover-letter.ts           # CoverLetter type
│   │   └── skill-gap.ts              # SkillGapResponse type
│   │
│   └── hooks/                        # Custom React hooks
│       ├── queries.ts                # TanStack Query hooks (useParseJob, useSkillGap, etc.)
│       ├── useJobIntake.ts           # Job intake form logic
│       ├── useGeneration.ts          # Generation workflow orchestration
│       └── useDownload.ts            # File download handling
│
├── public/                           # Static assets
├── tailwind.config.ts
├── next.config.mjs
├── tsconfig.json
└── package.json
```

---

## State Management

### Approach: Zustand + TanStack Query

We separate **client state** from **server state**:

| State Type | Tool | Examples |
|------------|------|----------|
| **Server State** | TanStack Query | Job profiles, skill gap results, generated outputs (data from API) |
| **Client State** | Zustand | UI preferences, form draft state, workflow step tracking |
| **Provider State** | React Context | Theme, toast notifications, modal state |

**Why this split?**
- TanStack Query handles caching, refetching, and loading states for API data
- Zustand handles ephemeral UI state that doesn't need server sync
- Avoids the common mistake of storing server data in client state stores

### Store Design

#### Job Store (`stores/job-store.ts`)

```typescript
import { create } from 'zustand';
import { JobProfile, SkillGapResponse } from '@/types';

interface JobState {
  // Current job being worked on
  currentJob: JobProfile | null;
  skillGapAnalysis: SkillGapResponse | null;

  // Loading states
  isParsingJD: boolean;
  isAnalyzingGap: boolean;

  // Actions
  setCurrentJob: (job: JobProfile) => void;
  setSkillGapAnalysis: (analysis: SkillGapResponse) => void;
  parseJobDescription: (text: string, url?: string) => Promise<void>;
  analyzeSkillGap: (jobProfileId: number) => Promise<void>;
  reset: () => void;
}

export const useJobStore = create<JobState>((set, get) => ({
  currentJob: null,
  skillGapAnalysis: null,
  isParsingJD: false,
  isAnalyzingGap: false,

  setCurrentJob: (job) => set({ currentJob: job }),
  setSkillGapAnalysis: (analysis) => set({ skillGapAnalysis: analysis }),

  parseJobDescription: async (text, url) => {
    set({ isParsingJD: true });
    try {
      const job = await api.parseJobDescription({ raw_text: text, source_url: url });
      set({ currentJob: job, isParsingJD: false });
    } catch (error) {
      set({ isParsingJD: false });
      throw error;
    }
  },

  analyzeSkillGap: async (jobProfileId) => {
    set({ isAnalyzingGap: true });
    try {
      const analysis = await api.analyzeSkillGap({ job_profile_id: jobProfileId });
      set({ skillGapAnalysis: analysis, isAnalyzingGap: false });
    } catch (error) {
      set({ isAnalyzingGap: false });
      throw error;
    }
  },

  reset: () => set({ currentJob: null, skillGapAnalysis: null }),
}));
```

#### Generation Store (`stores/generation-store.ts`)

```typescript
import { create } from 'zustand';
import { TailoredResume, GeneratedCoverLetter, CriticResult } from '@/types';

interface GenerationState {
  // Generated outputs
  resume: TailoredResume | null;
  coverLetter: GeneratedCoverLetter | null;

  // Quality metrics
  resumeCriticResult: CriticResult | null;
  coverLetterCriticResult: CriticResult | null;
  atsScore: number | null;

  // Workflow state
  generationStep: 'idle' | 'generating-resume' | 'generating-cover-letter' | 'complete';
  contextNotes: string;

  // Actions
  setContextNotes: (notes: string) => void;
  generateResume: (jobProfileId: number) => Promise<void>;
  generateCoverLetter: (jobProfileId: number) => Promise<void>;
  generateBoth: (jobProfileId: number) => Promise<void>;
  downloadFile: (type: 'resume' | 'cover-letter', format: 'docx' | 'txt' | 'json') => Promise<void>;
  reset: () => void;
}
```

---

## Data Fetching with TanStack Query

We use TanStack Query (React Query) for all server state management. This provides:
- **Automatic caching**: Parsed job profiles cached, no redundant API calls
- **Loading/error states**: Consistent UX without manual state management
- **Optimistic updates**: UI feels instant, rolls back on error
- **Background refetching**: Data stays fresh without user action

### API Functions (`lib/api.ts`)

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Base fetch wrapper with error handling
async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// API functions (used by TanStack Query hooks)
export const api = {
  // Job Profile
  parseJobDescription: (data: { raw_text: string; source_url?: string }) =>
    apiFetch<JobProfile>('/job-profile/parse', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getJobProfile: (id: number) =>
    apiFetch<JobProfile>(`/job-profile/${id}`),

  // Skill Gap
  analyzeSkillGap: (data: { job_profile_id: number; user_id?: number }) =>
    apiFetch<SkillGapResponse>('/skill-gap/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Resume
  generateResume: (data: { job_profile_id: number; context_notes?: string }) =>
    apiFetch<TailoredResume>('/resume/tailor', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  downloadResumeDocx: async (jobProfileId: number): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/resume/docx?job_profile_id=${jobProfileId}`);
    if (!response.ok) throw new Error('Download failed');
    return response.blob();
  },

  // Cover Letter
  generateCoverLetter: (data: { job_profile_id: number; context_notes?: string }) =>
    apiFetch<GeneratedCoverLetter>('/cover-letter/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  downloadCoverLetterDocx: async (jobProfileId: number): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/cover-letter/docx?job_profile_id=${jobProfileId}`);
    if (!response.ok) throw new Error('Download failed');
    return response.blob();
  },
};
```

### Query Hooks (`hooks/queries.ts`)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Query keys for cache management
export const queryKeys = {
  jobProfile: (id: number) => ['jobProfile', id] as const,
  skillGap: (jobProfileId: number) => ['skillGap', jobProfileId] as const,
  resume: (jobProfileId: number) => ['resume', jobProfileId] as const,
  coverLetter: (jobProfileId: number) => ['coverLetter', jobProfileId] as const,
};

// Parse job description mutation
export function useParseJobDescription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.parseJobDescription,
    onSuccess: (data) => {
      // Cache the parsed job profile
      queryClient.setQueryData(queryKeys.jobProfile(data.id), data);
    },
  });
}

// Skill gap analysis query (auto-fetches when jobProfileId is set)
export function useSkillGapAnalysis(jobProfileId: number | null) {
  return useQuery({
    queryKey: queryKeys.skillGap(jobProfileId!),
    queryFn: () => api.analyzeSkillGap({ job_profile_id: jobProfileId! }),
    enabled: !!jobProfileId, // Only fetch when we have a job profile
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

// Resume generation mutation
export function useGenerateResume() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.generateResume,
    onSuccess: (data, variables) => {
      queryClient.setQueryData(queryKeys.resume(variables.job_profile_id), data);
    },
  });
}

// Cover letter generation mutation
export function useGenerateCoverLetter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.generateCoverLetter,
    onSuccess: (data, variables) => {
      queryClient.setQueryData(queryKeys.coverLetter(variables.job_profile_id), data);
    },
  });
}

// Download hooks with loading state
export function useDownloadResume() {
  return useMutation({
    mutationFn: async (jobProfileId: number) => {
      const blob = await api.downloadResumeDocx(jobProfileId);
      // Trigger browser download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resume_${jobProfileId}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });
}
```

### Usage in Components

```typescript
function JobIntakePage() {
  const parseJob = useParseJobDescription();
  const generateResume = useGenerateResume();
  const { data: skillGap, isLoading: isAnalyzing } = useSkillGapAnalysis(
    parseJob.data?.id ?? null
  );

  const handleSubmit = async (jdText: string) => {
    const job = await parseJob.mutateAsync({ raw_text: jdText });
    // Skill gap analysis auto-fetches due to enabled condition
  };

  return (
    <div>
      {parseJob.isPending && <Spinner />}
      {parseJob.isError && <ErrorMessage error={parseJob.error} />}
      {skillGap && <SkillGapPanel analysis={skillGap} />}
    </div>
  );
}
```

---

## Component Specifications

### JobIntakeForm

Primary form for job description input and generation workflow.

```typescript
interface JobIntakeFormProps {
  onJobParsed?: (job: JobProfile) => void;
  onGenerate?: () => void;
}

// States:
// 1. Empty - awaiting JD input
// 2. JD entered - ready to parse
// 3. Parsing - loading state
// 4. Parsed - showing job details, ready to generate
// 5. Generating - loading state
// 6. Complete - showing results
```

### ATSScoreCard

Displays ATS compatibility score with visual indicators.

```typescript
interface ATSScoreCardProps {
  score: number;           // 0-100
  explanation?: string;    // Brief explanation of score
  suggestions?: string[];  // Improvement suggestions
}

// Visual:
// - Score < 60: Red indicator, "Needs Improvement"
// - Score 60-75: Yellow indicator, "Good"
// - Score > 75: Green indicator, "Excellent"
```

### SkillGapPanel

Visualizes skill gap analysis results.

```typescript
interface SkillGapPanelProps {
  analysis: SkillGapResponse;
  onRefresh?: () => void;
}

// Sections:
// 1. Match Score (overall percentage)
// 2. Matched Skills (green checks)
// 3. Weak Signals (yellow warnings)
// 4. Skill Gaps (red gaps)
// 5. Positioning Strategies (actionable tips)
```

---

## User Flow

### Primary Flow: Generate Resume + Cover Letter

```
┌─────────────────────────────────────────────────────────────┐
│                     JOB INTAKE PAGE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Job Description                                [Fetch] │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │                                                  │  │ │
│  │  │  Paste job description text here...              │  │ │
│  │  │                                                  │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  Context Notes (optional)                              │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  Add any special instructions...                 │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  [ Parse Job Description ]                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Job Details (after parsing)                           │ │
│  │  ──────────────────────────────────────────────────────│ │
│  │  Title: Senior Data Scientist                          │ │
│  │  Company: Acme Corp                                    │ │
│  │  Location: Boston, MA                                  │ │
│  │  Seniority: Senior                                     │ │
│  │                                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐                     │ │
│  │  │ ATS: 82/100 │  │ Match: 78%  │                     │ │
│  │  └─────────────┘  └─────────────┘                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Skill Gap Analysis                                    │ │
│  │  ──────────────────────────────────────────────────────│ │
│  │  ✓ Python, Machine Learning, SQL                       │ │
│  │  ⚠ Cloud Platforms (partial match)                     │ │
│  │  ✗ RAG Systems (opportunity to position)               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  [ Generate Resume ]  [ Generate Cover Letter ]        │ │
│  │                                                        │ │
│  │  [ Generate Both ]                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Results                                               │ │
│  │  ──────────────────────────────────────────────────────│ │
│  │  Resume: ✓ Generated (ATS: 85)                         │ │
│  │  [ Download DOCX ] [ Download TXT ] [ View JSON ]      │ │
│  │                                                        │ │
│  │  Cover Letter: ✓ Generated (Quality: 88)               │ │
│  │  [ Download DOCX ] [ Download TXT ] [ View JSON ]      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Styling Guidelines

### Color Palette

```css
/* Primary colors */
--primary: 222.2 47.4% 11.2%;      /* Dark blue-gray */
--primary-foreground: 210 40% 98%; /* Light text */

/* Semantic colors */
--success: 142.1 76.2% 36.3%;      /* Green */
--warning: 47.9 95.8% 53.1%;       /* Yellow */
--destructive: 0 84.2% 60.2%;      /* Red */

/* ATS Score colors */
--ats-excellent: var(--success);    /* > 75 */
--ats-good: var(--warning);         /* 60-75 */
--ats-poor: var(--destructive);     /* < 60 */
```

### Typography

- **Headings**: Inter (system fallback: sans-serif)
- **Body**: Inter
- **Code/Technical**: JetBrains Mono

### Component Styling

All components use shadcn/ui defaults with minimal customization:
- Rounded corners (`rounded-lg`)
- Subtle shadows on cards
- Clear hover/focus states
- Consistent spacing (4px grid)

---

## Performance Considerations

### Optimizations

1. **Server Components**: Use RSC for static content
2. **Streaming**: Stream generation results as they arrive
3. **Code Splitting**: Dynamic imports for heavy components
4. **Caching**: Cache parsed job profiles and skill gap results

### Targets

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| Time to Interactive | < 3.0s |
| Cumulative Layout Shift | < 0.1 |

---

## Testing Strategy

### Unit Tests (Vitest)

- Component rendering
- Store actions and selectors
- Utility functions
- Form validation

### Integration Tests

- API client with mock server
- User flows with Testing Library
- State management integration

### E2E Tests (Playwright - Future)

- Full generation workflow
- File download verification
- Error handling

---

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
```

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.etps.example.com
NEXT_PUBLIC_APP_ENV=production
```

---

## Implementation Checklist (Sprints 9-10)

### Sprint 9: Setup & Foundation

- [ ] Initialize Next.js 14 with TypeScript
- [ ] Configure Tailwind CSS
- [ ] Install and configure shadcn/ui
- [ ] Install TanStack Query (`@tanstack/react-query`)
- [ ] Install Zustand for client state
- [ ] Install React Hook Form + Zod
- [ ] Create base layout component with QueryClientProvider
- [ ] Set up API client with types
- [ ] Create TanStack Query hooks (`hooks/queries.ts`)
- [ ] Configure environment variables
- [ ] Create type definitions from backend schemas

### Sprint 10: Core Features

- [ ] Build JobIntakeForm component
- [ ] Implement JD text area with URL fetch
- [ ] Add context notes field
- [ ] Create generation buttons with loading states
- [ ] Build results panel
- [ ] Implement download buttons (DOCX, TXT, JSON)
- [ ] Add skill gap analysis display
- [ ] Add ATS score card with color coding
- [ ] Wire up all components to backend APIs
- [ ] Add error handling and validation

---

## Future Enhancements (Post-MVP)

1. **Application Tracking UI** (Phase 3)
   - Application list view
   - Status updates
   - Contact management

2. **Networking Intelligence** (Phase 2)
   - Warm contact display
   - Hiring manager suggestions
   - Outreach message generation

3. **Resume Editor** (Phase 2+)
   - Interactive bullet reordering with **dnd-kit**
   - Inline editing with real-time preview
   - Experience section drag-and-drop
   - Live ATS score updates as user edits

4. **Advanced Features**
   - Resume preview/editor
   - Side-by-side comparison
   - History/versioning
   - Batch processing

---

*Last Updated: December 2025*
