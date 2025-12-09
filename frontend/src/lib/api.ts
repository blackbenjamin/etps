import type {
  JobProfile,
  JobParseRequest,
  SkillGapRequest,
  SkillGapResponse,
  TailoredResume,
  ResumeGenerateRequest,
  GeneratedCoverLetter,
  CoverLetterGenerateRequest,
  CriticResult,
  CapabilityClusterResponse,
  CapabilityClusterAnalysis,
  CapabilitySelectionUpdate,
  AddUserSkillRequest,
  AddUserSkillResponse,
  ExperienceWithDetails,
} from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// User profile info from environment variables
const USER_PROFILE = {
  name: process.env.NEXT_PUBLIC_USER_NAME || 'User',
  email: process.env.NEXT_PUBLIC_USER_EMAIL || '',
  phone: process.env.NEXT_PUBLIC_USER_PHONE || '',
  linkedin: process.env.NEXT_PUBLIC_USER_LINKEDIN || '',
  portfolio: process.env.NEXT_PUBLIC_USER_PORTFOLIO || '',
}

// Education entries (hardcoded for now - could be moved to env or database)
const EDUCATION = [
  {
    institution: "MIT Sloan School of Management",
    location: "Cambridge, MA",
    degree: "MBA, Strategy, Finance & Innovation",
    details: []
  },
  {
    institution: "Tufts University",
    location: "Medford, MA",
    degree: "B.A., Economics; International Relations; German Studies",
    details: ["Semester abroad in Berlin; fluent in German."]
  }
]

class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// Error for extraction quality failures (422 responses)
interface ExtractionErrorDetail {
  error: 'extraction_failed'
  message: string
  score: number
  issues: string[]
  suggestions: string[]
}

class ExtractionFailedError extends Error {
  status: number = 422
  detail: ExtractionErrorDetail

  constructor(detail: ExtractionErrorDetail) {
    super(detail.message)
    this.name = 'ExtractionFailedError'
    this.detail = detail
  }

  get userMessage(): string {
    return this.detail.message
  }

  get suggestions(): string[] {
    return this.detail.suggestions
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

    // Check for extraction failure (422 with specific error structure)
    if (
      response.status === 422 &&
      typeof errorBody.detail === 'object' &&
      errorBody.detail?.error === 'extraction_failed'
    ) {
      throw new ExtractionFailedError(errorBody.detail as ExtractionErrorDetail)
    }

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
        user_name: USER_PROFILE.name,
        user_email: USER_PROFILE.email,
        user_phone: USER_PROFILE.phone,
        user_linkedin: USER_PROFILE.linkedin,
        user_portfolio: USER_PROFILE.portfolio,
        education: EDUCATION,
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
        user_name: USER_PROFILE.name,
        user_email: USER_PROFILE.email,
        user_phone: USER_PROFILE.phone,
        user_linkedin: USER_PROFILE.linkedin,
        user_portfolio: USER_PROFILE.portfolio,
        education: EDUCATION,
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
      critic_result: CriticResult
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

  downloadCoverLetterDocx: async (coverLetter: GeneratedCoverLetter): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/api/v1/cover-letter/docx?format=docx`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        generated_cover_letter: coverLetter,
        user_name: USER_PROFILE.name,
        user_email: USER_PROFILE.email,
        user_phone: USER_PROFILE.phone,
        user_linkedin: USER_PROFILE.linkedin,
      }),
    })
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Download failed: ${errorText}`)
    }
    return response.blob()
  },

  downloadCoverLetterText: async (coverLetter: GeneratedCoverLetter): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/api/v1/cover-letter/docx?format=text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        generated_cover_letter: coverLetter,
        user_name: USER_PROFILE.name,
        user_email: USER_PROFILE.email,
        user_phone: USER_PROFILE.phone,
        user_linkedin: USER_PROFILE.linkedin,
      }),
    })
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Download failed: ${errorText}`)
    }
    return response.blob()
  },

  // Capability Clusters
  getCapabilityClusters: (jobProfileId: number, userId: number = 1, forceRefresh: boolean = false) =>
    apiFetch<CapabilityClusterResponse>(
      `/api/v1/capability/job-profiles/${jobProfileId}/clusters?user_id=${userId}&force_refresh=${forceRefresh}`
    ),

  analyzeCapabilityClusters: (data: { job_profile_id: number; user_id?: number; force_refresh?: boolean }) =>
    apiFetch<CapabilityClusterResponse>(`/api/v1/capability/job-profiles/${data.job_profile_id}/clusters/analyze`, {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: data.user_id || 1 }),
    }),

  getCombinedAnalysis: (jobProfileId: number, userId: number = 1) =>
    apiFetch<{
      job_profile_id: number
      user_id: number
      flat_analysis: SkillGapResponse
      cluster_analysis: CapabilityClusterAnalysis
      merged_score: number
      analysis_timestamp: string
    }>(`/api/v1/capability/job-profiles/${jobProfileId}/combined-analysis?user_id=${userId}`),

  // User Skills
  addUserSkill: (jobProfileId: number, data: AddUserSkillRequest) =>
    apiFetch<AddUserSkillResponse>(
      `/api/v1/capability/job-profiles/${jobProfileId}/user-skills`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    ),

  getUserExperiences: (userId: number = 1) =>
    apiFetch<ExperienceWithDetails[]>(`/api/v1/users/${userId}/experiences`),
}

// Skill Selection Types
export interface SelectedSkill {
  skill: string
  match_pct: number
  included: boolean
  order: number
}

export interface SkillSelectionUpdate {
  selected_skills: SelectedSkill[]
  key_skills: string[]
}

export interface SkillSelectionResponse {
  job_profile_id: number
  selected_skills: SelectedSkill[]
  key_skills: string[]
  updated_at: string
}

// Skill Selection API function
export async function updateSkillSelection(
  jobProfileId: number,
  selection: SkillSelectionUpdate
): Promise<SkillSelectionResponse> {
  const response = await fetch(`${API_BASE}/api/v1/job/job-profiles/${jobProfileId}/skills`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(selection),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to update skill selection' }))
    throw new Error(typeof error.detail === 'string' ? error.detail : 'Failed to update skill selection')
  }

  return response.json()
}

export async function getSkillSelection(jobProfileId: number): Promise<SkillSelectionResponse> {
  const response = await fetch(`${API_BASE}/api/v1/job/job-profiles/${jobProfileId}/skills`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get skill selection' }))
    throw new Error(typeof error.detail === 'string' ? error.detail : 'Failed to get skill selection')
  }

  return response.json()
}

export { ApiError, ExtractionFailedError }
