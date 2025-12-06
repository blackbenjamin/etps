export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">ETPS</h1>
        <p className="text-xl text-gray-600 mb-8">
          Enterprise-Grade Talent Positioning System
        </p>
        <p className="text-gray-500">
          An AI-Orchestrated Resume, Cover Letter, and Networking Intelligence
          Platform
        </p>

        {/* TODO: Implement job intake form */}
        {/* TODO: Add resume/cover letter generation buttons */}
        {/* TODO: Add download buttons for docx, text, JSON */}
        {/* TODO: Add skill-gap analysis panel */}
      </div>
    </main>
  );
}
