'use client'

import { FileText, Target, PenLine, BarChart3, ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FeatureCard } from './FeatureCard'
import { cn } from '@/lib/utils'

interface HeroSectionProps {
  onGetStarted?: () => void
  className?: string
}

const features = [
  {
    icon: FileText,
    title: 'AI-Powered Resume Tailoring',
    description: 'Optimize your resume for each position with Claude AI. Automatically match your experience to job requirements.',
    highlight: true,
  },
  {
    icon: Target,
    title: 'ATS Score Prediction',
    description: 'See your compatibility score before applying. Understand how well your resume matches the job description.',
  },
  {
    icon: PenLine,
    title: 'Cover Letter Generation',
    description: 'Professional, personalized cover letters in seconds. Tailored to highlight your relevant experience.',
  },
  {
    icon: BarChart3,
    title: 'Skill Gap Analysis',
    description: 'Identify which skills to highlight or develop. Visual breakdown of matched vs missing requirements.',
  },
]

export function HeroSection({ onGetStarted, className }: HeroSectionProps) {
  return (
    <section
      className={cn(
        'relative min-h-[calc(100vh-73px)] overflow-hidden',
        'bg-gradient-to-b from-background via-background to-muted/30',
        className
      )}
    >
      {/* Background pattern */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-teal-100/20 via-transparent to-transparent dark:from-teal-900/10" />
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2364748b' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Hero content */}
        <div className="pt-16 pb-12 text-center sm:pt-24 lg:pt-32">
          {/* Badge */}
          <Badge
            variant="outline"
            className="mb-6 border-teal-500/30 bg-teal-50/50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-300"
          >
            <Sparkles className="mr-1.5 h-3.5 w-3.5" />
            AI-Powered Career Tools
          </Badge>

          {/* Headline */}
          <h1 className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Enterprise-Grade{' '}
            <span className="bg-gradient-to-r from-teal-600 to-cyan-600 bg-clip-text text-transparent">
              Talent Positioning
            </span>{' '}
            System
          </h1>

          {/* Subheadline */}
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl">
            AI-powered resume and cover letter optimization for consulting & enterprise roles.
            Stand out in competitive job markets with tailored, ATS-optimized applications.
          </p>

          {/* CTA Buttons */}
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button
              size="lg"
              onClick={onGetStarted}
              className="group relative overflow-hidden bg-teal-600 hover:bg-teal-700 text-white shadow-lg shadow-teal-600/25 transition-all hover:shadow-xl hover:shadow-teal-600/30"
            >
              <span className="relative z-10 flex items-center">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </span>
              <div className="absolute inset-0 -z-0 bg-gradient-to-r from-teal-500 to-cyan-500 opacity-0 transition-opacity group-hover:opacity-100" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={onGetStarted}
              className="border-2"
            >
              See How It Works
            </Button>
          </div>

          {/* Trust indicators */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-success" />
              <span>711+ Passing Tests</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-teal-500" />
              <span>Built with Claude AI</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-amber-500" />
              <span>Open Source</span>
            </div>
          </div>
        </div>

        {/* Feature cards */}
        <div className="pb-16 lg:pb-24">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <FeatureCard
                key={feature.title}
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
                highlight={feature.highlight}
                className="animate-fade-in"
                style={{ animationDelay: `${index * 100}ms` } as React.CSSProperties}
              />
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2">
          <button
            onClick={onGetStarted}
            className="flex flex-col items-center gap-2 text-muted-foreground/60 transition-colors hover:text-muted-foreground"
            aria-label="Scroll to get started"
          >
            <span className="text-xs uppercase tracking-wider">Paste a Job Description</span>
            <div className="h-8 w-5 rounded-full border-2 border-current p-1">
              <div className="h-2 w-1 animate-bounce rounded-full bg-current" />
            </div>
          </button>
        </div>
      </div>
    </section>
  )
}
