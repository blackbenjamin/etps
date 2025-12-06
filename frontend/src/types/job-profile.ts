export interface JobProfile {
  id?: number // Some responses use job_profile_id instead
  user_id?: number
  company_id?: number
  job_profile_id?: number // Primary ID returned by parse endpoint
  raw_jd_text: string
  jd_url?: string
  job_title: string
  company_name?: string
  location?: string
  seniority?: string
  responsibilities?: string
  requirements?: string
  nice_to_haves?: string
  extracted_skills?: string[]
  core_priorities?: string[]
  must_have_capabilities?: string[]
  nice_to_have_capabilities?: string[]
  skill_gap_analysis?: Record<string, unknown>
  tone_style?: string
  job_type_tags?: string[]
  created_at: string
  updated_at?: string
}

export interface JobParseRequest {
  jd_text?: string
  jd_url?: string
  user_id: number
}

export interface JobParseResponse extends JobProfile {}
