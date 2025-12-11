'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FileText, Mail, CheckCircle2, Sparkles } from 'lucide-react'
import { CircularProgress } from '@/components/ui/circular-progress'
import type { TailoredResume, GeneratedCoverLetter } from '@/types'

interface ResultsPreviewProps {
  resume: TailoredResume | null
  coverLetter: GeneratedCoverLetter | null
}

export function ResultsPreview({ resume, coverLetter }: ResultsPreviewProps) {
  if (!resume && !coverLetter) return null

  const resumeScore = resume?.ats_score_estimate ?? resume?.ats_score
  const coverLetterScore = coverLetter?.quality_score

  return (
    <Card className="overflow-hidden border-t-4 border-t-success bg-gradient-to-br from-success/5 via-background to-teal-500/5">
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <div className="p-2 rounded-lg bg-success/10">
            <CheckCircle2 className="h-5 w-5 text-success" />
          </div>
          <div>
            <h3 className="font-semibold text-lg">Generation Complete</h3>
            <p className="text-sm text-muted-foreground">Your materials are ready for download</p>
          </div>
          <Badge className="ml-auto bg-success/10 text-success border-success/20">
            <Sparkles className="h-3 w-3 mr-1" />
            AI Generated
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Resume Preview */}
          {resume && (
            <div className="flex flex-col items-center gap-3 p-4 rounded-lg bg-muted/30 border">
              <div className="p-3 rounded-full bg-teal-100 dark:bg-teal-900/30">
                <FileText className="h-6 w-6 text-teal-600 dark:text-teal-400" />
              </div>
              <div className="text-center">
                <p className="font-semibold">Resume</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {resume.selected_roles?.length || 0} roles &bull; {resume.selected_skills?.length || 0} skills
                </p>
              </div>
              {resumeScore && (
                <CircularProgress
                  value={resumeScore}
                  size="lg"
                  strokeWidth={6}
                  showValue
                  showLabel
                  label="ATS"
                  colorScheme="auto"
                />
              )}
            </div>
          )}

          {/* Cover Letter Preview */}
          {coverLetter && (
            <div className="flex flex-col items-center gap-3 p-4 rounded-lg bg-muted/30 border">
              <div className="p-3 rounded-full bg-teal-100 dark:bg-teal-900/30">
                <Mail className="h-6 w-6 text-teal-600 dark:text-teal-400" />
              </div>
              <div className="text-center">
                <p className="font-semibold">Cover Letter</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {coverLetter.draft_cover_letter?.split(' ').length || 0} words
                </p>
              </div>
              {coverLetterScore && (
                <CircularProgress
                  value={coverLetterScore}
                  size="lg"
                  strokeWidth={6}
                  showValue
                  showLabel
                  label="Quality"
                  colorScheme="auto"
                />
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
