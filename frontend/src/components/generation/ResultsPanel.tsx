'use client'

import { useState } from 'react'
import { CheckCircle2, FileText, Download, ChevronDown, ChevronRight, Briefcase, Sparkles } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { DownloadButtons } from './DownloadButtons'
import { ResultsPreview } from '@/components/results'
import type { TailoredResume, GeneratedCoverLetter, SelectedRole } from '@/types'

// Format ISO date (YYYY-MM-DD) to M/YYYY
function formatDate(isoDate: string | null | undefined): string {
  if (!isoDate) return 'Present'
  const parts = isoDate.split('-')
  if (parts.length >= 2) {
    const month = parseInt(parts[1], 10)
    const year = parts[0]
    return `${month}/${year}`
  }
  return isoDate
}

// Check if role has engagements (consulting-style role)
function hasEngagements(role: SelectedRole): boolean {
  return (role.selected_engagements?.length ?? 0) > 0
}

// Count total bullets in a role
function countRoleBullets(role: SelectedRole): number {
  let count = role.selected_bullets?.length ?? 0
  if (role.selected_engagements) {
    for (const engagement of role.selected_engagements) {
      count += engagement.selected_bullets?.length ?? 0
    }
  }
  return count
}

interface ResultsPanelProps {
  resume: TailoredResume | null
  coverLetter: GeneratedCoverLetter | null
  jobProfileId: number
  companyName?: string
}

