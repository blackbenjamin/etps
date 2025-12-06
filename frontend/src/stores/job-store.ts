import { create } from 'zustand'
import type { JobProfile, SkillGapResponse } from '@/types'

interface JobState {
  currentJob: JobProfile | null
  skillGapAnalysis: SkillGapResponse | null

  setCurrentJob: (job: JobProfile | null) => void
  setSkillGapAnalysis: (analysis: SkillGapResponse | null) => void
  reset: () => void
}

export const useJobStore = create<JobState>((set) => ({
  currentJob: null,
  skillGapAnalysis: null,

  setCurrentJob: (job) => set({ currentJob: job }),
  setSkillGapAnalysis: (analysis) => set({ skillGapAnalysis: analysis }),
  reset: () => set({ currentJob: null, skillGapAnalysis: null }),
}))
