'use client';

interface ProgressBreadcrumbProps {
  resumeUploaded: boolean;
  jobUploaded: boolean;
  jobSkipped: boolean;
  jobInputValid: boolean;
  analysisStarted: boolean;
  isAnalyzing: boolean;
}

interface Stage {
  id: string;
  label: string;
  completed: boolean;
  current: boolean;
}

export const ProgressBreadcrumb = ({
  resumeUploaded,
  jobUploaded,
  jobSkipped,
  jobInputValid,
  analysisStarted,
  isAnalyzing,
}: ProgressBreadcrumbProps) => {
  // Build stages dynamically - exclude job step if skipped
  const allStages: Stage[] = [
    {
      id: 'resume',
      label: 'Upload Resume',
      completed: resumeUploaded,
      current: !resumeUploaded,
    },
    // Only include job stage if not skipped
    ...(!jobSkipped ? [{
      id: 'job',
      label: 'Add Job Description',
      completed: jobUploaded || jobInputValid,
      current: resumeUploaded && !jobUploaded && !jobInputValid && !analysisStarted,
    }] : []),
    {
      id: 'analyze',
      label: 'Analysis',
      completed: analysisStarted && !isAnalyzing,
      current: isAnalyzing,
    },
    {
      id: 'chat',
      label: 'Chat Ready',
      completed: analysisStarted && !isAnalyzing,
      current: false,
    },
  ];

  const stages = allStages;

  return (
    <div className="w-full">
      <div className="flex items-center justify-center">
        {stages.map((stage, index) => (
          <div key={stage.id} className="flex items-center">
            {/* Stage Circle */}
            <div className="flex items-center gap-3">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all ${
                  stage.completed
                    ? 'border-green-500 bg-green-500 dark:border-green-400 dark:bg-green-400'
                    : stage.current
                      ? 'border-indigo-500 bg-indigo-500 dark:border-indigo-400 dark:bg-indigo-400'
                      : 'border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-800'
                }`}
              >
                {stage.completed ? (
                  <svg
                    className="h-5 w-5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : stage.current ? (
                  <div className="h-3 w-3 rounded-full bg-white"></div>
                ) : (
                  <span className="text-sm font-medium text-slate-400 dark:text-slate-500">
                    {index + 1}
                  </span>
                )}
              </div>
              
              {/* Stage Label */}
              <span
                className={`hidden text-sm font-medium transition-colors sm:block ${
                  stage.completed
                    ? 'text-green-700 dark:text-green-400'
                    : stage.current
                      ? 'text-indigo-700 dark:text-indigo-400'
                      : 'text-slate-400 dark:text-slate-500'
                }`}
              >
                {stage.label}
              </span>
            </div>

            {/* Connector Line */}
            {index < stages.length - 1 && (
              <div
                className={`mx-2 h-0.5 w-8 transition-colors sm:mx-4 sm:w-16 ${
                  stage.completed
                    ? 'bg-green-500 dark:bg-green-400'
                    : 'bg-slate-300 dark:bg-slate-600'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
