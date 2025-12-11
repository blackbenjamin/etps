'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Lightbulb, HelpCircle, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface ContextNotesFieldProps {
  value: string
  onChange: (notes: string) => void
}

const quickInsertSuggestions = [
  { label: 'Referral', prefix: 'Mention referral from: ' },
  { label: 'Emphasize', prefix: 'Emphasize experience with: ' },
  { label: 'Avoid', prefix: 'Do not emphasize: ' },
  { label: 'Prior Contact', prefix: 'I previously spoke with: ' },
]

export function ContextNotesField({ value, onChange }: ContextNotesFieldProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handleQuickInsert = (prefix: string) => {
    const newValue = value ? `${value}\n${prefix}` : prefix
    onChange(newValue)
  }

  const charCount = value.length
  const isLong = charCount > 500

  return (
    <div className="rounded-lg border border-teal-200 bg-gradient-to-br from-teal-50/50 to-transparent dark:border-teal-800 dark:from-teal-950/20">
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="w-full flex items-center justify-between p-4 hover:bg-teal-50/50 dark:hover:bg-teal-950/30 transition-colors rounded-lg"
          >
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-teal-100 dark:bg-teal-900/50">
                <Lightbulb className="h-4 w-4 text-teal-600 dark:text-teal-400" />
              </div>
              <span className="font-medium text-sm">Context Notes</span>
              <Badge variant="outline" className="text-xs text-muted-foreground border-muted">
                Optional
              </Badge>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <HelpCircle className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <p className="text-sm">
                      Add specific details to personalize your resume and cover letter.
                      Mention referrals, emphasize certain skills, or note topics to avoid.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <div className="flex items-center gap-2">
              {value && (
                <Badge variant="secondary" className="text-xs">
                  {charCount} chars
                </Badge>
              )}
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform" />
              )}
            </div>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent className="px-4 pb-4">
          <div className="space-y-3">
            {/* Quick insert suggestions */}
            <div className="flex flex-wrap gap-2">
              {quickInsertSuggestions.map((suggestion) => (
                <Button
                  key={suggestion.label}
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs border-teal-200 hover:bg-teal-50 dark:border-teal-800 dark:hover:bg-teal-950/50"
                  onClick={() => handleQuickInsert(suggestion.prefix)}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  {suggestion.label}
                </Button>
              ))}
            </div>

            {/* Textarea */}
            <Textarea
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder="Add any special instructions, known hiring manager info, or customization requests...

Examples:
• Mention that I spoke with John Smith at the XYZ conference
• Emphasize AI governance experience for this role
• Do not lean heavily on defense work"
              rows={5}
              className="text-sm border-teal-200 focus:border-teal-400 focus:ring-teal-400/20 dark:border-teal-800 dark:focus:border-teal-600"
            />

            {/* Character count and hints */}
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-foreground">
                Context notes help tailor the summary, bullets, and cover letter.
              </span>
              <span className={isLong ? 'text-warning font-medium' : 'text-muted-foreground'}>
                {charCount} {isLong && '(consider keeping concise)'}
              </span>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}
