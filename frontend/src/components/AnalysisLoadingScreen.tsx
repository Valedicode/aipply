'use client';

type StepState = 'pending' | 'active' | 'done' | 'skipped';

interface StepProps {
  title: string;
  description: string;
  state: StepState;
  showConnector?: boolean;
}

const Step = ({ title, description, state, showConnector = false }: StepProps) => {
  const indicator = (() => {
    if (state === 'done') {
      return (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500 text-white dark:bg-green-400">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    }

    if (state === 'skipped') {
      return (
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400">
          <span className="text-lg">–</span>
        </div>
      );
    }

    if (state === 'active') {
      return (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white dark:bg-indigo-500">
          <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      );
    }

    return (
      <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-400 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-500">
        <span className="text-sm font-semibold">•</span>
      </div>
    );
  })();

  const titleClass =
    state === 'done'
      ? 'text-slate-900 dark:text-slate-100'
      : state === 'active'
        ? 'text-indigo-700 dark:text-indigo-300'
        : state === 'skipped'
          ? 'text-slate-600 dark:text-slate-400'
          : 'text-slate-500 dark:text-slate-500';

  const descClass =
    state === 'active'
      ? 'text-slate-600 dark:text-slate-300'
      : 'text-slate-500 dark:text-slate-400';

  const connectorVisible = state === 'done' || state === 'skipped';
  const connectorColor = connectorVisible
    ? 'bg-green-500 dark:bg-green-400'
    : 'bg-slate-300 dark:bg-slate-600';

  return (
    <div className="relative">
      <div className="flex items-start gap-4">
        <div className="relative flex-shrink-0">
          {indicator}
          {/* Connecting Line - appears only after THIS step is finished */}
          {showConnector && (
            <div
              className={`absolute left-1/2 top-10 h-6 w-0.5 -translate-x-1/2 origin-top transform transition-all duration-500 ${connectorColor} ${connectorVisible ? 'scale-y-100 opacity-100' : 'scale-y-0 opacity-0'}`}
            />
          )}
        </div>
        <div className="min-w-0 pt-0.5">
          <div className={`text-base font-semibold ${titleClass}`}>{title}</div>
          <div className={`mt-1 text-sm ${descClass}`}>{description}</div>
        </div>
      </div>
    </div>
  );
};

interface AnalysisLoadingScreenProps {
  resumeState: StepState;
  jobState: StepState;
  preparingState: StepState;
}

export const AnalysisLoadingScreen = ({
  resumeState,
  jobState,
  preparingState,
}: AnalysisLoadingScreenProps) => {
  const headline =
    resumeState === 'active'
      ? 'Extracting your resume'
      : jobState === 'active'
        ? 'Analyzing the job description'
      : preparingState === 'active'
        ? 'Preparing your AI assistant'
        : 'Starting analysis';

  const subheadline =
    resumeState === 'active'
      ? 'We’re extracting skills, experience, and achievements.'
      : jobState === 'active'
        ? 'Extracting key requirements, skills, and keywords to tailor your documents.'
      : preparingState === 'active'
        ? 'Almost ready — setting up your chat workspace.'
        : 'This usually takes a few moments.';

  return (
    <div className="flex flex-1 items-center justify-center py-10">
      <div className="w-full max-w-3xl">
        <div className="rounded-2xl bg-white p-10 shadow-lg dark:bg-slate-800">
          <div className="mx-auto max-w-xl text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300">
              <svg className="h-9 w-9 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {headline}
            </h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{subheadline}</p>
          </div>

          <div className="mt-10 space-y-6">
            <Step
              title="Resume extraction"
              description="Parsing your PDF and structuring your profile."
              state={resumeState}
              showConnector={true}
            />
            <Step
              title="Job description"
              description={
                jobState === 'active'
                  ? 'Extracting requirements and keywords to match your resume.'
                  : jobState === 'skipped'
                    ? 'Skipped — we’ll focus on general improvements.'
                    : 'Using job requirements to tailor your documents (optional).'
              }
              state={jobState}
              showConnector={true}
            />
            <Step
              title="Prepare chat"
              description="Loading your personalized assistant and tools."
              state={preparingState}
              showConnector={false}
            />
          </div>

          <div className="mt-10 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900/20 dark:text-slate-400">
            You can keep this tab open — we’ll continue automatically.
          </div>
        </div>
      </div>
    </div>
  );
};
