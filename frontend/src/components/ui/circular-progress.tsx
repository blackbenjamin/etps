'use client'

import { cn } from '@/lib/utils'

interface CircularProgressProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg' | 'xl'
  strokeWidth?: number
  showValue?: boolean
  showLabel?: boolean
  label?: string
  colorScheme?: 'default' | 'success' | 'warning' | 'danger' | 'auto'
  className?: string
}

const sizeConfig = {
  sm: { width: 48, textSize: 'text-xs', labelSize: 'text-[10px]' },
  md: { width: 64, textSize: 'text-sm', labelSize: 'text-xs' },
  lg: { width: 80, textSize: 'text-base', labelSize: 'text-xs' },
  xl: { width: 120, textSize: 'text-2xl', labelSize: 'text-sm' },
}

function getColorForValue(value: number): string {
  if (value >= 75) return 'stroke-success'
  if (value >= 50) return 'stroke-warning'
  return 'stroke-danger'
}

function getTextColorForValue(value: number): string {
  if (value >= 75) return 'text-success'
  if (value >= 50) return 'text-warning'
  return 'text-danger'
}

export function CircularProgress({
  value,
  max = 100,
  size = 'md',
  strokeWidth = 4,
  showValue = true,
  showLabel = false,
  label,
  colorScheme = 'auto',
  className,
}: CircularProgressProps) {
  const { width, textSize, labelSize } = sizeConfig[size]
  const radius = (width - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const normalizedValue = Math.min(Math.max(value, 0), max)
  const percentage = (normalizedValue / max) * 100
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  // Determine stroke color
  let strokeColor: string
  let textColor: string

  if (colorScheme === 'auto') {
    strokeColor = getColorForValue(percentage)
    textColor = getTextColorForValue(percentage)
  } else if (colorScheme === 'success') {
    strokeColor = 'stroke-success'
    textColor = 'text-success'
  } else if (colorScheme === 'warning') {
    strokeColor = 'stroke-warning'
    textColor = 'text-warning'
  } else if (colorScheme === 'danger') {
    strokeColor = 'stroke-danger'
    textColor = 'text-danger'
  } else {
    strokeColor = 'stroke-primary'
    textColor = 'text-primary'
  }

  return (
    <div
      className={cn('relative inline-flex items-center justify-center', className)}
      style={{ width, height: width }}
      role="progressbar"
      aria-valuenow={normalizedValue}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-label={label || `${Math.round(percentage)}%`}
    >
      <svg
        className="transform -rotate-90"
        width={width}
        height={width}
        viewBox={`0 0 ${width} ${width}`}
      >
        {/* Background circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          className="stroke-muted"
        />
        {/* Progress circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className={cn(strokeColor, 'transition-all duration-500 ease-out')}
          style={{
            strokeDasharray: circumference,
            strokeDashoffset,
          }}
        />
      </svg>

      {/* Center content */}
      {(showValue || showLabel) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showValue && (
            <span className={cn('font-semibold tabular-nums', textSize, textColor)}>
              {Math.round(percentage)}
            </span>
          )}
          {showLabel && label && (
            <span className={cn('text-muted-foreground', labelSize)}>
              {label}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// Convenience wrapper for ATS scores specifically
interface ATSScoreCircleProps {
  score: number
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showLabel?: boolean
  className?: string
}

export function ATSScoreCircle({
  score,
  size = 'lg',
  showLabel = true,
  className,
}: ATSScoreCircleProps) {
  return (
    <CircularProgress
      value={score}
      size={size}
      showValue
      showLabel={showLabel}
      label="ATS Score"
      colorScheme="auto"
      strokeWidth={size === 'xl' ? 8 : size === 'lg' ? 6 : 4}
      className={className}
    />
  )
}
