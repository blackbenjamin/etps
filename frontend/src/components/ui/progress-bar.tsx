'use client'

import { cn } from '@/lib/utils'

interface ProgressBarProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  colorScheme?: 'default' | 'success' | 'warning' | 'danger' | 'auto'
  showValue?: boolean
  label?: string
  className?: string
  animate?: boolean
}

const sizeConfig = {
  sm: { height: 'h-1.5', textSize: 'text-xs' },
  md: { height: 'h-2', textSize: 'text-sm' },
  lg: { height: 'h-3', textSize: 'text-sm' },
}

function getColorForValue(value: number): string {
  if (value >= 75) return 'bg-success'
  if (value >= 50) return 'bg-warning'
  return 'bg-danger'
}

export function ProgressBar({
  value,
  max = 100,
  size = 'md',
  colorScheme = 'default',
  showValue = false,
  label,
  className,
  animate = true,
}: ProgressBarProps) {
  const { height, textSize } = sizeConfig[size]
  const normalizedValue = Math.min(Math.max(value, 0), max)
  const percentage = (normalizedValue / max) * 100

  // Determine bar color
  let barColor: string
  if (colorScheme === 'auto') {
    barColor = getColorForValue(percentage)
  } else if (colorScheme === 'success') {
    barColor = 'bg-success'
  } else if (colorScheme === 'warning') {
    barColor = 'bg-warning'
  } else if (colorScheme === 'danger') {
    barColor = 'bg-danger'
  } else {
    barColor = 'bg-primary'
  }

  return (
    <div className={cn('w-full', className)}>
      {/* Label row */}
      {(label || showValue) && (
        <div className={cn('flex justify-between items-center mb-1', textSize)}>
          {label && <span className="text-muted-foreground">{label}</span>}
          {showValue && (
            <span className="font-medium tabular-nums">{Math.round(percentage)}%</span>
          )}
        </div>
      )}

      {/* Progress bar */}
      <div
        className={cn(
          'w-full rounded-full bg-muted overflow-hidden',
          height
        )}
        role="progressbar"
        aria-valuenow={normalizedValue}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label || `${Math.round(percentage)}%`}
      >
        <div
          className={cn(
            'h-full rounded-full',
            barColor,
            animate && 'transition-all duration-500 ease-out'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Skill match progress bar with semantic coloring
interface SkillMatchBarProps {
  matchPercentage: number
  label?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function SkillMatchBar({
  matchPercentage,
  label,
  size = 'sm',
  className,
}: SkillMatchBarProps) {
  return (
    <ProgressBar
      value={matchPercentage}
      size={size}
      colorScheme="auto"
      showValue
      label={label}
      className={className}
    />
  )
}

// Multi-segment progress bar for showing multiple values
interface SegmentedProgressProps {
  segments: {
    value: number
    color: 'success' | 'warning' | 'danger' | 'muted'
    label?: string
  }[]
  total?: number
  size?: 'sm' | 'md' | 'lg'
  showLegend?: boolean
  className?: string
}

const segmentColors = {
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
  muted: 'bg-muted-foreground/30',
}

export function SegmentedProgress({
  segments,
  total,
  size = 'md',
  showLegend = false,
  className,
}: SegmentedProgressProps) {
  const { height } = sizeConfig[size]
  const calculatedTotal = total || segments.reduce((sum, seg) => sum + seg.value, 0)

  return (
    <div className={cn('w-full', className)}>
      {/* Progress bar with segments */}
      <div
        className={cn(
          'w-full rounded-full bg-muted overflow-hidden flex',
          height
        )}
        role="progressbar"
      >
        {segments.map((segment, index) => {
          const widthPercent = (segment.value / calculatedTotal) * 100
          return (
            <div
              key={index}
              className={cn(
                'h-full transition-all duration-500 ease-out',
                segmentColors[segment.color],
                index === 0 && 'rounded-l-full',
                index === segments.length - 1 && 'rounded-r-full'
              )}
              style={{ width: `${widthPercent}%` }}
              title={segment.label ? `${segment.label}: ${segment.value}` : undefined}
            />
          )
        })}
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="flex gap-4 mt-2 text-xs">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center gap-1">
              <div
                className={cn(
                  'w-2.5 h-2.5 rounded-full',
                  segmentColors[segment.color]
                )}
              />
              <span className="text-muted-foreground">
                {segment.label || `Segment ${index + 1}`}: {segment.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
