'use client'

import { CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DownloadButtons } from './DownloadButtons'
import type { TailoredResume, GeneratedCoverLetter } from '@/types'

interface ResultsPanelProps {
  resume: TailoredResume | null
  coverLetter: GeneratedCoverLetter | null
  jobProfileId: number
  companyName?: string
}

export function ResultsPanel({ resume, coverLetter, jobProfileId, companyName }: ResultsPanelProps) {
  if (!resume && !coverLetter) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generated Materials</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {resume && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold">Resume</h3>
              </div>
              <div className="flex items-center gap-2">
                {(resume.ats_score_estimate ?? resume.ats_score) && (
                  <Badge variant={(resume.ats_score_estimate ?? resume.ats_score)! > 75 ? 'default' : 'secondary'}>
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
                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-sm whitespace-pre-wrap">{resume.tailored_summary}</p>
                </div>
              </TabsContent>
              <TabsContent value="roles" className="mt-4">
                <div className="space-y-4">
                  {resume.selected_roles?.map((role, idx) => (
                    <div key={idx} className="border-l-2 border-primary pl-4">
                      <p className="font-medium">{role.job_title}</p>
                      <p className="text-sm text-muted-foreground">{role.employer_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {role.start_date} - {role.end_date || 'Present'}
                      </p>
                      <ul className="mt-2 space-y-1">
                        {role.selected_bullets?.map((bullet) => (
                          <li key={bullet.bullet_id} className="text-sm flex gap-2">
                            <span className="text-muted-foreground">•</span>
                            <span>{bullet.text}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </TabsContent>
              <TabsContent value="skills" className="mt-4">
                <div className="flex flex-wrap gap-2">
                  {resume.selected_skills?.map((skill, idx) => (
                    <Badge key={idx} variant="secondary">{skill.skill}</Badge>
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
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold">Cover Letter</h3>
              </div>
              <Badge variant={coverLetter.quality_score > 75 ? 'default' : 'secondary'}>
                Quality: {Math.round(coverLetter.quality_score)}/100
              </Badge>
            </div>

            <DownloadButtons
              type="cover-letter"
              jobProfileId={jobProfileId}
              jsonData={coverLetter}
              companyName={companyName}
            />

            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {coverLetter.draft_cover_letter}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
