import type {
  JobProfile,
  JobParseRequest,
  SkillGapRequest,
  SkillGapResponse,
  TailoredResume,
  ResumeGenerateRequest,
  GeneratedCoverLetter,
  CoverLetterGenerateRequest,
} from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: 'Request failed' }))
    const errorMessage = typeof errorBody.detail === 'string'
      ? errorBody.detail
      : JSON.stringify(errorBody.detail)
    throw new ApiError(errorMessage || `HTTP ${response.status}`, response.status)
  }

  // Handle empty responses
  const text = await response.text()
  return text ? JSON.parse(text) : ({} as T)
}

export const api = {
  // Health check
  healthCheck: () => apiFetch<{ status: string; version: string }>('/health'),

  // Job Profile
  parseJobDescription: (data: JobParseRequest) =>
    apiFetch<JobProfile>('/api/v1/job/parse', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getJobProfile: (id: number) =>
    apiFetch<JobProfile>(`/api/v1/job/${id}`),

  // Skill Gap
  analyzeSkillGap: (data: { job_profile_id: number; user_id?: number }) =>
    apiFetch<SkillGapResponse>('/api/v1/job/skill-gap', {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: data.user_id || 1 }),
    }),

  // Resume
  generateResume: (data: { job_profile_id: number; context_notes?: string }) =>
    apiFetch<TailoredResume>('/api/v1/resume/generate', {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: 1 }),
    }),

  downloadResumeDocx: async (resume: TailoredResume): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/api/v1/resume/docx?format=docx`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tailored_resume: resume,
        user_name: 'Benjamin Black',
        user_email: 'benjamin@etps.dev',
        user_phone: '555-0123',
        user_linkedin: 'linkedin.com/in/benjaminblack',
        user_portfolio: 'github.com/benjaminblack',
      }),
    })
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Download failed: ${errorText}`)
    }
    return response.blob()
  },

  downloadResumeText: async (resume: TailoredResume): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/api/v1/resume/docx?format=text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tailored_resume: resume,
        user_name: 'Benjamin Black',
        user_email: 'benjamin@etps.dev',
        user_phone: '555-0123',
        user_linkedin: 'linkedin.com/in/benjaminblack',
        user_portfolio: 'github.com/benjaminblack',
      }),
    })
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Download failed: ${errorText}`)
    }
    return response.blob()
  },

  // Cover Letter
  generateCoverLetter: (data: { job_profile_id: number; context_notes?: string }) =>
    apiFetch<GeneratedCoverLetter>('/api/v1/cover-letter/generate', {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: 1 }),
    }),

  generateCoverLetterWithCritic: async (data: CoverLetterGenerateRequest) => {
    const response = await apiFetch<{
      cover_letter: GeneratedCoverLetter
      critic_result: any
      accepted: boolean
    }>('/api/v1/cover-letter/generate-with-critic', {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: 1 }),
    })
    return {
      ...response.cover_letter,
      critic_result: response.critic_result,
    }
  },

  downloadCoverLetterDocx: async (jobProfileId: number): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/api/v1/cover-letter/docx?job_profile_id=${jobProfileId}`);
    if (!response.ok) throw new Error('Download failed');
    return response.blob();
  },
}

export { ApiError }
