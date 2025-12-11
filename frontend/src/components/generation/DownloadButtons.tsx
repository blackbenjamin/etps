'use client'

import { Download, Code, FileText, Loader2, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { useDownloadResume, useDownloadCoverLetter, useDownloadResumeText, useDownloadCoverLetterText } from '@/hooks/queries'
import { generateDownloadFilename } from '@/lib/utils'
import type { TailoredResume, GeneratedCoverLetter } from '@/types'

interface DownloadButtonsProps {
  type: 'resume' | 'cover-letter'
  jobProfileId?: number // Kept for backwards compatibility but no longer used
  jsonData: TailoredResume | GeneratedCoverLetter
  companyName?: string
}

export function DownloadButtons({ type, jsonData, companyName }: DownloadButtonsProps) {
  const downloadResume = useDownloadResume()
  const downloadResumeText = useDownloadResumeText()
  const downloadCoverLetter = useDownloadCoverLetter()
  const downloadCoverLetterText = useDownloadCoverLetterText()

  const isDownloading = downloadResume.isPending || downloadCoverLetter.isPending || downloadResumeText.isPending || downloadCoverLetterText.isPending

  const docLabel = type === 'resume' ? 'Resume' : 'Cover Letter'

  const handleDownloadDocx = async () => {
    try {
      if (type === 'resume') {
        await downloadResume.mutateAsync({ resume: jsonData as TailoredResume, companyName })
      } else {
        await downloadCoverLetter.mutateAsync({ coverLetter: jsonData as GeneratedCoverLetter, companyName })
      }
      toast.success(`${docLabel} downloaded`, {
        description: `${generateDownloadFilename(type, companyName, 'docx')}`,
        icon: <CheckCircle2 className="h-4 w-4" />,
      })
    } catch (error) {
      toast.error('Download failed', {
        description: error instanceof Error ? error.message : 'Please try again',
      })
    }
  }

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = generateDownloadFilename(type, companyName, 'json')
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success(`${docLabel} JSON exported`, {
      description: generateDownloadFilename(type, companyName, 'json'),
      icon: <CheckCircle2 className="h-4 w-4" />,
    })
  }

  const handleDownloadTxt = async () => {
    try {
      if (type === 'resume') {
        await downloadResumeText.mutateAsync({ resume: jsonData as TailoredResume, companyName })
      } else {
        await downloadCoverLetterText.mutateAsync({ coverLetter: jsonData as GeneratedCoverLetter, companyName })
      }
      toast.success(`${docLabel} text exported`, {
        description: generateDownloadFilename(type, companyName, 'txt'),
        icon: <CheckCircle2 className="h-4 w-4" />,
      })
    } catch (error) {
      toast.error('Export failed', {
        description: error instanceof Error ? error.message : 'Please try again',
      })
    }
  }

  return (
    <div className="flex gap-2 flex-wrap">
      <Button
        onClick={handleDownloadDocx}
        disabled={isDownloading}
        size="sm"
      >
        {isDownloading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Download className="mr-2 h-4 w-4" />
        )}
        DOCX
      </Button>
      <Button onClick={handleDownloadTxt} variant="outline" size="sm" disabled={isDownloading}>
        <FileText className="mr-2 h-4 w-4" />
        TXT
      </Button>
      <Button onClick={handleDownloadJson} variant="outline" size="sm" disabled={isDownloading}>
        <Code className="mr-2 h-4 w-4" />
        JSON
      </Button>
    </div>
  )
}
