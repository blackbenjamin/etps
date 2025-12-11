'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertCircle, Loader2, Star, Plus, RefreshCw, Maximize2, Minimize2, Target } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { CircularProgress } from '@/components/ui/circular-progress'
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
      return <Badge className="text-xs bg-warning text-warning-foreground">Important</Badge>
    case 'nice-to-have':
      return <Badge variant="secondary" className="text-xs">Nice-to-have</Badge>
    default:
      return <Badge variant="outline" className="text-xs">{importance}</Badge>
  }
}

function getMatchColor(percentage: number) {
  if (percentage >= 70) return 'text-success'
  if (percentage >= 40) return 'text-warning'
  return 'text-danger'
}

function ComponentSkillRow({ skill, clusterName, onKeySkillToggle, isKeySkill, onAddSkill }: {
  skill: ComponentSkill
  clusterName: string
  onKeySkillToggle?: (clusterName: string, skillName: string, selected: boolean) => void
  isKeySkill: boolean
  onAddSkill?: (skillName: string) => void
}) {
  return (
    <div className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-muted/50 transition-colors">
      <div className="flex items-center gap-2 flex-1">
        {skill.matched ? (
          <CheckCircle2 className="h-4 w-4 text-success flex-shrink-0" />
        ) : skill.required ? (
          <XCircle className="h-4 w-4 text-danger flex-shrink-0" />
        ) : (
          <AlertCircle className="h-4 w-4 text-warning flex-shrink-0" />
        )}
        <span className={`text-sm ${skill.matched ? 'font-medium' : 'text-muted-foreground'}`}>
          {skill.name}
        </span>
        {skill.required && !skill.matched && (
          <Badge variant="outline" className="text-xs text-danger border-danger/30">Required</Badge>
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
            className="h-7 text-xs border-teal-200 hover:bg-teal-50 dark:border-teal-800 dark:hover:bg-teal-950/50"
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
            <Star className={`h-3 w-3 ${isKeySkill ? 'text-warning fill-warning' : 'text-muted-foreground'}`} />
          </div>
        )}
      </div>
    </div>
  )
}

function ClusterCard({ cluster, onKeySkillToggle, selectedKeySkills, onAddSkill, isExpanded, onToggle }: {
  cluster: CapabilityCluster
  onKeySkillToggle?: (clusterName: string, skillName: string, selected: boolean) => void
  selectedKeySkills?: Set<string>
  onAddSkill?: (skillName: string) => void
  isExpanded: boolean
  onToggle: () => void
}) {
  const matchedCount = cluster.component_skills.filter(s => s.matched).length
  const totalCount = cluster.component_skills.length

  return (
    <div className="border rounded-lg overflow-hidden transition-shadow hover:shadow-md">
      <Collapsible open={isExpanded} onOpenChange={onToggle}>
        {/* Cluster Header */}
        <CollapsibleTrigger asChild>
          <button className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
            <div className="flex items-center gap-3">
              {isExpanded ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground transition-transform" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground transition-transform" />
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
              {/* Summary info (always visible) */}
              <div className="text-right hidden sm:block">
                <div className="text-xs text-muted-foreground">
                  {matchedCount}/{totalCount} skills
                </div>
              </div>
              {/* Circular Progress */}
              <CircularProgress
                value={cluster.match_percentage}
                size="md"
                strokeWidth={4}
                showValue
                colorScheme="auto"
              />
            </div>
          </button>
        </CollapsibleTrigger>

        {/* Expanded Content */}
        <CollapsibleContent>
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
                    <Badge key={idx} variant="outline" className="text-xs text-danger border-danger/30 bg-danger/5">
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
                <p className="text-sm text-muted-foreground leading-relaxed border-l-2 border-teal-500 pl-3">
                  {cluster.positioning}
                </p>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
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

  // Track expanded clusters
  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(new Set())

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

  const toggleCluster = (clusterName: string) => {
    setExpandedClusters(prev => {
      const next = new Set(prev)
      if (next.has(clusterName)) {
        next.delete(clusterName)
      } else {
        next.add(clusterName)
      }
      return next
    })
  }

  const expandAll = () => {
    if (analysis?.clusters) {
      setExpandedClusters(new Set(analysis.clusters.map(c => c.name)))
    }
  }

  const collapseAll = () => {
    setExpandedClusters(new Set())
  }

  const allExpanded = analysis?.clusters && expandedClusters.size === analysis.clusters.length

  if (isLoading) {
    return (
      <Card className="border-l-4 border-l-teal-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-teal-600" />
            Analyzing Capabilities...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-teal-500 animate-pulse w-2/3" />
          </div>
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
        return 'bg-success/10 text-success border-success/30'
      case 'moderate_match':
        return 'bg-warning/10 text-warning border-warning/30'
      case 'stretch_role':
        return 'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-900/20 dark:text-orange-300'
      default:
        return 'bg-danger/10 text-danger border-danger/30'
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
      <Card className="overflow-hidden border-l-4 border-l-teal-500">
        <CardHeader className="pb-3 bg-gradient-to-r from-muted/50 to-transparent">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-teal-100 dark:bg-teal-900/30">
                <Target className="h-4 w-4 text-teal-600 dark:text-teal-400" />
              </div>
              <div>
                <CardTitle className="text-lg">Capability Cluster Analysis</CardTitle>
                <CardDescription>
                  Strategic capability matching for this role
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Expand/Collapse All button */}
              <Button
                size="sm"
                variant="outline"
                onClick={allExpanded ? collapseAll : expandAll}
                className="text-xs"
              >
                {allExpanded ? (
                  <>
                    <Minimize2 className="h-3.5 w-3.5 mr-1" />
                    Collapse All
                  </>
                ) : (
                  <>
                    <Maximize2 className="h-3.5 w-3.5 mr-1" />
                    Expand All
                  </>
                )}
              </Button>
              {/* Overall Score */}
              <div className="text-right">
                <Badge className={getRecommendationStyle(analysis.recommendation)}>
                  {Math.round(analysis.overall_match_score)}% Overall
                </Badge>
                <p className="text-xs text-muted-foreground mt-1">
                  {getRecommendationLabel(analysis.recommendation)}
                </p>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4 pt-4">
          {/* Key Strengths */}
          {analysis.key_strengths && analysis.key_strengths.length > 0 && (
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs font-semibold text-muted-foreground">Strengths:</span>
              {analysis.key_strengths.map((strength, idx) => (
                <Badge key={idx} className="bg-success/10 text-success border-success/30 text-xs">
                  {strength}
                </Badge>
              ))}
            </div>
          )}

          {/* Critical Gaps */}
          {analysis.critical_gaps && analysis.critical_gaps.length > 0 && (
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs font-semibold text-muted-foreground">Critical Gaps:</span>
              {analysis.critical_gaps.map((gap, idx) => (
                <Badge key={idx} variant="outline" className="text-xs text-danger border-danger/30 bg-danger/5">
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
                isExpanded={expandedClusters.has(cluster.name)}
                onToggle={() => toggleCluster(cluster.name)}
              />
            ))}
          </div>

          {/* Positioning Summary */}
          {analysis.positioning_summary && (
            <div className="pt-4 border-t">
              <h4 className="text-sm font-semibold mb-2">Positioning Summary</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
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
                  className="shadow-lg bg-teal-600 hover:bg-teal-700"
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
