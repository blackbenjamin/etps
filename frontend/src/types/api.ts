// API error and response types
export interface ApiError {
  detail: string
  status?: number
}

export interface CriticIssue {
  severity: 'critical' | 'major' | 'minor'
  category: string
  message: string
  location?: string
}

export interface CriticResult {
  passed: boolean
  quality_score: number
  issues: CriticIssue[]
  improvement_suggestions: string[]
}
