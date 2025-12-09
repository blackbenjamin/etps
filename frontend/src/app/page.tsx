'use client'

import { useEffect, useState } from 'react'
import { JobIntakeForm } from '@/components/job-intake'
import { GenerateButtons, ResultsPanel } from '@/components/generation'
import { ATSScoreCard } from '@/components/analysis'
import { SkillSelectionPanel } from '@/components/skills'
import { CapabilityClusterPanel } from '@/components/capability/CapabilityClusterPanel'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Pencil, Check } from 'lucide-react'
import { useJobStore } from '@/stores/job-store'
import { useGenerationStore } from '@/stores/generation-store'
import { useSkillGapAnalysis, useCapabilityClusterAnalysis } from '@/hooks/queries'
import type { JobProfile } from '@/types'

// Helper to safely get job profile ID from either field
function getJobId(job: JobProfile | null): number | null {
  if (!job) return null
  return job.job_profile_id ?? job.id ?? null
}

export default function Home() {
  const { currentJob, setCurrentJob, setSkillGapAnalysis } = useJobStore()
  const { resume, coverLetter } = useGenerationStore()
  const [editingCompany, setEditingCompany] = useState(false)
  const [companyNameInput, setCompanyNameInput] = useState('')

  // Get the job ID safely
  const jobId = getJobId(currentJob)

  // Sync company name input when job changes
  useEffect(() => {
    setCompanyNameInput(currentJob?.company_name || '')
    setEditingCompany(false)
  }, [currentJob?.job_profile_id])

  // Handle saving edited company name
  const handleSaveCompanyName = () => {
    if (currentJob && companyNameInput.trim()) {
      setCurrentJob({ ...currentJob, company_name: companyNameInput.trim() })
    }
    setEditingCompany(false)
  }

  // Auto-fetch skill gap when job is parsed
  const { data: skillGap, isLoading: isAnalyzing } = useSkillGapAnalysis(jobId)

  // Auto-fetch capability cluster analysis
  const { data: clusterAnalysis, isLoading: isAnalyzingClusters } = useCapabilityClusterAnalysis(jobId)

  useEffect(() => {
    if (skillGap) {
      setSkillGapAnalysis(skillGap)
    }
  }, [skillGap, setSkillGapAnalysis])

  return (
    <main className="min-h-screen bg-background">
      {/* Header - Sticky */}
      <header className="border-b bg-card sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">ETPS</h1>
          <p className="text-sm text-muted-foreground">
            Enterprise Talent Positioning System
          </p>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Input & Generation - Sticky on large screens */}
          <div className="space-y-6 lg:sticky lg:top-[85px] lg:self-start lg:max-h-[calc(100vh-100px)] lg:overflow-y-auto">
            <JobIntakeForm />

            {currentJob && (
              <>
                {/* Job Details Card */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Job Details</span>
                      {currentJob.seniority && (
                        <Badge variant="outline">{currentJob.seniority}</Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-muted-foreground">Title</p>
                        <p className="font-medium">{currentJob.job_title || 'Unknown Position'}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Company</p>
                        {editingCompany ? (
                          <div className="flex items-center gap-1">
                            <Input
                              value={companyNameInput}
                              onChange={(e) => setCompanyNameInput(e.target.value)}
                              placeholder="Enter company name"
                              className="h-7 text-sm"
                              onKeyDown={(e) => e.key === 'Enter' && handleSaveCompanyName()}
                              autoFocus
                            />
                            <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={handleSaveCompanyName}>
                              <Check className="h-4 w-4" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <p className="font-medium">{currentJob.company_name || 'Not specified'}</p>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
                              onClick={() => {
                                setCompanyNameInput(currentJob.company_name || '')
                                setEditingCompany(true)
                              }}
                            >
                              <Pencil className="h-3 w-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                      {currentJob.location && (
                        <div>
                          <p className="text-muted-foreground">Location</p>
                          <p className="font-medium">{currentJob.location}</p>
                        </div>
                      )}
                      {currentJob.extracted_skills && currentJob.extracted_skills.length > 0 && (
                        <div className="col-span-2">
                          <p className="text-muted-foreground mb-1">Key Skills</p>
                          <div className="flex flex-wrap gap-1">
                            {currentJob.extracted_skills.slice(0, 8).map((skill, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                            {currentJob.extracted_skills.length > 8 && (
                              <Badge variant="outline" className="text-xs">
                                +{currentJob.extracted_skills.length - 8} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Generate Buttons */}
                {jobId && (
                  <GenerateButtons jobProfileId={jobId} companyName={currentJob.company_name} />
                )}
              </>
            )}
          </div>

          {/* Right Column: Analysis & Results */}
          <div className="space-y-6">
            {/* Capability Cluster Analysis (Sprint 11 - strategic capability matching) */}
            {(currentJob || isAnalyzingClusters) && jobId && (
              <CapabilityClusterPanel
                analysis={clusterAnalysis ?? null}
                isLoading={isAnalyzingClusters}
              />
            )}

            {/* Skill Selection Panel (Sprint 10E - flat skill matching) */}
            {(currentJob || isAnalyzing) && jobId && (
              <SkillSelectionPanel
                jobProfileId={jobId}
                analysis={skillGap ?? null}
                isLoading={isAnalyzing}
              />
            )}

            {/* ATS Score */}
            {(resume?.ats_score_estimate ?? resume?.ats_score) && (
              <ATSScoreCard
                score={(resume.ats_score_estimate ?? resume.ats_score)!}
                explanation={resume.tailoring_rationale ?? resume.rationale?.summary_approach}
                suggestions={resume.critic_result?.improvement_suggestions}
              />
            )}

            {/* Results Panel */}
            {currentJob && jobId && (
              <ResultsPanel
                resume={resume}
                coverLetter={coverLetter}
                jobProfileId={jobId}
                companyName={currentJob.company_name}
              />
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
