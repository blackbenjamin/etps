'use client'

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, X, Plus } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

export interface SkillRowData {
  skill: string
  match_pct: number
  included: boolean
  order: number
  isKey: boolean
}

interface SkillRowProps {
  data: SkillRowData
  onToggleKey: (skill: string) => void
  onRemove: (skill: string) => void
  onAddSkill?: (skill: string) => void
  isDragging?: boolean
}

export function SkillRow({ data, onToggleKey, onRemove, onAddSkill, isDragging }: SkillRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: data.skill })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  // Color coding for match percentage
  const getMatchColor = (pct: number) => {
    if (pct >= 70) return 'bg-green-500'
    if (pct >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getMatchTextColor = (pct: number) => {
    if (pct >= 70) return 'text-green-700 dark:text-green-400'
    if (pct >= 40) return 'text-yellow-700 dark:text-yellow-400'
    return 'text-red-700 dark:text-red-400'
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'flex items-center gap-3 p-3 bg-card border rounded-lg',
        isDragging && 'opacity-50',
        !data.included && 'opacity-40'
      )}
    >
      {/* Drag Handle */}
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing touch-none p-1 hover:bg-accent rounded"
      >
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </button>

      {/* Key Checkbox */}
      <Checkbox
        checked={data.isKey}
        onCheckedChange={() => onToggleKey(data.skill)}
        disabled={!data.included}
        aria-label="Mark as key skill"
      />

      {/* Skill Name */}
      <div className="flex-1 min-w-0">
        <p className={cn("font-medium truncate", data.isKey && "text-primary")}>{data.skill}</p>
      </div>

      {/* Match Percentage Bar */}
      <div className="flex items-center gap-2 w-32">
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full", getMatchColor(data.match_pct))}
            style={{ width: `${data.match_pct}%` }}
          />
        </div>
        <span className={cn('text-xs font-medium w-10 text-right', getMatchTextColor(data.match_pct))}>
          {Math.round(data.match_pct)}%
        </span>
      </div>

      {/* "I have this" Button - for low match skills */}
      {data.match_pct < 40 && onAddSkill && (
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs"
          onClick={(e) => {
            e.stopPropagation()
            onAddSkill(data.skill)
          }}
        >
          <Plus className="h-3 w-3 mr-1" />
          I have this
        </Button>
      )}

      {/* Remove Button */}
      <Button
        size="sm"
        variant="ghost"
        className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
        onClick={() => onRemove(data.skill)}
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  )
}
