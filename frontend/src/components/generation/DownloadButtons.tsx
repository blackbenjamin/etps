'use client'

import { Download, Code, FileText, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useDownloadResume, useDownloadCoverLetter, useDownloadResumeText, useDownloadCoverLetterText } from '@/hooks/queries'
import type { TailoredResume, GeneratedCoverLetter } from '@/types'

interface DownloadButtonsProps {
  type: 'resume' | 'cover-letter'
  jobProfileId: number
  jsonData: TailoredResume | GeneratedCoverLetter
}

export function DownloadButtons({ type, jobProfileId, jsonData }: DownloadButtonsProps) {
  const downloadResume = useDownloadResume()
  const downloadResumeText = useDownloadResumeText()
  const downloadCoverLetter = useDownloadCoverLetter()
  const downloadCoverLetterText = useDownloadCoverLetterText()

  const isDownloading = downloadResume.isPending || downloadCoverLetter.isPending || downloadResumeText.isPending || downloadCoverLetterText.isPending

  const handleDownloadDocx = async () => {
    if (type === 'resume') {
      await downloadResume.mutateAsync(jsonData as TailoredResume)
    } else {
      await downloadCoverLetter.mutateAsync(jobProfileId)
    }
  }

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${type}_${jobProfileId}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleDownloadTxt = async () => {
    if (type === 'resume') {
      await downloadResumeText.mutateAsync(jsonData as TailoredResume)
    } else {
      await downloadCoverLetterText.mutateAsync(jobProfileId)
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
