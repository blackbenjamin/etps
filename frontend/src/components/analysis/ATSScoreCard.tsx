'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CircularProgress } from '@/components/ui/circular-progress'
import { CheckCircle2, AlertTriangle, XCircle, Lightbulb } from 'lucide-react'

interface ATSScoreCardProps {
  score: number
  explanation?: string
  suggestions?: string[]
}

export function ATSScoreCard({ score, explanation, suggestions }: ATSScoreCardProps) {
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

        {/* Explanation */}
        {explanation && (
          <div className="bg-muted/50 rounded-lg p-3">
            <p className="text-sm">{explanation}</p>
          </div>
        )}

        {/* Suggestions */}
        {suggestions && suggestions.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-warning" />
              Improvement Suggestions
            </h4>
            <ul className="space-y-2">
              {suggestions.slice(0, 3).map((suggestion, idx) => (
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
