import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Generate a filename for resume or cover letter downloads
 * Format: Benjamin_Black_Resume_CompanyName_YYYYMMDD.ext
 * or: Benjamin_Black_Cover_Letter_CompanyName_YYYYMMDD.ext
 */
export function generateDownloadFilename(
  type: 'resume' | 'cover-letter',
  companyName: string | undefined,
  extension: string
): string {
  const userName = process.env.NEXT_PUBLIC_USER_NAME || 'User'
  const safeName = userName.replace(/\s+/g, '_')

  // Sanitize company name: remove special chars, replace spaces with underscores
  const safeCompany = companyName
    ? companyName.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 30)
    : 'Company'

  // Format date as YYYYMMDD
  const today = new Date()
  const dateStr = today.toISOString().slice(0, 10).replace(/-/g, '')

  const docType = type === 'resume' ? 'Resume' : 'Cover_Letter'

  return `${safeName}_${docType}_${safeCompany}_${dateStr}.${extension}`
}
