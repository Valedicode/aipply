import type { JobRequirements } from '@/types';

interface JobInputProps {
  jobText: string;
  setJobText: (text: string) => void;
  jobData: JobRequirements | null;
  isProcessing: boolean;
  error: string | null;
  onSubmit: () => void;
  onClear: () => void;
}

export const JobInput = ({
  jobText,
  setJobText,
  jobData,
  isProcessing,
  error,
  onSubmit,
  onClear,
}: JobInputProps) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
        Job Description
      </h2>

      {/* Input Area */}
      {!jobData ? (
        <div className="space-y-3">
          <div className="relative">
            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paste job description or URL here..."
              className="w-full resize-none rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:border-indigo-400"
              rows={4}
              disabled={isProcessing}
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Paste the job description text or provide a URL. Press Cmd/Ctrl + Enter to submit.
            </p>
          </div>

          <button
            onClick={onSubmit}
            disabled={!jobText.trim() || isProcessing}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-600"
          >
            {isProcessing ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Processing...
              </span>
            ) : (
              'Analyze Job'
            )}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Success Message */}
          <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900/50 dark:bg-green-950/30">
            <div className="flex items-start gap-3">
              <svg
                className="h-5 w-5 flex-shrink-0 text-green-600 dark:text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-700 dark:text-green-300">
                  Job analyzed successfully!
                </p>
                <p className="mt-1 text-xs text-green-600 dark:text-green-400">
                  {jobData.job_title} - {jobData.location}
                </p>
              </div>
            </div>
          </div>

          {/* Job Details Preview */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-700/50">
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Title:
                </span>{' '}
                <span className="text-slate-600 dark:text-slate-400">
                  {jobData.job_title}
                </span>
              </div>
              <div>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Level:
                </span>{' '}
                <span className="text-slate-600 dark:text-slate-400">
                  {jobData.job_level}
                </span>
              </div>
              <div>
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Required Skills:
                </span>{' '}
                <span className="text-slate-600 dark:text-slate-400">
                  {jobData.required_skills.slice(0, 3).join(', ')}
                  {jobData.required_skills.length > 3 && '...'}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={onClear}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          >
            Clear & Enter New Job
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900/50 dark:bg-red-950/30">
          <div className="flex items-start gap-2">
            <svg
              className="h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

