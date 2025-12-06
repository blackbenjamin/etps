'use client'

import { useState } from 'react'
import { Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ContextNotesField } from './ContextNotesField'
import { useParseJobDescription } from '@/hooks/queries'
import { useJobStore } from '@/stores/job-store'
import { useGenerationStore } from '@/stores/generation-store'
import type { JobProfile } from '@/types'

interface JobIntakeFormProps {
  onJobParsed?: (job: JobProfile) => void
}

// Helper to extract readable error message
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>
    // Handle API error objects with detail field
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

export function JobIntakeForm({ onJobParsed }: JobIntakeFormProps) {
  const [jdText, setJdText] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [contextNotes, setContextNotes] = useState('')

  // Debug logging
  console.log('JobIntakeForm rendered', { jdLength: jdText.length, hasUrl: !!sourceUrl })

  const parseJob = useParseJobDescription()
  const { setCurrentJob } = useJobStore()
  const { setContextNotes: setStoreContextNotes, reset: resetGeneration } = useGenerationStore()

  const handleParse = async () => {
    console.log('handleParse called', { jdTextLength: jdText.length, sourceUrl })
    // Allow parsing if we have JD text OR a valid URL
    if (!jdText.trim() && !sourceUrl.trim()) return

    try {
      const result = await parseJob.mutateAsync({
        jd_text: jdText || undefined,
        jd_url: sourceUrl || undefined,
        user_id: 1, // Default user for single-user mode
      })

      // Store in Zustand
      setCurrentJob(result)
      setStoreContextNotes(contextNotes)

      // Reset any previous generation results
      resetGeneration()

      onJobParsed?.(result)
    } catch (error) {
      console.error('Job parsing failed:', error)
      // Error displayed via mutation state below
    }
  }

  // Allow parsing if JD text is 50+ chars OR if a valid URL is provided
  const hasValidUrl = sourceUrl.trim().length > 0 && /^https?:\/\/.+/.test(sourceUrl.trim())
  const hasValidText = jdText.trim().length >= 50
  const canParse = hasValidText || hasValidUrl

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Description</CardTitle>
        <CardDescription>
          Paste the job description text to analyze and generate tailored materials
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste the full job description here...

Include:
• Job title and company
• Requirements and qualifications
• Responsibilities
• Nice-to-haves"
            rows={12}
            className="flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm font-mono"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{jdText.length} characters</span>
            <span>
              {hasValidText
                ? '✓ Ready to parse'
                : hasValidUrl
                  ? '✓ URL provided - ready to parse'
                  : 'Paste 50+ characters or provide a URL'}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <Input
            type="url"
            placeholder="Job posting URL (optional, for reference)"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
          />
        </div>

        <ContextNotesField value={contextNotes} onChange={setContextNotes} />

        <Button
          onClick={handleParse}
          disabled={!canParse || parseJob.isPending}
          className="w-full"
          size="lg"
        >
          {parseJob.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Parsing Job Description...
            </>
          ) : (
            'Parse Job Description'
          )}
        </Button>

        {parseJob.isError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Parsing Failed</AlertTitle>
            <AlertDescription>
              {getErrorMessage(parseJob.error)}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
