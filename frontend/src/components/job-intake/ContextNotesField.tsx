'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ContextNotesFieldProps {
  value: string
  onChange: (notes: string) => void
}

export function ContextNotesField({ value, onChange }: ContextNotesFieldProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 mr-1" />
        ) : (
          <ChevronRight className="h-4 w-4 mr-1" />
        )}
        Add Context Notes (Optional)
      </button>
      {isExpanded && (
        <div className="space-y-2">
          <Textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Add any special instructions, known hiring manager info, or customization requests...

Examples:
• Mention that I spoke with John Smith at the XYZ conference
• Emphasize AI governance experience for this role
• Do not lean heavily on defense work"
            rows={5}
            className="text-sm"
          />
          <p className="text-xs text-muted-foreground">
            Context notes help tailor the summary, bullets, and cover letter to your specific situation.
          </p>
        </div>
      )}
    </div>
  )
}
