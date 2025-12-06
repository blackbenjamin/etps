export interface CoverLetterOutline {
  introduction: string
  value_proposition: string
  alignment: string
  call_to_action: string
}

export interface GeneratedCoverLetter {
  job_profile_id: number
  draft_cover_letter: string
  outline: CoverLetterOutline
  banned_phrase_check: {
    violations_found: number
    passed: boolean
    violations?: Array<{ phrase: string; severity: string }>
  }
  tone_compliance: {
    compliance_score: number
    compatible: boolean
  }
  ats_keyword_coverage: {
    coverage_percentage: number
    covered_keywords: string[]
    missing_keywords?: string[]
  }
  requirements_covered: string[]
  quality_score: number
  critic_result?: import('./api').CriticResult
  generated_at: string
}

export interface CoverLetterGenerateRequest {
  job_profile_id: number
  user_id?: number
  company_profile_id?: number
  context_notes?: string
}
