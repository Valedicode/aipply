export const HowItWorks = () => {
  return (
    <div className="rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50 to-blue-50 p-5 dark:border-indigo-900/50 dark:from-indigo-950/50 dark:to-blue-950/50">
      <h3 className="mb-2 text-sm font-semibold text-indigo-900 dark:text-indigo-300">
        How it works
      </h3>
      <ol className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
        <li className="flex gap-2">
          <span className="font-semibold text-indigo-600 dark:text-indigo-400">1.</span>
          <span>Upload your resume PDF</span>
        </li>
        <li className="flex gap-2">
          <span className="font-semibold text-indigo-600 dark:text-indigo-400">2.</span>
          <span>Paste job description or URL</span>
        </li>
        <li className="flex gap-2">
          <span className="font-semibold text-indigo-600 dark:text-indigo-400">3.</span>
          <span>Review AI suggestions</span>
        </li>
        <li className="flex gap-2">
          <span className="font-semibold text-indigo-600 dark:text-indigo-400">4.</span>
          <span>Download optimized resume</span>
        </li>
      </ol>
    </div>
  );
};


