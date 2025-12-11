'use client'

import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface FeatureCardProps {
  icon: LucideIcon
  title: string
  description: string
  highlight?: boolean
  className?: string
  style?: React.CSSProperties
}

export function FeatureCard({
  icon: Icon,
  title,
  description,
  highlight = false,
  className,
  style,
}: FeatureCardProps) {
  return (
    <div
      style={style}
      className={cn(
        'group relative rounded-xl border bg-card p-6 transition-all duration-300',
        'hover:shadow-lg hover:-translate-y-1',
        highlight
          ? 'border-teal-500/50 bg-gradient-to-br from-teal-50 to-white dark:from-teal-950/30 dark:to-card'
          : 'border-border hover:border-teal-500/30',
        className
      )}
    >
      {/* Icon */}
      <div
        className={cn(
          'mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg transition-colors',
          highlight
            ? 'bg-teal-600 text-white'
            : 'bg-teal-100 text-teal-600 group-hover:bg-teal-600 group-hover:text-white dark:bg-teal-900/50 dark:text-teal-400'
        )}
      >
        <Icon className="h-6 w-6" />
      </div>

      {/* Title */}
      <h3 className="mb-2 text-lg font-semibold text-foreground">
        {title}
      </h3>

      {/* Description */}
      <p className="text-sm text-muted-foreground leading-relaxed">
        {description}
      </p>

      {/* Hover gradient overlay */}
      <div
        className={cn(
          'absolute inset-0 rounded-xl opacity-0 transition-opacity duration-300',
          'bg-gradient-to-br from-teal-500/5 to-transparent',
          'group-hover:opacity-100'
        )}
      />
    </div>
  )
}
