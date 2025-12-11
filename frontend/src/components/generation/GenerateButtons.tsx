'use client'

import { Loader2, FileText, Mail, Sparkles, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useGenerateResume, useGenerateCoverLetterWithCritic } from '@/hooks/queries'
import { useGenerationStore } from '@/stores/generation-store'
import type { TailoredResume, GeneratedCoverLetter } from '@/types'

// Helper to extract readable error message
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>
    if ('detail' in err) {
      // FastAPI validation errors return detail as an array
      if (Array.isArray(err.detail)) {
        const messages = err.detail
          .map((d: unknown) => {
            if (typeof d === 'object' && d !== null && 'msg' in d) {
              return (d as { msg: string }).msg
            }
            return String(d)
          })
          .join('; ')
        return messages || 'Validation error'
      }
      if (typeof err.detail === 'string') {
        return err.detail
      }
    }
    if ('message' in err && typeof err.message === 'string') {
      return err.message
    }
  }
  if (typeof error === 'string') {
    return error
  }
  return 'An unexpected error occurred. Please try again.'
}

interface GenerateButtonsProps {
  jobProfileId: number
  companyName?: string
  disabled?: boolean
  onResumeGenerated?: (resume: TailoredResume) => void
  onCoverLetterGenerated?: (coverLetter: GeneratedCoverLetter) => void
}

export function GenerateButtons({
  jobProfileId,
  companyName,
  disabled,
  onResumeGenerated,
  onCoverLetterGenerated,
}: GenerateButtonsProps) {
  const generateResume = useGenerateResume()
  const generateCoverLetter = useGenerateCoverLetterWithCritic()
  const { contextNotes, setResume, setCoverLetter, setGenerationStep } = useGenerationStore()

  const isGenerating = generateResume.isPending || generateCoverLetter.isPending

  const handleGenerateResume = async () => {
    setGenerationStep('generating-resume')
    const toastId = toast.loading('Generating tailored resume...', {
      description: 'Analyzing job requirements and selecting optimal content',
    })
    try {
      const result = await generateResume.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
      })
      setResume(result)
      setGenerationStep('complete')
      onResumeGenerated?.(result)
      toast.success('Resume generated successfully!', {
        id: toastId,
        description: `ATS Score: ${Math.round(result.ats_score_estimate ?? result.ats_score ?? 0)}/100`,
        icon: <CheckCircle2 className="h-4 w-4" />,
      })
    } catch (error) {
      console.error('Resume generation failed:', error)
      setGenerationStep('idle')
      toast.error('Resume generation failed', {
        id: toastId,
        description: getErrorMessage(error),
      })
    }
  }

  const handleGenerateCoverLetter = async () => {
    setGenerationStep('generating-cover-letter')
    const toastId = toast.loading('Generating cover letter...', {
      description: 'Crafting a compelling narrative for your application',
    })
    try {
      const result = await generateCoverLetter.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
        company_name: companyName || undefined,
      })
      setCoverLetter(result)
      setGenerationStep('complete')
      onCoverLetterGenerated?.(result)
      toast.success('Cover letter generated successfully!', {
        id: toastId,
        description: `Quality Score: ${Math.round(result.quality_score)}/100`,
        icon: <CheckCircle2 className="h-4 w-4" />,
      })
    } catch (error) {
      console.error('Cover letter generation failed:', error)
      setGenerationStep('idle')
      toast.error('Cover letter generation failed', {
        id: toastId,
        description: getErrorMessage(error),
      })
    }
  }

  const handleGenerateBoth = async () => {
    setGenerationStep('generating-resume')
    const toastId = toast.loading('Generating resume...', {
      description: 'Step 1 of 2: Analyzing job requirements',
    })
    try {
      const resumeResult = await generateResume.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
      })
      setResume(resumeResult)
      onResumeGenerated?.(resumeResult)

      setGenerationStep('generating-cover-letter')
      toast.loading('Generating cover letter...', {
        id: toastId,
        description: 'Step 2 of 2: Crafting your narrative',
      })

      const clResult = await generateCoverLetter.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
        company_name: companyName || undefined,
      })
      setCoverLetter(clResult)
      onCoverLetterGenerated?.(clResult)

      setGenerationStep('complete')
      toast.success('Both documents generated!', {
        id: toastId,
        description: `Resume ATS: ${Math.round(resumeResult.ats_score_estimate ?? resumeResult.ats_score ?? 0)}/100 | Cover Letter: ${Math.round(clResult.quality_score)}/100`,
        icon: <CheckCircle2 className="h-4 w-4" />,
      })
    } catch (error) {
      console.error('Generation failed:', error)
      setGenerationStep('idle')
      toast.error('Generation failed', {
        id: toastId,
        description: getErrorMessage(error),
      })
    }
  }

  return (
    <Card className="border-t-4 border-t-teal-500">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-teal-100 dark:bg-teal-900/30">
            <Sparkles className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          </div>
          Generate Materials
        </CardTitle>
        <CardDescription>
          Create tailored resume and cover letter for this position
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Button
            onClick={handleGenerateResume}
            disabled={disabled || isGenerating}
            variant="outline"
            className="w-full transition-all duration-200 hover:border-teal-300 hover:bg-teal-50/50 dark:hover:border-teal-700 dark:hover:bg-teal-950/30"
          >
            {generateResume.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FileText className="mr-2 h-4 w-4" />
            )}
            {generateResume.isPending ? 'Generating...' : 'Resume'}
          </Button>
          <Button
            onClick={handleGenerateCoverLetter}
            disabled={disabled || isGenerating}
            variant="outline"
            className="w-full transition-all duration-200 hover:border-teal-300 hover:bg-teal-50/50 dark:hover:border-teal-700 dark:hover:bg-teal-950/30"
          >
            {generateCoverLetter.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Mail className="mr-2 h-4 w-4" />
            )}
            {generateCoverLetter.isPending ? 'Generating...' : 'Cover Letter'}
          </Button>
        </div>
        <Button
          onClick={handleGenerateBoth}
          disabled={disabled || isGenerating}
          className="w-full bg-teal-600 hover:bg-teal-700 text-white transition-all duration-200"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {generateResume.isPending ? 'Generating Resume...' : 'Generating Cover Letter...'}
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Both
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
