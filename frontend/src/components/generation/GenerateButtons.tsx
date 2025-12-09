'use client'

import { Loader2, FileText, Mail, Sparkles, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
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
    try {
      const result = await generateResume.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
      })
      setResume(result)
      setGenerationStep('complete')
      onResumeGenerated?.(result)
    } catch (error) {
      console.error('Resume generation failed:', error)
      setGenerationStep('idle')
    }
  }

  const handleGenerateCoverLetter = async () => {
    setGenerationStep('generating-cover-letter')
    try {
      const result = await generateCoverLetter.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
        company_name: companyName || undefined,
      })
      setCoverLetter(result)
      setGenerationStep('complete')
      onCoverLetterGenerated?.(result)
    } catch (error) {
      console.error('Cover letter generation failed:', error)
      setGenerationStep('idle')
    }
  }

  const handleGenerateBoth = async () => {
    setGenerationStep('generating-resume')
    try {
      const resumeResult = await generateResume.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
      })
      setResume(resumeResult)
      onResumeGenerated?.(resumeResult)

      setGenerationStep('generating-cover-letter')
      const clResult = await generateCoverLetter.mutateAsync({
        job_profile_id: jobProfileId,
        context_notes: contextNotes || undefined,
        company_name: companyName || undefined,
      })
      setCoverLetter(clResult)
      onCoverLetterGenerated?.(clResult)

      setGenerationStep('complete')
    } catch (error) {
      console.error('Generation failed:', error)
      setGenerationStep('idle')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
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
            className="w-full"
          >
            {generateResume.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FileText className="mr-2 h-4 w-4" />
            )}
            Resume
          </Button>
          <Button
            onClick={handleGenerateCoverLetter}
            disabled={disabled || isGenerating}
            variant="outline"
            className="w-full"
          >
            {generateCoverLetter.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Mail className="mr-2 h-4 w-4" />
            )}
            Cover Letter
          </Button>
        </div>
        <Button
          onClick={handleGenerateBoth}
          disabled={disabled || isGenerating}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Both
            </>
          )}
        </Button>

        {(generateResume.isError || generateCoverLetter.isError) && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Generation Failed</AlertTitle>
            <AlertDescription>
              {getErrorMessage(generateResume.error || generateCoverLetter.error)}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
