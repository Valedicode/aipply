export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
        <div className="container mx-auto flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-blue-600">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-slate-900">
              Resume AI Agent
            </h1>
          </div>
          
          {/* Placeholder for dark mode toggle */}
          <div className="flex items-center gap-4">
            <div className="h-9 w-9 rounded-lg border border-slate-200 bg-slate-50"></div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container mx-auto flex flex-1 flex-col gap-6 p-6">
        <div className="flex flex-1 flex-col gap-6 lg:flex-row">
          
        </div>
      </main>
    </div>
  );
}
