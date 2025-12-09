'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Alert, AlertDescription } from '@/components/ui/alert'
import type { ExperienceWithDetails, EvidenceMapping } from '@/types'

interface SkillEvidenceModalProps {
  isOpen: boolean
  onClose: () => void
  skillName: string
  experiences: ExperienceWithDetails[]
  onConfirm: (evidenceMappings: EvidenceMapping[]) => Promise<void>
  isLoading?: boolean
  loadError?: string | null
}

interface ExperienceSelection {
  experience_id: number
  engagement_ids: Set<number>
  bullet_ids: Set<number>
}

export function SkillEvidenceModal({
  isOpen,
  onClose,
  skillName,
  experiences,
  onConfirm,
  isLoading = false,
  loadError = null,
}: SkillEvidenceModalProps) {
  const [selections, setSelections] = useState<Map<number, ExperienceSelection>>(new Map())
  const [expandedExperiences, setExpandedExperiences] = useState<Set<number>>(new Set())
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset state when modal opens or skill changes
  useEffect(() => {
    if (isOpen) {
      setSelections(new Map())
      setExpandedExperiences(new Set())
      setError(null)
    }
  }, [isOpen, skillName])

  const toggleExperience = (expId: number) => {
    setExpandedExperiences(prev => {
      const next = new Set(prev)
      if (next.has(expId)) {
        next.delete(expId)
      } else {
        next.add(expId)
      }
      return next
    })
  }

  const toggleExperienceSelection = (expId: number) => {
    setSelections(prev => {
      const next = new Map(prev)
      if (next.has(expId)) {
        next.delete(expId)
      } else {
        next.set(expId, {
          experience_id: expId,
          engagement_ids: new Set(),
          bullet_ids: new Set(),
        })
      }
      return next
    })
  }

  const toggleEngagement = (expId: number, engagementId: number) => {
    setSelections(prev => {
      const next = new Map(prev)
      const existing = next.get(expId)

      // Create new Set objects to ensure React detects the change
      const newEngagementIds = new Set(existing?.engagement_ids || [])
      const newBulletIds = new Set(existing?.bullet_ids || [])

      if (newEngagementIds.has(engagementId)) {
        newEngagementIds.delete(engagementId)
      } else {
        newEngagementIds.add(engagementId)
      }

      // Create a new selection object with new Sets
      const newSelection: ExperienceSelection = {
        experience_id: expId,
        engagement_ids: newEngagementIds,
        bullet_ids: newBulletIds,
      }

      // Ensure experience is selected if engagement is selected
      if (newEngagementIds.size > 0 || newBulletIds.size > 0) {
        next.set(expId, newSelection)
      } else {
        next.delete(expId)
      }

      return next
    })
  }

  const toggleBullet = (expId: number, bulletId: number) => {
    setSelections(prev => {
      const next = new Map(prev)
      const existing = next.get(expId)

      // Create new Set objects to ensure React detects the change
      const newBulletIds = new Set(existing?.bullet_ids || [])
      const newEngagementIds = new Set(existing?.engagement_ids || [])

      if (newBulletIds.has(bulletId)) {
        newBulletIds.delete(bulletId)
      } else {
        newBulletIds.add(bulletId)
      }

      // Create a new selection object with new Sets
      const newSelection: ExperienceSelection = {
        experience_id: expId,
        engagement_ids: newEngagementIds,
        bullet_ids: newBulletIds,
      }

      // Ensure experience is selected if bullet is selected
      if (newBulletIds.size > 0 || newEngagementIds.size > 0) {
        next.set(expId, newSelection)
      } else {
        next.delete(expId)
      }

      return next
    })
  }

  const handleConfirm = async () => {
    if (selections.size === 0) {
      setError('Please select at least one experience, engagement, or bullet to demonstrate this skill.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const evidenceMappings: EvidenceMapping[] = Array.from(selections.values()).map(selection => ({
        experience_id: selection.experience_id,
        engagement_id: selection.engagement_ids.size > 0 ? Array.from(selection.engagement_ids)[0] : undefined,
        bullet_ids: selection.bullet_ids.size > 0 ? Array.from(selection.bullet_ids) : undefined,
      }))

      await onConfirm(evidenceMappings)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add skill. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const isExperienceSelected = (expId: number) => selections.has(expId)
  const isEngagementSelected = (expId: number, engagementId: number) =>
    selections.get(expId)?.engagement_ids.has(engagementId) ?? false
  const isBulletSelected = (expId: number, bulletId: number) =>
    selections.get(expId)?.bullet_ids.has(bulletId) ?? false

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Where did you use {skillName}?</DialogTitle>
          <DialogDescription>
            Select the experiences, engagements, or specific accomplishments that demonstrate this skill.
          </DialogDescription>
        </DialogHeader>

        {(error || loadError) && (
          <Alert variant="destructive">
            <AlertDescription>{error || loadError}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">Loading experiences...</span>
            </div>
          ) : experiences.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No experiences found. Please add experiences to your profile first.
            </div>
          ) : (
            experiences.map((exp) => {
              const isExpanded = expandedExperiences.has(exp.id)
              const isSelected = isExperienceSelected(exp.id)
              const isConsulting = exp.employer_type === 'independent_consulting'
              const hasExpandableContent = exp.bullets.length > 0 || exp.engagements.length > 0

              return (
                <div key={exp.id} className="border rounded-lg overflow-hidden">
                  {/* Experience Header */}
                  <div className="flex items-start gap-3 p-3 hover:bg-muted/50">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleExperienceSelection(exp.id)}
                      className="mt-1"
                    />
                    <div className="flex-1 min-w-0">
                      <button
                        onClick={() => toggleExperience(exp.id)}
                        className="w-full text-left flex items-start gap-2"
                      >
                        {hasExpandableContent && (
                          isExpanded ? (
                            <ChevronDown className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                          )
                        )}
                        <div className="flex-1">
                          <div className="font-medium">{exp.job_title}</div>
                          <div className="text-sm text-muted-foreground">
                            {exp.employer_name}
                            {exp.location && ` • ${exp.location}`}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {exp.start_date} - {exp.end_date || 'Present'}
                          </div>
                        </div>
                      </button>
                    </div>
                  </div>

                  {/* Expanded Content: Engagements and/or Direct Bullets */}
                  {isExpanded && (
                    <div className="border-t bg-muted/20 px-3 py-2 space-y-2">
                      {exp.engagements.length > 0 ? (
                        // Show engagements if the role has them
                        exp.engagements.map((engagement) => (
                          <div key={engagement.id} className="ml-6 border-l-2 border-muted pl-3 space-y-1">
                            <div className="flex items-start gap-2">
                              <Checkbox
                                checked={isEngagementSelected(exp.id, engagement.id)}
                                onCheckedChange={() => toggleEngagement(exp.id, engagement.id)}
                                className="mt-0.5"
                              />
                              <div>
                                <div className="text-sm font-medium">
                                  {engagement.project_name || 'Unnamed Project'}
                                  {engagement.client && (
                                    <span className="text-muted-foreground"> • {engagement.client}</span>
                                  )}
                                </div>
                                {engagement.date_range_label && (
                                  <div className="text-xs text-muted-foreground">
                                    {engagement.date_range_label}
                                  </div>
                                )}
                                {engagement.bullets.length > 0 && (
                                  <div className="mt-1 space-y-1">
                                    {engagement.bullets.map((bullet) => (
                                      <div key={bullet.id} className="flex items-start gap-2 ml-4">
                                        <Checkbox
                                          checked={isBulletSelected(exp.id, bullet.id)}
                                          onCheckedChange={() => toggleBullet(exp.id, bullet.id)}
                                          className="mt-0.5"
                                        />
                                        <div className="text-xs text-muted-foreground line-clamp-2">
                                          {bullet.text}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        // Show direct bullets for non-consulting roles
                        exp.bullets.length > 0 && (
                          <div className="ml-6 space-y-1">
                            {exp.bullets.map((bullet) => (
                              <div key={bullet.id} className="flex items-start gap-2">
                                <Checkbox
                                  checked={isBulletSelected(exp.id, bullet.id)}
                                  onCheckedChange={() => toggleBullet(exp.id, bullet.id)}
                                  className="mt-0.5"
                                />
                                <div className="text-xs text-muted-foreground line-clamp-2">
                                  {bullet.text}
                                </div>
                              </div>
                            ))}
                          </div>
                        )
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isSubmitting || selections.size === 0}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Adding...
              </>
            ) : (
              `Confirm (${selections.size} selected)`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
