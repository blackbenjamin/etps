import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { generateDownloadFilename } from '@/lib/utils'
import type {
  JobParseRequest,
  SkillGapRequest,
  ResumeGenerateRequest,
  CoverLetterGenerateRequest,
  TailoredResume,
  GeneratedCoverLetter,
} from '@/types'

// Query keys for cache management
export const queryKeys = {
  jobProfile: (id: number) => ['jobProfile', id] as const,
  skillGap: (jobProfileId: number) => ['skillGap', jobProfileId] as const,
  capabilityClusters: (jobProfileId: number) => ['capabilityClusters', jobProfileId] as const,
  combinedAnalysis: (jobProfileId: number) => ['combinedAnalysis', jobProfileId] as const,
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

// Capability cluster analysis query
export function useCapabilityClusterAnalysis(jobProfileId: number | null) {
  return useQuery({
    queryKey: jobProfileId ? queryKeys.capabilityClusters(jobProfileId) : ['capabilityClusters', null],
    queryFn: () => api.getCapabilityClusters(jobProfileId!),
    enabled: !!jobProfileId,
    staleTime: 5 * 60 * 1000,
    select: (data) => data.analysis, // Extract just the analysis from response
  })
}

// Combined analysis query (flat skill + cluster analysis)
export function useCombinedAnalysis(jobProfileId: number | null) {
  return useQuery({
    queryKey: jobProfileId ? queryKeys.combinedAnalysis(jobProfileId) : ['combinedAnalysis', null],
    queryFn: () => api.getCombinedAnalysis(jobProfileId!),
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
    mutationFn: async ({ resume, companyName }: { resume: TailoredResume; companyName?: string }) => {
      const blob = await api.downloadResumeDocx(resume)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = generateDownloadFilename('resume', companyName, 'docx')
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}

// Download resume text mutation
export function useDownloadResumeText() {
  return useMutation({
    mutationFn: async ({ resume, companyName }: { resume: TailoredResume; companyName?: string }) => {
      const blob = await api.downloadResumeText(resume)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = generateDownloadFilename('resume', companyName, 'txt')
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
    mutationFn: async ({ coverLetter, companyName }: { coverLetter: GeneratedCoverLetter; companyName?: string }) => {
      const blob = await api.downloadCoverLetterDocx(coverLetter)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = generateDownloadFilename('cover-letter', companyName, 'docx')
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}

// Download cover letter text mutation
export function useDownloadCoverLetterText() {
  return useMutation({
    mutationFn: async ({ coverLetter, companyName }: { coverLetter: GeneratedCoverLetter; companyName?: string }) => {
      const blob = await api.downloadCoverLetterText(coverLetter)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = generateDownloadFilename('cover-letter', companyName, 'txt')
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}
