'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CircularProgress } from '@/components/ui/circular-progress'
import { CheckCircle2, AlertTriangle, XCircle, Lightbulb, FileText, Tag, ListChecks } from 'lucide-react'
import type { ATSBreakdown } from '@/types/resume'

interface ATSScoreCardProps {
  score: number
  breakdown?: ATSBreakdown
  explanation?: string
  suggestions?: string[]
}

function ScoreBar({ label, score, icon }: { label: string; score: number; icon: React.ReactNode }) {
  const getBarColor = (score: number) => {
    if (score >= 75) return 'bg-success'
    if (score >= 50) return 'bg-warning'
    return 'bg-danger'
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          {icon}
          {label}
        </span>
        <span className="font-medium">{Math.round(score)}%</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${getBarColor(score)}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
    </div>
  )
}

export function ATSScoreCard({ score, breakdown, explanation, suggestions }: ATSScoreCardProps) {
  const getScoreLabel = (score: number) => {
    if (score >= 75) return 'Excellent Match'
    if (score >= 60) return 'Good Match'
    return 'Needs Improvement'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 75) return <CheckCircle2 className="h-5 w-5 text-success" />
    if (score >= 60) return <AlertTriangle className="h-5 w-5 text-warning" />
    return <XCircle className="h-5 w-5 text-danger" />
  }

  const getScoreDescription = (score: number) => {
    if (score >= 75) return 'Your resume is well-optimized for this position.'
    if (score >= 60) return 'Your resume has a good foundation but could be improved.'
    return 'Consider tailoring your resume more closely to the job requirements.'
  }

  // Generate actionable suggestions based on breakdown
  const getBreakdownSuggestions = (): string[] => {
    if (!breakdown) return []
    const tips: string[] = []

    if (breakdown.keyword_score < 60) {
      tips.push(`Add more job-specific keywords. Missing: ${breakdown.keywords_missing.slice(0, 3).join(', ')}`)
    }
    if (breakdown.skills_score < 60) {
      tips.push('Expand your skills section to better match the job requirements')
    }
    if (breakdown.format_score < 80) {
      tips.push('Ensure all resume sections are complete and properly formatted')
    }

    return tips
  }

  const displaySuggestions = suggestions?.length ? suggestions : getBreakdownSuggestions()

  return (
    <Card className="overflow-hidden border-t-4 border-t-teal-500">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              {getScoreIcon(score)}
              ATS Compatibility Score
            </CardTitle>
            <CardDescription className="mt-1">
              {getScoreLabel(score)}
            </CardDescription>
          </div>
          <CircularProgress
            value={score}
            size="xl"
            strokeWidth={6}
            showValue
            colorScheme="auto"
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Score description */}
        <p className="text-sm text-muted-foreground">
          {getScoreDescription(score)}
        </p>

        {/* Score breakdown */}
        {breakdown && (
          <div className="space-y-3 bg-muted/30 rounded-lg p-3">
            <h4 className="font-semibold text-sm">Score Breakdown</h4>
            <div className="space-y-3">
              <ScoreBar
                label="Keywords"
                score={breakdown.keyword_score}
                icon={<Tag className="h-3.5 w-3.5" />}
              />
              <ScoreBar
                label="Skills"
                score={breakdown.skills_score}
                icon={<ListChecks className="h-3.5 w-3.5" />}
              />
              <ScoreBar
                label="Format"
                score={breakdown.format_score}
                icon={<FileText className="h-3.5 w-3.5" />}
              />
            </div>
            {breakdown.keywords_matched > 0 && (
              <p className="text-xs text-muted-foreground mt-2">
                Matched {breakdown.keywords_matched} of {breakdown.total_keywords} keywords
              </p>
            )}
          </div>
        )}

        {/* Explanation */}
        {explanation && (
          <div className="bg-muted/50 rounded-lg p-3">
            <p className="text-sm">{explanation}</p>
          </div>
        )}

        {/* Missing keywords */}
        {breakdown?.keywords_missing && breakdown.keywords_missing.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm text-danger">Missing Keywords</h4>
            <div className="flex flex-wrap gap-1.5">
              {breakdown.keywords_missing.slice(0, 5).map((keyword, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-1 bg-danger/10 text-danger rounded-full"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Suggestions */}
        {displaySuggestions && displaySuggestions.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-warning" />
              Improvement Suggestions
            </h4>
            <ul className="space-y-2">
              {displaySuggestions.slice(0, 3).map((suggestion, idx) => (
                <li
                  key={idx}
                  className="text-sm text-muted-foreground flex items-start gap-2 bg-muted/30 rounded-md p-2"
                >
                  <span className="text-teal-600 font-medium shrink-0">{idx + 1}.</span>
                  {suggestion}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
