import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Providers from './providers'
import { Toaster } from '@/components/ui/sonner'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'ETPS - Enterprise-Grade Talent Positioning System',
  description: 'AI-powered resume and cover letter tailoring system for enterprise professionals',
  keywords: ['resume', 'cover letter', 'AI', 'job application', 'ATS', 'career'],
  authors: [{ name: 'Benjamin Black' }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} antialiased`}>
        <Providers>
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <main id="main-content" tabIndex={-1}>
            {children}
          </main>
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  )
}
