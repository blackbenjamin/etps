// Capability Cluster Types (Sprint 11)
// Three-tier capability model for strategic role matching

export interface EvidenceSkill {
  name: string
  category: 'tech' | 'domain' | 'soft_skill' | 'methodology'
  matched: boolean
  confidence: number
  evidence_bullet_ids: string[]
}

export interface ComponentSkill {
  name: string
  description?: string
  evidence_skills: EvidenceSkill[]
  required: boolean
  matched: boolean
  match_strength: number
  evidence_bullet_ids: string[]
}

export interface CapabilityCluster {
  name: string
  description: string
  component_skills: ComponentSkill[]
  importance: 'critical' | 'important' | 'nice-to-have'
  match_percentage: number
  user_evidence: string[]
  gaps: string[]
  positioning?: string
  is_expanded: boolean
}

export interface CapabilityClusterAnalysis {
  job_profile_id: number
  user_id: number
  clusters: CapabilityCluster[]
  overall_match_score: number
  recommendation: 'strong_match' | 'moderate_match' | 'stretch_role' | 'weak_match'
  positioning_summary: string
  key_strengths: string[]
  critical_gaps: string[]
  analysis_timestamp?: string
  cache_key?: string
}

export interface CapabilityClusterRequest {
  job_profile_id: number
  user_id?: number
  force_refresh?: boolean
}

export interface CapabilityClusterResponse {
  analysis: CapabilityClusterAnalysis
  cached: boolean
  cache_expires_at?: string
}

export interface KeySkillSelection {
  cluster_name: string
  skill_name: string
  selected: boolean
}

export interface CapabilitySelectionUpdate {
  job_profile_id: number
  key_skills: KeySkillSelection[]
  cluster_expansions?: Record<string, boolean>
}
