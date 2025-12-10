'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertCircle, Loader2, Star, Plus, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { SkillEvidenceModal } from './SkillEvidenceModal'
import { api } from '@/lib/api'
import type {
  CapabilityClusterAnalysis,
  CapabilityCluster,
  ComponentSkill,
  ExperienceWithDetails,
  EvidenceMapping,
  AddUserSkillRequest
} from '@/types'

interface CapabilityClusterPanelProps {
  analysis: CapabilityClusterAnalysis | null
  isLoading?: boolean
  onKeySkillToggle?: (clusterName: string, skillName: string, selected: boolean) => void
  selectedKeySkills?: Set<string>
  jobProfileId?: number
  onRerunAnalysis?: () => Promise<void>
}

function getImportanceBadge(importance: string) {
  switch (importance) {
    case 'critical':
      return <Badge variant="destructive" className="text-xs">Critical</Badge>
    case 'important':
      return <Badge variant="default" className="text-xs bg-yellow-600">Important</Badge>
    case 'nice-to-have':
      return <Badge variant="secondary" className="text-xs">Nice-to-have</Badge>
    default:
      return <Badge variant="outline" className="text-xs">{importance}</Badge>
  }
}

function getMatchColor(percentage: number) {
  if (percentage >= 70) return 'text-green-600'
  if (percentage >= 40) return 'text-yellow-600'
  return 'text-red-600'
}

function getProgressColor(percentage: number) {
  if (percentage >= 70) return 'bg-green-600'
  if (percentage >= 40) return 'bg-yellow-600'
  return 'bg-red-600'
}

function ComponentSkillRow({ skill, clusterName, onKeySkillToggle, isKeySkill, onAddSkill }: {
  skill: ComponentSkill
  clusterName: string
  onKeySkillToggle?: (clusterName: string, skillName: string, selected: boolean) => void
  isKeySkill: boolean
  onAddSkill?: (skillName: string) => void
}) {
  const skillKey = `${clusterName}::${skill.name}`

  return (
    <div className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-muted/50">
      <div className="flex items-center gap-2 flex-1">
        {skill.matched ? (
          <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
        ) : skill.required ? (
          <XCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
        ) : (
          <AlertCircle className="h-4 w-4 text-yellow-600 flex-shrink-0" />
        )}
        <span className={`text-sm ${skill.matched ? 'font-medium' : 'text-muted-foreground'}`}>
          {skill.name}
        </span>
        {skill.required && !skill.matched && (
          <Badge variant="outline" className="text-xs text-red-600 border-red-200">Required</Badge>
        )}
      </div>
      <div className="flex items-center gap-2">
        {skill.match_strength > 0 && (
          <span className={`text-xs ${getMatchColor(skill.match_strength * 100)}`}>
            {Math.round(skill.match_strength * 100)}%
          </span>
        )}
        {!skill.matched && onAddSkill && (
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs"
            onClick={() => onAddSkill(skill.name)}
          >
            <Plus className="h-3 w-3 mr-1" />
            I have this
          </Button>
        )}
        {onKeySkillToggle && skill.matched && (
          <div
            className="flex items-center gap-1 cursor-pointer"
            onClick={() => onKeySkillToggle(clusterName, skill.name, !isKeySkill)}
          >
            <Checkbox
              checked={isKeySkill}
              className="h-4 w-4"
            />
            <Star className={`h-3 w-3 ${isKeySkill ? 'text-yellow-500 fill-yellow-500' : 'text-muted-foreground'}`} />
          </div>
        )}
      </div>
    </div>
  )
}

