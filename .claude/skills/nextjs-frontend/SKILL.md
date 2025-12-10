---
name: nextjs-frontend
description: Build Next.js pages with shadcn/ui components, React hooks, TypeScript, and TanStack Query. Use when working on frontend/ directory, UI components, pages, hooks, or API integration.
---

# Next.js Frontend for ETPS

## Tech Stack
- Framework: Next.js 14 (App Router)
- UI: shadcn/ui components
- Styling: Tailwind CSS
- State: TanStack Query for API caching
- Language: TypeScript

## Key Directories
```
frontend/src/
├── app/           # Pages and layouts
├── components/    # React components
│   ├── ui/        # shadcn/ui components
│   ├── generation/# Resume/CL generation UI
│   └── job-intake/# Job intake form
├── hooks/         # Custom hooks (queries.ts)
├── lib/           # Utilities (api.ts, utils.ts)
└── types/         # TypeScript types
```

## API Integration
```typescript
// frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = {
  parseJobDescription: (data: JobParseRequest) =>
    apiFetch<JobProfile>('/api/v1/job/parse', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  // ...
}
```

## React Query Hooks
```typescript
// frontend/src/hooks/queries.ts
export function useParseJobDescription() {
  return useMutation({
    mutationFn: (data: JobParseRequest) => api.parseJobDescription(data),
  })
}
```

## Component Pattern
```tsx
'use client'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface MyComponentProps {
  data: SomeType
}

export function MyComponent({ data }: MyComponentProps) {
  return (
    <Card>
      <Button>Action</Button>
    </Card>
  )
}
```

## Environment Variables
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_USER_NAME` - User's name for documents
- `NEXT_PUBLIC_USER_EMAIL` - User's email for documents
- `NEXT_PUBLIC_USER_PHONE` - User's phone for documents
- `NEXT_PUBLIC_USER_LINKEDIN` - User's LinkedIn URL

## Best Practices
1. Use shadcn/ui for all UI components
2. Type all props with TypeScript interfaces
3. Use TanStack Query for API calls (caching, loading states)
4. Keep components focused and composable
5. Use 'use client' directive for interactive components
