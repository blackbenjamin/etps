import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type {
  JobParseRequest,
  SkillGapRequest,
  ResumeGenerateRequest,
  CoverLetterGenerateRequest,
  TailoredResume,
} from '@/types'

// Query keys for cache management
export const queryKeys = {
  jobProfile: (id: number) => ['jobProfile', id] as const,
  skillGap: (jobProfileId: number) => ['skillGap', jobProfileId] as const,
  resume: (jobProfileId: number) => ['resume', jobProfileId] as const,
  coverLetter: (jobProfileId: number) => ['coverLetter', jobProfileId] as const,
}

// Health check hook
export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.healthCheck,
    retry: false,
    staleTime: 30 * 1000, // 30 seconds
  })
}

// Parse job description mutation
export function useParseJobDescription() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: JobParseRequest) => api.parseJobDescription(data),
    onSuccess: (data) => {
      // API returns job_profile_id, not id
      const jobId = data.job_profile_id ?? data.id
      if (jobId) {
        queryClient.setQueryData(queryKeys.jobProfile(jobId), data)
      }
    },
  })
}

// Get job profile query
export function useJobProfile(id: number | null) {
  return useQuery({
    queryKey: id ? queryKeys.jobProfile(id) : ['jobProfile', null],
    queryFn: () => api.getJobProfile(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Skill gap analysis query
export function useSkillGapAnalysis(jobProfileId: number | null) {
  return useQuery({
    queryKey: jobProfileId ? queryKeys.skillGap(jobProfileId) : ['skillGap', null],
    queryFn: () => api.analyzeSkillGap({ job_profile_id: jobProfileId! }),
    enabled: !!jobProfileId,
    staleTime: 5 * 60 * 1000,
  })
}

// Resume generation mutation
export function useGenerateResume() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ResumeGenerateRequest) => api.generateResume(data),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(queryKeys.resume(variables.job_profile_id), data)
    },
  })
}

// Cover letter generation mutation
export function useGenerateCoverLetter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CoverLetterGenerateRequest) => api.generateCoverLetter(data),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(queryKeys.coverLetter(variables.job_profile_id), data)
    },
  })
}

// Cover letter with critic generation mutation
export function useGenerateCoverLetterWithCritic() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CoverLetterGenerateRequest) => api.generateCoverLetterWithCritic(data),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(queryKeys.coverLetter(variables.job_profile_id), data)
    },
  })
}

// Download resume mutation
export function useDownloadResume() {
  return useMutation({
    mutationFn: async (resume: TailoredResume) => {
      const blob = await api.downloadResumeDocx(resume)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `resume_${resume.job_profile_id}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}

// Download cover letter mutation
export function useDownloadCoverLetter() {
  return useMutation({
    mutationFn: async (jobProfileId: number) => {
      const blob = await api.downloadCoverLetterDocx(jobProfileId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cover_letter_${jobProfileId}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}
