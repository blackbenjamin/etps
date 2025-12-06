'use client'

import { CheckCircle2, AlertCircle, XCircle, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import type { SkillGapResponse } from '@/types'

interface SkillGapPanelProps {
  analysis: SkillGapResponse | null
  isLoading?: boolean
}

export function SkillGapPanel({ analysis, isLoading }: SkillGapPanelProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            Analyzing Skill Gap...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Progress value={undefined} className="w-full" />
        </CardContent>
      </Card>
    )
  }

  if (!analysis) return null

  const getRecommendationStyle = (rec: string) => {
    if (rec === 'strong_match') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    if (rec === 'moderate_match') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
  }

  const getRecommendationLabel = (rec: string) => {
    if (rec === 'strong_match') return 'Strong Match'
    if (rec === 'moderate_match') return 'Moderate Match'
    return 'Stretch Role'
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Skill Gap Analysis</CardTitle>
          <Badge className={getRecommendationStyle(analysis.recommendation)}>
            {Math.round(analysis.skill_match_score || 0)}% Match
          </Badge>
        </div>
        <CardDescription>
          {getRecommendationLabel(analysis.recommendation)}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Matched Skills */}
        {analysis.matched_skills && analysis.matched_skills.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              Matched Skills ({analysis.matched_skills.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {analysis.matched_skills.map((skill, idx) => (
                <Badge key={idx} variant="default" className="bg-green-600">
                  {skill.skill} ({Math.round((skill.match_strength || 0) * 100)}%)
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Weak Signals */}
        {analysis.weak_signals && analysis.weak_signals.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              Weak Signals ({analysis.weak_signals.length})
            </h4>
            <div className="space-y-2">
              {analysis.weak_signals.slice(0, 3).map((signal, idx) => (
                <div key={idx} className="text-sm bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded">
                  <p className="font-medium">{signal.skill}</p>
                  {((signal.current_evidence && signal.current_evidence[0]) || (signal.evidence && signal.evidence[0])) && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {signal.current_evidence?.[0] || signal.evidence?.[0]}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skill Gaps */}
        {analysis.skill_gaps && analysis.skill_gaps.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-600" />
              Skill Gaps ({analysis.skill_gaps.length})
            </h4>
            <div className="space-y-2">
              {analysis.skill_gaps.slice(0, 3).map((gap, idx) => (
                <div key={idx} className="text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{gap.skill}</p>
                    <Badge variant="outline" className="text-xs">
                      {gap.importance}
                    </Badge>
                  </div>
                  {gap.positioning_strategy && (
                    <p className="text-xs text-muted-foreground mt-1">
                      💡 {gap.positioning_strategy}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cover Letter Hooks */}
        {analysis.cover_letter_hooks && analysis.cover_letter_hooks.length > 0 && (
          <div className="space-y-2 pt-4 border-t">
            <h4 className="font-semibold text-sm">Cover Letter Hooks</h4>
            <ul className="space-y-1">
              {analysis.cover_letter_hooks.slice(0, 3).map((hook, idx) => (
                <li key={idx} className="text-sm text-muted-foreground flex gap-2">
                  <span>•</span>
                  <span>{hook}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
