export interface SkillMatch {
  skill: string
  match_strength: number
  evidence: string[]
  user_skill?: string
}

export interface SkillGap {
  skill: string
  importance: 'critical' | 'important' | 'nice-to-have'
  positioning_strategy: string
}

export interface WeakSignal {
  skill: string
  current_evidence?: string[]
  evidence?: string[] // Alias for compatibility
  strengthening_strategy?: string
}

export interface SkillGapRequest {
  job_profile_id: number
  user_id?: number
}

export interface SkillGapResponse {
  job_profile_id: number
  user_id: number
  skill_match_score: number
  recommendation: 'strong_match' | 'moderate_match' | 'weak_match' | 'stretch_role'
  confidence: number
  matched_skills: SkillMatch[]
  skill_gaps: SkillGap[]
  weak_signals: WeakSignal[]
  key_positioning_angles: string[]
  bullet_selection_guidance: Record<string, string[]>
  cover_letter_hooks: string[]
  user_advantages: string[]
  potential_concerns: string[]
  mitigation_strategies: Record<string, string>
  analysis_timestamp: string
}
