import type { JobRequirements } from '@/types';

interface JobInputProps {
  jobUrl: string;
  setJobUrl: (url: string) => void;
  jobText: string;
  setJobText: (text: string) => void;
  jobData: JobRequirements | null;
  isProcessing: boolean;
  error: string | null;
  urlValidationError: string | null;
  textValidationError: string | null;
  onClear: () => void;
}

export const JobInput = ({
  jobUrl,
  setJobUrl,
  jobText,
  setJobText,
  jobData,
  isProcessing,
  error,
  urlValidationError,
  textValidationError,
  onClear,
}: JobInputProps) => {
  return (
    <div>
      {/* Input Area */}
      {!jobData ? (
        <div className="space-y-4">
          {/* URL Input */}
          <div className="relative">
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Job Posting URL (Optional)
            </label>
            <input
              type="url"
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              placeholder="https://example.com/job-posting"
              className={`w-full rounded-xl border px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:bg-slate-800/30 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:bg-slate-800 ${
                urlValidationError
                  ? 'border-red-300 bg-red-50/50 focus:border-red-500 dark:border-red-700 dark:bg-red-950/20 dark:focus:border-red-500'
                  : 'border-slate-300 bg-slate-50/50 focus:border-indigo-500 focus:bg-white dark:border-slate-600 dark:focus:border-indigo-400'
              }`}
            />
            {urlValidationError && (
              <p className="mt-1.5 text-xs text-red-600 dark:text-red-400">
                {urlValidationError}
              </p>
            )}
            {!urlValidationError && jobUrl.trim() && (
              <p className="mt-1.5 text-xs text-green-600 dark:text-green-400">
                Valid URL
              </p>
            )}
          </div>

          {/* Text Input */}
          <div className="relative">
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Job Description Text (Optional)
            </label>
            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              placeholder="Paste the job description text here (minimum 50 characters)..."
              className={`min-h-[200px] w-full resize-none rounded-xl border px-4 py-4 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:bg-slate-800/30 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:bg-slate-800 ${
                textValidationError
                  ? 'border-red-300 bg-red-50/50 focus:border-red-500 dark:border-red-700 dark:bg-red-950/20 dark:focus:border-red-500'
                  : 'border-slate-300 bg-slate-50/50 focus:border-indigo-500 focus:bg-white dark:border-slate-600 dark:focus:border-indigo-400'
              }`}
            />
            <div className="mt-2 flex items-center justify-between">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {textValidationError ? (
                  <span className="text-red-600 dark:text-red-400">{textValidationError}</span>
                ) : jobText.trim().length > 0 ? (
                  <span className={jobText.trim().length >= 50 ? 'text-green-600 dark:text-green-400' : 'text-slate-500 dark:text-slate-400'}>
                    {jobText.trim().length} characters
                  </span>
                ) : (
                  'Enter at least 50 characters'
                )}
              </p>
              {jobText.trim().length >= 50 && (
                <p className="text-xs text-green-600 dark:text-green-400">Valid</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
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
                <p className="font-medium text-green-700 dark:text-green-300">
                  Job analyzed successfully!
                </p>
                <p className="mt-0.5 text-sm text-green-600 dark:text-green-400">
                  {jobData.job_title} - {jobData.location}
                </p>
              </div>
            </div>
          </div>

          {/* Job Details Preview */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
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
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            Clear & Enter New Job
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30">
          <div className="flex items-start gap-3">
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
            <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};



