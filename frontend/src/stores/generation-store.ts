import { create } from 'zustand'
import type { TailoredResume, GeneratedCoverLetter } from '@/types'

type GenerationStep = 'idle' | 'generating-resume' | 'generating-cover-letter' | 'complete'

interface GenerationState {
  resume: TailoredResume | null
  coverLetter: GeneratedCoverLetter | null
  generationStep: GenerationStep
  contextNotes: string

  setResume: (resume: TailoredResume | null) => void
  setCoverLetter: (coverLetter: GeneratedCoverLetter | null) => void
  setGenerationStep: (step: GenerationStep) => void
  setContextNotes: (notes: string) => void
  reset: () => void
}

export const useGenerationStore = create<GenerationState>((set) => ({
  resume: null,
  coverLetter: null,
  generationStep: 'idle',
  contextNotes: '',

  setResume: (resume) => set({ resume }),
  setCoverLetter: (coverLetter) => set({ coverLetter }),
  setGenerationStep: (step) => set({ generationStep: step }),
  setContextNotes: (notes) => set({ contextNotes: notes }),
  reset: () => set({
    resume: null,
    coverLetter: null,
    generationStep: 'idle',
    contextNotes: ''
  }),
}))
