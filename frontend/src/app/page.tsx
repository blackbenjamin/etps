'use client'

import { useEffect, useState, useRef } from 'react'
import { JobIntakeForm } from '@/components/job-intake'
import { GenerateButtons, ResultsPanel } from '@/components/generation'
import { ATSScoreCard } from '@/components/analysis'
import { SkillSelectionPanel } from '@/components/skills'
import { CapabilityClusterPanel } from '@/components/capability/CapabilityClusterPanel'
import { HeroSection } from '@/components/hero'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Pencil, Check, Briefcase, Building2, MapPin, Award } from 'lucide-react'
import { useJobStore } from '@/stores/job-store'
import { useGenerationStore } from '@/stores/generation-store'
import { useSkillGapAnalysis, useCapabilityClusterAnalysis } from '@/hooks/queries'
import { api } from '@/lib/api'
import type { JobProfile } from '@/types'

// Helper to safely get job profile ID from either field
function getJobId(job: JobProfile | null): number | null {
  if (!job) return null
  return job.job_profile_id ?? job.id ?? null
}

export default function Home() {
  const { currentJob, setCurrentJob, setSkillGapAnalysis } = useJobStore()
  const { resume, coverLetter } = useGenerationStore()

  // Ref for scrolling to intake form
  const intakeFormRef = useRef<HTMLDivElement>(null)

  // Handler for hero CTA clicks
  const handleGetStarted = () => {
    intakeFormRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // Editable fields state
  const [editingCompany, setEditingCompany] = useState(false)
  const [companyNameInput, setCompanyNameInput] = useState('')
  const [editingJobTitle, setEditingJobTitle] = useState(false)
  const [jobTitleInput, setJobTitleInput] = useState('')
  const [editingLocation, setEditingLocation] = useState(false)
  const [locationInput, setLocationInput] = useState('')

  // Get the job ID safely
  const jobId = getJobId(currentJob)

  // Sync editable inputs when job changes
  useEffect(() => {
    setCompanyNameInput(currentJob?.company_name || '')
    setEditingCompany(false)
    setJobTitleInput(currentJob?.job_title || '')
    setEditingJobTitle(false)
    setLocationInput(currentJob?.location || '')
    setEditingLocation(false)
  }, [currentJob?.job_profile_id])

  // Handle saving edited company name
  const handleSaveCompanyName = () => {
    if (currentJob && companyNameInput.trim()) {
      setCurrentJob({ ...currentJob, company_name: companyNameInput.trim() })
    }
    setEditingCompany(false)
  }

  // Handle saving edited job title
  const handleSaveJobTitle = () => {
    if (currentJob && jobTitleInput.trim()) {
      setCurrentJob({ ...currentJob, job_title: jobTitleInput.trim() })
    }
    setEditingJobTitle(false)
  }

  // Handle saving edited location
  const handleSaveLocation = () => {
    if (currentJob) {
      setCurrentJob({ ...currentJob, location: locationInput.trim() || undefined })
    }
    setEditingLocation(false)
  }

  // Auto-fetch skill gap when job is parsed
  const { data: skillGap, isLoading: isAnalyzing } = useSkillGapAnalysis(jobId)

  // Auto-fetch capability cluster analysis
  const { data: clusterAnalysis, isLoading: isAnalyzingClusters, refetch: refetchClusterAnalysis } = useCapabilityClusterAnalysis(jobId)

  useEffect(() => {
    if (skillGap) {
      setSkillGapAnalysis(skillGap)
    }
  }, [skillGap, setSkillGapAnalysis])

  // Handler to re-run capability cluster analysis with force_refresh
  const handleRerunAnalysis = async () => {
    if (!jobId) return

    // Call the analyze endpoint with force_refresh=true
    await api.analyzeCapabilityClusters({
      job_profile_id: jobId,
      force_refresh: true
    })

    // Refetch to update the UI with new results
    await refetchClusterAnalysis()
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Header - Sticky with enterprise gradient */}
      <header className="border-b bg-gradient-to-r from-enterprise-navy to-enterprise-navy-light sticky top-0 z-50 shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Logo mark */}
              <div className="w-10 h-10 rounded-lg bg-teal-600 flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">E</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight">ETPS</h1>
                <p className="text-xs text-white/70">
                  Enterprise-Grade Talent Positioning System
                </p>
              </div>
            </div>
            {/* Portfolio badge */}
            <Badge
              variant="outline"
              className="hidden sm:flex text-white/80 border-white/30 hover:bg-white/10 transition-colors"
            >
              Portfolio Project by Benjamin Black
            </Badge>
          </div>
        </div>
      </header>

      {/* Hero Section - Show when no job loaded */}
      {!currentJob && (
        <HeroSection onGetStarted={handleGetStarted} />
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Input & Generation - Sticky on large screens */}
          <div className="space-y-6 lg:sticky lg:top-[85px] lg:self-start lg:max-h-[calc(100vh-100px)] lg:overflow-y-auto">
            <div ref={intakeFormRef}>
              <JobIntakeForm />
            </div>

            {currentJob && (
              <>
                {/* Job Details Card - Redesigned */}
                <Card className="overflow-hidden border-l-4 border-l-teal-500">
                  <CardHeader className="pb-3 bg-gradient-to-r from-muted/50 to-transparent">
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-teal-100 dark:bg-teal-900/30">
                          <Briefcase className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                        </div>
                        <span>Job Details</span>
                      </div>
                      {currentJob.seniority && (
                        <Badge className="bg-teal-100 text-teal-700 border-teal-300 dark:bg-teal-900/30 dark:text-teal-300">
                          {currentJob.seniority}
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4 space-y-4 text-sm">
                    {/* Title Field */}
                    <div className="flex items-start gap-3">
                      <Award className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Position</p>
                        {editingJobTitle ? (
                          <div className="flex items-center gap-1">
                            <Input
                              value={jobTitleInput}
                              onChange={(e) => setJobTitleInput(e.target.value)}
                              placeholder="Enter job title"
                              className="h-8 text-sm"
                              onKeyDown={(e) => e.key === 'Enter' && handleSaveJobTitle()}
                              autoFocus
                            />
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 hover:bg-teal-100 dark:hover:bg-teal-900/30" onClick={handleSaveJobTitle}>
                              <Check className="h-4 w-4 text-teal-600" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 group">
                            <p className="font-medium truncate">{currentJob.job_title || 'Unknown Position'}</p>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-teal-600"
                              onClick={() => {
                                setJobTitleInput(currentJob.job_title || '')
                                setEditingJobTitle(true)
                              }}
                            >
                              <Pencil className="h-3 w-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Company Field */}
                    <div className="flex items-start gap-3">
                      <Building2 className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Company</p>
                        {editingCompany ? (
                          <div className="flex items-center gap-1">
                            <Input
                              value={companyNameInput}
                              onChange={(e) => setCompanyNameInput(e.target.value)}
                              placeholder="Enter company name"
                              className="h-8 text-sm"
                              onKeyDown={(e) => e.key === 'Enter' && handleSaveCompanyName()}
                              autoFocus
                            />
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 hover:bg-teal-100 dark:hover:bg-teal-900/30" onClick={handleSaveCompanyName}>
                              <Check className="h-4 w-4 text-teal-600" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 group">
                            <p className="font-medium truncate">{currentJob.company_name || 'Not specified'}</p>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-teal-600"
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
                    </div>

                    {/* Location Field */}
                    <div className="flex items-start gap-3">
                      <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Location</p>
                        {editingLocation ? (
                          <div className="flex items-center gap-1">
                            <Input
                              value={locationInput}
                              onChange={(e) => setLocationInput(e.target.value)}
                              placeholder="Enter location"
                              className="h-8 text-sm"
                              onKeyDown={(e) => e.key === 'Enter' && handleSaveLocation()}
                              autoFocus
                            />
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 hover:bg-teal-100 dark:hover:bg-teal-900/30" onClick={handleSaveLocation}>
                              <Check className="h-4 w-4 text-teal-600" />
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 group">
                            <p className="font-medium truncate">{currentJob.location || 'Not specified'}</p>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-teal-600"
                              onClick={() => {
                                setLocationInput(currentJob.location || '')
                                setEditingLocation(true)
                              }}
                            >
                              <Pencil className="h-3 w-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Key Skills */}
                    {currentJob.extracted_skills && currentJob.extracted_skills.length > 0 && (
                      <div className="pt-2 border-t">
                        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Key Skills</p>
                        <div className="flex flex-wrap gap-1.5">
                          {currentJob.extracted_skills.slice(0, 8).map((skill, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className="text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 transition-colors"
                            >
                              {skill}
                            </Badge>
                          ))}
                          {currentJob.extracted_skills.length > 8 && (
                            <Badge variant="outline" className="text-xs text-muted-foreground">
                              +{currentJob.extracted_skills.length - 8} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
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
                jobProfileId={jobId}
                onRerunAnalysis={handleRerunAnalysis}
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
