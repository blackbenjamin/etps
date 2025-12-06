'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ATSScoreCardProps {
  score: number
  explanation?: string
  suggestions?: string[]
}

export function ATSScoreCard({ score, explanation, suggestions }: ATSScoreCardProps) {
  const getScoreStyle = (score: number) => {
    if (score > 75) return 'border-green-300 bg-green-50 dark:bg-green-900/20'
    if (score >= 60) return 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/20'
    return 'border-red-300 bg-red-50 dark:bg-red-900/20'
  }

  const getScoreColor = (score: number) => {
    if (score > 75) return 'text-green-700 dark:text-green-300'
    if (score >= 60) return 'text-yellow-700 dark:text-yellow-300'
    return 'text-red-700 dark:text-red-300'
  }

  const getScoreLabel = (score: number) => {
    if (score > 75) return 'Excellent'
    if (score >= 60) return 'Good'
    return 'Needs Improvement'
  }

  return (
    <Card className={`border-2 ${getScoreStyle(score)}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">ATS Compatibility</CardTitle>
          <div className={`text-3xl font-bold ${getScoreColor(score)}`}>
            {Math.round(score)}
          </div>
        </div>
        <CardDescription className={getScoreColor(score)}>
          {getScoreLabel(score)}
        </CardDescription>
      </CardHeader>
      {(explanation || (suggestions && suggestions.length > 0)) && (
        <CardContent className="space-y-3">
          {explanation && (
            <p className="text-sm">{explanation}</p>
          )}
          {suggestions && suggestions.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Suggestions</h4>
              <ul className="space-y-1 text-sm list-disc list-inside">
                {suggestions.slice(0, 3).map((suggestion, idx) => (
                  <li key={idx} className="text-muted-foreground">{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
