'use client'

import { useState, useEffect } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { AlertCircle, Loader2, Save, CheckCircle2, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { SkillRow, type SkillRowData } from './SkillRow'
import { SkillEvidenceModal } from '@/components/capability/SkillEvidenceModal'
import { updateSkillSelection, api } from '@/lib/api'
import type { SkillGapResponse, ExperienceWithDetails, EvidenceMapping, AddUserSkillRequest } from '@/types'

interface SkillSelectionPanelProps {
  jobProfileId: number
  analysis: SkillGapResponse | null
  isLoading?: boolean
  onSaved?: () => void
}

export function SkillSelectionPanel({ jobProfileId, analysis, isLoading, onSaved }: SkillSelectionPanelProps) {
  const [skills, setSkills] = useState<SkillRowData[]>([])
  const [keySkills, setKeySkills] = useState<Set<string>>(new Set())
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // State for "I have this" modal
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [experiences, setExperiences] = useState<ExperienceWithDetails[]>([])
  const [isLoadingExperiences, setIsLoadingExperiences] = useState(false)
  const [experienceLoadError, setExperienceLoadError] = useState<string | null>(null)
  const [skillsAddedCount, setSkillsAddedCount] = useState(0)
  const [isRerunning, setIsRerunning] = useState(false)

  // Initialize skills from analysis
  useEffect(() => {
    if (!analysis) return

    // Combine matched skills and extracted skills for a comprehensive list
    const skillMap = new Map<string, { match_pct: number; source: string }>()

    // Add matched skills with their actual match strength
    if (analysis.matched_skills) {
      for (const match of analysis.matched_skills) {
        skillMap.set(match.skill, {
          match_pct: (match.match_strength || 0) * 100,
          source: 'matched'
        })
      }
    }

    // Add weak signals (partial matches) with moderate score
    if (analysis.weak_signals) {
      for (const signal of analysis.weak_signals) {
        if (!skillMap.has(signal.skill)) {
          skillMap.set(signal.skill, {
            match_pct: 40, // Weak signals get 40%
            source: 'weak'
          })
        }
      }
    }

    // Add skill gaps (no match) with 0%
    if (analysis.skill_gaps) {
      for (const gap of analysis.skill_gaps) {
        if (!skillMap.has(gap.skill)) {
          skillMap.set(gap.skill, {
            match_pct: 0,
            source: 'gap'
          })
        }
      }
    }

    // Convert to array and sort by match_pct descending
    const initialSkills: SkillRowData[] = Array.from(skillMap.entries())
      .sort((a, b) => b[1].match_pct - a[1].match_pct)
      .map(([skill, data], index) => ({
        skill,
        match_pct: data.match_pct,
        included: true,
        order: index,
        isKey: false,
      }))

    setSkills(initialSkills)
    setKeySkills(new Set())
    setSaveSuccess(false)
  }, [analysis])

  // Load experiences when modal opens
  useEffect(() => {
    if (isModalOpen) {
      setIsLoadingExperiences(true)
      setExperienceLoadError(null)
      api.getUserExperiences()
        .then(setExperiences)
        .catch(err => {
          console.error('Failed to load experiences:', err)
          setExperienceLoadError(`Failed to load experiences: ${err instanceof Error ? err.message : 'Unknown error'}`)
          setExperiences([])
        })
        .finally(() => setIsLoadingExperiences(false))
    }
  }, [isModalOpen])

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      setSkills((items) => {
        const oldIndex = items.findIndex((item) => item.skill === active.id)
        const newIndex = items.findIndex((item) => item.skill === over.id)

        const reordered = arrayMove(items, oldIndex, newIndex)
        // Update order values
        return reordered.map((item, idx) => ({ ...item, order: idx }))
      })
      setSaveSuccess(false)
    }
  }

  const handleToggleKey = (skill: string) => {
    const currentIsKey = keySkills.has(skill)

    if (!currentIsKey && keySkills.size >= 4) {
      setSaveError('Maximum 4 key skills allowed')
      setTimeout(() => setSaveError(null), 3000)
      return
    }

    setKeySkills((prev) => {
      const updated = new Set(prev)
      if (updated.has(skill)) {
        updated.delete(skill)
      } else {
        updated.add(skill)
      }
      return updated
    })

    // Update isKey flag in skills array
    setSkills((prev) =>
      prev.map((s) =>
        s.skill === skill ? { ...s, isKey: !s.isKey } : s
      )
    )
    setSaveSuccess(false)
  }

  const handleRemove = (skill: string) => {
    setSkills((prev) =>
      prev.map((s) =>
        s.skill === skill ? { ...s, included: false } : s
      )
    )
    // Remove from key skills if it was marked as key
    setKeySkills((prev) => {
      const updated = new Set(prev)
      updated.delete(skill)
      return updated
    })
    // Update isKey in skills array
    setSkills((prev) =>
      prev.map((s) =>
        s.skill === skill ? { ...s, isKey: false, included: false } : s
      )
    )
    setSaveSuccess(false)
  }

  const handleSave = async () => {
    setIsSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    try {
      await updateSkillSelection(jobProfileId, {
        selected_skills: skills.map((s) => ({
          skill: s.skill,
          match_pct: s.match_pct,
          included: s.included,
          order: s.order,
        })),
        key_skills: Array.from(keySkills),
      })
      setSaveSuccess(true)
      onSaved?.()
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save skill selection')
    } finally {
      setIsSaving(false)
    }
  }

  // Handle "I have this" skill addition
  const handleAddSkill = (skillName: string) => {
    setSelectedSkill(skillName)
    setIsModalOpen(true)
  }

  const handleConfirmSkill = async (evidenceMappings: EvidenceMapping[]) => {
    if (!selectedSkill) return

    const request: AddUserSkillRequest = {
      skill_name: selectedSkill,
      user_id: 1,
      evidence_mappings: evidenceMappings
    }

    await api.addUserSkill(jobProfileId, request)
    setSkillsAddedCount(prev => prev + 1)

    // Update match percentage for the skill locally (boost to 70%)
    setSkills(prev =>
      prev.map(s =>
        s.skill === selectedSkill
          ? { ...s, match_pct: Math.max(s.match_pct, 70) }
          : s
      )
    )
    setSaveSuccess(false)
  }

  // Handle re-running skill gap analysis
  const handleUpdateAnalysis = async () => {
    setIsRerunning(true)
    try {
      await api.analyzeSkillGap({ job_profile_id: jobProfileId })
      setSkillsAddedCount(0)
      onSaved?.()
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to update analysis')
    } finally {
      setIsRerunning(false)
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading Skills...
          </CardTitle>
        </CardHeader>
      </Card>
    )
  }

  if (!analysis || skills.length === 0) {
    return null
  }

  const keySkillCount = keySkills.size
  const needsMoreKeySkills = keySkillCount < 3
  const includedSkills = skills.filter((s) => s.included)
  const removedSkills = skills.filter((s) => !s.included)

  return (
    <>
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Skills for This Application</CardTitle>
            <CardDescription>
              Drag to reorder by priority. Check 3-4 key skills for cover letter focus.
            </CardDescription>
          </div>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : saveSuccess ? (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4 text-green-500" />
                Saved
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Warning about key skills */}
        {needsMoreKeySkills && (
          <Alert variant="default">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {keySkillCount}/4 key skills selected. Select 3-4 skills to emphasize in your cover letter.
            </AlertDescription>
          </Alert>
        )}

        {/* Save success */}
        {saveSuccess && (
          <Alert className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800 dark:text-green-200">
              Skill selections saved! Generate your resume or cover letter to use these preferences.
            </AlertDescription>
          </Alert>
        )}

        {/* Save error */}
        {saveError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{saveError}</AlertDescription>
          </Alert>
        )}

        {/* Draggable skill list */}
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={includedSkills.map((s) => s.skill)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2">
              {includedSkills.map((skill) => (
                <SkillRow
                  key={skill.skill}
                  data={skill}
                  onToggleKey={handleToggleKey}
                  onRemove={handleRemove}
                  onAddSkill={handleAddSkill}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        {/* Removed skills (collapsed) */}
        {removedSkills.length > 0 && (
          <details className="text-sm text-muted-foreground">
            <summary className="cursor-pointer hover:text-foreground">
              {removedSkills.length} removed skill{removedSkills.length > 1 ? 's' : ''}
            </summary>
            <div className="mt-2 space-y-1 pl-4">
              {removedSkills.map((s) => (
                <div key={s.skill} className="opacity-50 flex items-center gap-2">
                  <span>-</span>
                  <span>{s.skill}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 px-2 text-xs"
                    onClick={() => {
                      setSkills((prev) =>
                        prev.map((skill) =>
                          skill.skill === s.skill ? { ...skill, included: true } : skill
                        )
                      )
                      setSaveSuccess(false)
                    }}
                  >
                    Restore
                  </Button>
                </div>
              ))}
            </div>
          </details>
        )}

        {/* Floating Update Analysis Button */}
        {skillsAddedCount > 0 && (
          <div className="sticky bottom-4 left-0 right-0 flex justify-center pointer-events-none mt-4">
            <div className="pointer-events-auto">
              <Button
                size="lg"
                onClick={handleUpdateAnalysis}
                disabled={isRerunning}
                className="shadow-lg"
              >
                {isRerunning ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Updating Analysis...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-5 w-5" />
                    Update Analysis ({skillsAddedCount} skill{skillsAddedCount > 1 ? 's' : ''} added)
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>

    {/* Skill Evidence Modal */}
    {selectedSkill && (
      <SkillEvidenceModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedSkill(null)
          setExperienceLoadError(null)
        }}
        skillName={selectedSkill}
        experiences={experiences}
        onConfirm={handleConfirmSkill}
        isLoading={isLoadingExperiences}
        loadError={experienceLoadError}
      />
    )}
  </>
  )
}
