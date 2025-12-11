'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { ProgressBar } from '@/components/ui/progress-bar'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'

export type SkillGroupType = 'matched' | 'partial' | 'missing'

interface SkillGroupProps {
  type: SkillGroupType
  count: number
  total: number
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

const groupConfig: Record<SkillGroupType, {
  label: string
  icon: React.ComponentType<{ className?: string }>
  bgColor: string
  borderColor: string
  iconColor: string
  badgeVariant: 'success' | 'warning' | 'destructive'
}> = {
  matched: {
    label: 'Matched Skills',
    icon: CheckCircle2,
    bgColor: 'bg-success/5',
    borderColor: 'border-success/20',
    iconColor: 'text-success',
    badgeVariant: 'success',
  },
  partial: {
    label: 'Partial Matches',
    icon: AlertTriangle,
    bgColor: 'bg-warning/5',
    borderColor: 'border-warning/20',
    iconColor: 'text-warning',
    badgeVariant: 'warning',
  },
  missing: {
    label: 'Missing Skills',
    icon: XCircle,
    bgColor: 'bg-destructive/5',
    borderColor: 'border-destructive/20',
    iconColor: 'text-destructive',
    badgeVariant: 'destructive',
  },
}

export function SkillGroup({
  type,
  count,
  total,
  isExpanded,
  onToggle,
  children,
}: SkillGroupProps) {
  const config = groupConfig[type]
  const Icon = config.icon
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0

  return (
    <Collapsible open={isExpanded} onOpenChange={onToggle}>
      <div className={cn('rounded-lg border', config.bgColor, config.borderColor)}>
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="w-full flex items-center gap-3 p-4 hover:bg-muted/30 transition-colors rounded-t-lg"
          >
            {/* Expand/Collapse Icon */}
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            )}

            {/* Group Icon */}
            <div className={cn('p-1.5 rounded-lg', config.bgColor)}>
              <Icon className={cn('h-4 w-4', config.iconColor)} />
            </div>

            {/* Label and Count */}
            <div className="flex-1 flex items-center gap-2 min-w-0">
              <span className="font-medium text-sm">{config.label}</span>
              <Badge
                variant="outline"
                className={cn(
                  'text-xs',
                  type === 'matched' && 'border-success/30 text-success',
                  type === 'partial' && 'border-warning/30 text-warning',
                  type === 'missing' && 'border-destructive/30 text-destructive'
                )}
              >
                {count}
              </Badge>
            </div>

            {/* Progress Bar */}
            <div className="w-24 flex-shrink-0">
              <ProgressBar
                value={percentage}
                size="sm"
                colorScheme={type === 'matched' ? 'success' : type === 'partial' ? 'warning' : 'danger'}
              />
            </div>

            {/* Percentage */}
            <span className={cn(
              'text-xs font-medium w-10 text-right flex-shrink-0',
              config.iconColor
            )}>
              {percentage}%
            </span>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4">
            {children}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}
