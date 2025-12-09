// User Skills and Evidence Types (Sprint 11D)

export interface BulletSummary {
  id: number
  text: string
  tags?: string[]
}

export interface EngagementSummary {
  id: number
  client?: string
  project_name?: string
  date_range_label?: string
  bullets: BulletSummary[]
}

export interface ExperienceWithDetails {
  id: number
  job_title: string
  employer_name: string
  location?: string
  start_date: string
  end_date?: string
  employer_type?: string
  tools_and_technologies?: string[]
  engagements: EngagementSummary[]
  bullets: BulletSummary[]  // Direct bullets for non-consulting
}

export interface EvidenceMapping {
  experience_id: number
  engagement_id?: number
  bullet_ids?: number[]
}

export interface AddUserSkillRequest {
  skill_name: string
  user_id?: number
  evidence_mappings: EvidenceMapping[]
}

export interface AddUserSkillResponse {
  skill_name: string
  user_id: number
  entities_updated: number
  added_at: string
}