function ClusterCard({ cluster, onKeySkillToggle, selectedKeySkills, onAddSkill }: {
  cluster: CapabilityCluster
  onKeySkillToggle?: (clusterName: string, skillName: string, selected: boolean) => void
  selectedKeySkills?: Set<string>
  onAddSkill?: (skillName: string) => void
}) {
  const [isExpanded, setIsExpanded] = useState(cluster.is_expanded ?? false)

  const matchedCount = cluster.component_skills.filter(s => s.matched).length
  const totalCount = cluster.component_skills.length

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Cluster Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          )}
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="font-semibold">{cluster.name}</span>
              {getImportanceBadge(cluster.importance)}
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
              {cluster.description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className={`text-lg font-bold ${getMatchColor(cluster.match_percentage)}`}>
              {Math.round(cluster.match_percentage)}%
            </div>
            <div className="text-xs text-muted-foreground">
              {matchedCount}/{totalCount} skills
            </div>
          </div>
          <div className="w-24">
            <Progress
              value={cluster.match_percentage}
              className="h-2"
            />
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t bg-muted/20 p-4 space-y-3">
          {/* Component Skills */}
          <div className="space-y-1">
            <h5 className="text-xs font-semibold uppercase text-muted-foreground mb-2">
              Component Skills
            </h5>
            {cluster.component_skills.map((skill, idx) => {
              const skillKey = `${cluster.name}::${skill.name}`
              return (
                <ComponentSkillRow
                  key={idx}
                  skill={skill}
                  clusterName={cluster.name}
                  onKeySkillToggle={onKeySkillToggle}
                  isKeySkill={selectedKeySkills?.has(skillKey) ?? false}
                  onAddSkill={onAddSkill}
                />
              )
            })}
          </div>

          {/* Gaps */}
          {cluster.gaps && cluster.gaps.length > 0 && (
            <div className="pt-2 border-t">
              <h5 className="text-xs font-semibold uppercase text-muted-foreground mb-2">
                Gaps to Address
              </h5>
              <div className="flex flex-wrap gap-1">
                {cluster.gaps.map((gap, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs text-red-600 border-red-200">
                    {gap}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Positioning Strategy */}
          {cluster.positioning && (
            <div className="pt-2 border-t">
              <h5 className="text-xs font-semibold uppercase text-muted-foreground mb-1">
                Positioning Strategy
              </h5>
              <p className="text-sm text-muted-foreground">
                {cluster.positioning}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function CapabilityClusterPanel({
  analysis,
  isLoading,
  onKeySkillToggle,
  selectedKeySkills,
  jobProfileId,
  onRerunAnalysis
}: CapabilityClusterPanelProps) {
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [experiences, setExperiences] = useState<ExperienceWithDetails[]>([])
  const [isLoadingExperiences, setIsLoadingExperiences] = useState(false)
  const [experienceLoadError, setExperienceLoadError] = useState<string | null>(null)
  const [skillsAddedCount, setSkillsAddedCount] = useState(0)
  const [isRerunning, setIsRerunning] = useState(false)

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

  const handleAddSkill = (skillName: string) => {
    setSelectedSkill(skillName)
    setIsModalOpen(true)
  }

  const handleConfirmSkill = async (evidenceMappings: EvidenceMapping[]) => {
    if (!jobProfileId || !selectedSkill) return

    const request: AddUserSkillRequest = {
      skill_name: selectedSkill,
      user_id: 1,
      evidence_mappings: evidenceMappings
    }

    await api.addUserSkill(jobProfileId, request)
    setSkillsAddedCount(prev => prev + 1)
  }

  const handleRerunAnalysis = async () => {
    if (!onRerunAnalysis) return

    setIsRerunning(true)
    try {
      await onRerunAnalysis()
      setSkillsAddedCount(0) // Reset counter after successful re-run
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
            Analyzing Capabilities...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Progress value={undefined} className="w-full" />
        </CardContent>
      </Card>
    )
  }

  if (!analysis || !analysis.clusters || analysis.clusters.length === 0) {
    return null
  }

  const getRecommendationStyle = (rec: string) => {
    switch (rec) {
      case 'strong_match':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'moderate_match':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'stretch_role':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
      default:
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    }
  }

  const getRecommendationLabel = (rec: string) => {
    switch (rec) {
      case 'strong_match': return 'Strong Match'
      case 'moderate_match': return 'Moderate Match'
      case 'stretch_role': return 'Stretch Role'
      default: return 'Weak Match'
    }
  }

  // Sort clusters by importance then match percentage
  const sortedClusters = [...analysis.clusters].sort((a, b) => {
    const importanceOrder: Record<string, number> = { critical: 0, important: 1, 'nice-to-have': 2 }
    const aOrder = importanceOrder[a.importance] ?? 1
    const bOrder = importanceOrder[b.importance] ?? 1
    if (aOrder !== bOrder) return aOrder - bOrder
    return b.match_percentage - a.match_percentage
  })

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Capability Cluster Analysis</CardTitle>
              <CardDescription>
                Strategic capability matching for this role
              </CardDescription>
            </div>
            <div className="text-right">
              <Badge className={getRecommendationStyle(analysis.recommendation)}>
                {Math.round(analysis.overall_match_score)}% Overall
              </Badge>
              <p className="text-xs text-muted-foreground mt-1">
                {getRecommendationLabel(analysis.recommendation)}
              </p>
            </div>
          </div>
        </CardHeader>

      <CardContent className="space-y-4">
        {/* Key Strengths */}
        {analysis.key_strengths && analysis.key_strengths.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <span className="text-xs font-semibold text-muted-foreground">Strengths:</span>
            {analysis.key_strengths.map((strength, idx) => (
              <Badge key={idx} variant="default" className="bg-green-600 text-xs">
                {strength}
              </Badge>
            ))}
          </div>
        )}

        {/* Critical Gaps */}
        {analysis.critical_gaps && analysis.critical_gaps.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <span className="text-xs font-semibold text-muted-foreground">Critical Gaps:</span>
            {analysis.critical_gaps.map((gap, idx) => (
              <Badge key={idx} variant="outline" className="text-xs text-red-600 border-red-200">
                {gap}
              </Badge>
            ))}
          </div>
        )}

        {/* Cluster List */}
        <div className="space-y-3">
          {sortedClusters.map((cluster, idx) => (
            <ClusterCard
              key={idx}
              cluster={cluster}
              onKeySkillToggle={onKeySkillToggle}
              selectedKeySkills={selectedKeySkills}
              onAddSkill={jobProfileId ? handleAddSkill : undefined}
            />
          ))}
        </div>

        {/* Positioning Summary */}
        {analysis.positioning_summary && (
          <div className="pt-4 border-t">
            <h4 className="text-sm font-semibold mb-2">Positioning Summary</h4>
            <p className="text-sm text-muted-foreground">
              {analysis.positioning_summary}
            </p>
          </div>
        )}

        {/* Floating Update Analysis Button */}
        {skillsAddedCount > 0 && onRerunAnalysis && (
          <div className="sticky bottom-4 left-0 right-0 flex justify-center pointer-events-none mt-4">
            <div className="pointer-events-auto">
              <Button
                size="lg"
                onClick={handleRerunAnalysis}
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
