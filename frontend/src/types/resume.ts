export interface SelectedBullet {
  id: number
  text: string
  relevance_score: number
  tags?: string[]
}

export interface SelectedRole {
  experience_id: number
  employer_name: string
  job_title: string
  start_date: string
  end_date?: string
  selected_bullets: SelectedBullet[]
}

export interface SelectedSkill {
  skill: string
  priority_score: number
  match_type: 'direct_match' | 'adjacent_skill' | 'transferable'
  source: string
}

export interface TailoredResume {
  job_profile_id: number
  tailored_summary: string
  selected_roles: SelectedRole[]
  selected_skills: SelectedSkill[]
  tailoring_rationale: string
  ats_score?: number
  critic_result?: import('./api').CriticResult
  generated_at: string
}

export interface ResumeGenerateRequest {
  job_profile_id: number
  user_id?: number
  context_notes?: string
}
