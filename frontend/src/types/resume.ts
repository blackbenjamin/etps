export interface SelectedBullet {
  bullet_id: number
  text: string
  relevance_score: number
  was_rewritten: boolean
  original_text?: string
  tags: string[]
  selection_reason: string
  engagement_id?: number
}

export interface SelectedEngagement {
  engagement_id: number
  client?: string
  project_name?: string
  date_range_label?: string
  selected_bullets: SelectedBullet[]
}

export interface SelectedRole {
  experience_id: number
  job_title: string
  employer_name: string
  location?: string
  start_date: string
  end_date?: string
  employer_type?: string
  role_summary?: string
  selected_bullets: SelectedBullet[]
  selected_engagements: SelectedEngagement[]
  bullet_selection_rationale: string
}

export interface SelectedSkill {
  skill: string
  priority_score: number
  match_type: 'direct_match' | 'adjacent_skill' | 'transferable'
  source: string
}

export interface TailoringRationale {
  summary_approach: string
  bullet_selection_strategy: string
  skills_ordering_logic: string
  role_emphasis: Record<number, string>
  gaps_addressed: string[]
  strengths_highlighted: string[]
}

export interface ATSBreakdown {
  keyword_score: number
  format_score: number
  skills_score: number
  total_keywords: number
  keywords_matched: number
  keywords_missing: string[]
}

export interface TailoredResume {
  job_profile_id: number
  user_id: number
  application_id?: number
  tailored_summary: string
  selected_roles: SelectedRole[]
  selected_skills: SelectedSkill[]
  rationale: TailoringRationale
  skill_gap_summary?: Record<string, unknown>
  ats_score_estimate?: number
  ats_breakdown?: ATSBreakdown
  match_score: number
  generated_at: string
  constraints_validated: boolean
  // Frontend-only field for backward compatibility
  tailoring_rationale?: string
  // Frontend-only alias for ats_score_estimate
  ats_score?: number
  critic_result?: import('./api').CriticResult
}

export interface ResumeGenerateRequest {
  job_profile_id: number
  user_id?: number
  context_notes?: string
}