export function ResultsPanel({ resume, coverLetter, jobProfileId, companyName }: ResultsPanelProps) {
  const [expandedRoles, setExpandedRoles] = useState<Set<number>>(new Set([0])) // First role expanded by default

  if (!resume && !coverLetter) {
    return null
  }

  const toggleRole = (idx: number) => {
    setExpandedRoles(prev => {
      const next = new Set(prev)
      if (next.has(idx)) {
        next.delete(idx)
      } else {
        next.add(idx)
      }
      return next
    })
  }

  const expandAllRoles = () => {
    if (resume?.selected_roles) {
      setExpandedRoles(new Set(resume.selected_roles.map((_, i) => i)))
    }
  }

  const collapseAllRoles = () => {
    setExpandedRoles(new Set())
  }

  const allRolesExpanded = resume?.selected_roles?.length === expandedRoles.size

  return (
    <div className="space-y-6">
      {/* Results Preview Card */}
      <ResultsPreview resume={resume} coverLetter={coverLetter} />

      {/* Detailed Results */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-teal-100 dark:bg-teal-900/30">
              <FileText className="h-5 w-5 text-teal-600 dark:text-teal-400" />
            </div>
            Generated Materials
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {resume && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-success" />
                <h3 className="font-semibold">Resume</h3>
              </div>
              <div className="flex items-center gap-2">
                {(resume.ats_score_estimate ?? resume.ats_score) && (
                  <Badge
                    variant="outline"
                    className={(resume.ats_score_estimate ?? resume.ats_score)! > 75
                      ? 'border-success/30 text-success'
                      : 'border-warning/30 text-warning'}
                  >
                    ATS: {Math.round((resume.ats_score_estimate ?? resume.ats_score)!)}/100
                  </Badge>
                )}
              </div>
            </div>

            <DownloadButtons
              type="resume"
              jobProfileId={jobProfileId}
              jsonData={resume}
              companyName={companyName}
            />

            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="roles">Roles ({resume.selected_roles?.length || 0})</TabsTrigger>
                <TabsTrigger value="skills">Skills</TabsTrigger>
              </TabsList>
              <TabsContent value="summary" className="mt-4">
                <div className="bg-gradient-to-br from-teal-50/50 to-transparent dark:from-teal-950/20 p-4 rounded-lg border border-teal-100 dark:border-teal-900/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                    <span className="text-xs font-medium text-teal-600 dark:text-teal-400 uppercase tracking-wider">AI-Tailored Summary</span>
                  </div>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{resume.tailored_summary}</p>
                </div>
              </TabsContent>
              <TabsContent value="roles" className="mt-4">
                <div className="space-y-3">
                  {/* Expand/Collapse All */}
                  {resume.selected_roles && resume.selected_roles.length > 1 && (
                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={allRolesExpanded ? collapseAllRoles : expandAllRoles}
                        className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                      >
                        {allRolesExpanded ? (
                          <>
                            <ChevronDown className="h-3 w-3" />
                            Collapse All
                          </>
                        ) : (
                          <>
                            <ChevronRight className="h-3 w-3" />
                            Expand All
                          </>
                        )}
                      </button>
                    </div>
                  )}

                  {resume.selected_roles?.map((role, idx) => (
                    <Collapsible
                      key={idx}
                      open={expandedRoles.has(idx)}
                      onOpenChange={() => toggleRole(idx)}
                    >
                      <div className="rounded-lg border bg-card">
                        <CollapsibleTrigger asChild>
                          <button
                            type="button"
                            className="w-full flex items-center gap-3 p-4 hover:bg-muted/30 transition-colors rounded-t-lg text-left"
                          >
                            {expandedRoles.has(idx) ? (
                              <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            )}

                            <div className="p-1.5 rounded-lg bg-teal-100 dark:bg-teal-900/30 flex-shrink-0">
                              <Briefcase className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                            </div>

                            <div className="flex-1 min-w-0">
                              <p className="font-medium truncate">{role.job_title}</p>
                              <p className="text-sm text-muted-foreground truncate">{role.employer_name}</p>
                            </div>

                            <div className="flex items-center gap-2 flex-shrink-0">
                              <Badge variant="outline" className="text-xs">
                                {countRoleBullets(role)} bullets
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(role.start_date)} – {formatDate(role.end_date)}
                              </span>
                            </div>
                          </button>
                        </CollapsibleTrigger>

                        <CollapsibleContent>
                          <div className="px-4 pb-4 pt-0 space-y-3">
                            {role.role_summary && (
                              <p className="text-sm italic text-muted-foreground border-l-2 border-teal-200 dark:border-teal-800 pl-3">
                                {role.role_summary}
                              </p>
                            )}

                            {/* Direct bullets (non-consulting roles or role-level bullets) */}
                            {role.selected_bullets && role.selected_bullets.length > 0 && (
                              <ul className="space-y-2">
                                {role.selected_bullets.map((bullet) => (
                                  <li key={bullet.bullet_id} className="text-sm flex gap-2">
                                    <span className="text-teal-500 flex-shrink-0">•</span>
                                    <span>{bullet.text}</span>
                                  </li>
                                ))}
                              </ul>
                            )}

                            {/* Engagements (consulting-style roles) */}
                            {hasEngagements(role) && (
                              <div className="space-y-4">
                                {role.selected_engagements?.map((engagement, engIdx) => (
                                  <div key={engIdx} className="ml-2 border-l-2 border-muted pl-4">
                                    <p className="text-sm font-medium text-muted-foreground mb-2">
                                      {engagement.client}
                                    </p>
                                    {engagement.selected_bullets && engagement.selected_bullets.length > 0 && (
                                      <ul className="space-y-2">
                                        {engagement.selected_bullets.map((bullet) => (
                                          <li key={bullet.bullet_id} className="text-sm flex gap-2">
                                            <span className="text-teal-500 flex-shrink-0">•</span>
                                            <span>{bullet.text}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </CollapsibleContent>
                      </div>
                    </Collapsible>
                  ))}
                </div>
              </TabsContent>
              <TabsContent value="skills" className="mt-4">
                <div className="flex flex-wrap gap-2">
                  {resume.selected_skills?.map((skill, idx) => (
                    <Badge
                      key={idx}
                      variant="secondary"
                      className="bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/30 dark:text-teal-300 dark:border-teal-800"
                    >
                      {skill.skill}
                    </Badge>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </div>
        )}

        {coverLetter && (
          <div className={`space-y-4 ${resume ? 'pt-6 border-t' : ''}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-success" />
                <h3 className="font-semibold">Cover Letter</h3>
              </div>
              <Badge
                variant="outline"
                className={coverLetter.quality_score > 75
                  ? 'border-success/30 text-success'
                  : 'border-warning/30 text-warning'}
              >
                Quality: {Math.round(coverLetter.quality_score)}/100
              </Badge>
            </div>

            <DownloadButtons
              type="cover-letter"
              jobProfileId={jobProfileId}
              jsonData={coverLetter}
              companyName={companyName}
            />

            <div className="bg-gradient-to-br from-teal-50/50 to-transparent dark:from-teal-950/20 p-4 rounded-lg border border-teal-100 dark:border-teal-900/30">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                <span className="text-xs font-medium text-teal-600 dark:text-teal-400 uppercase tracking-wider">AI-Generated Cover Letter</span>
              </div>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {coverLetter.draft_cover_letter}
              </p>
            </div>
          </div>
        )}
        </CardContent>
      </Card>
    </div>
  )
}
