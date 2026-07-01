'use client';

import { useState } from 'react';
import { ResumeUpload } from '@/components/ResumeUpload';
import { JobInput } from '@/components/JobInput';
import { HowItWorks } from '@/components/HowItWorks';
import type { ResumeInfo, JobRequirements } from '@/types';

interface UploadSectionProps {
  // Flow mode selection
  flowMode: 'cv_only' | 'job_tailoring' | null;
  onSetFlowMode: (mode: 'cv_only' | 'job_tailoring') => void;

  // Resume upload props
  uploadedFile: File | null;
  isDragging: boolean;
  uploadError: string | null;
  isUploading: boolean;
  cvData: ResumeInfo | null;
  needsClarification: boolean;
  clarificationQuestions: string[] | null;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClickUpload: () => void;
  onRemoveFile: () => void;

  // Job input props
  jobUrl: string;
  setJobUrl: (url: string) => void;
  jobText: string;
  setJobText: (text: string) => void;
  jobData: JobRequirements | null;
  isJobProcessing: boolean;
  jobError: string | null;
  urlValidationError: string | null;
  textValidationError: string | null;
  onJobClear: () => void;
  
  // Manual start props
  jobSkipped: boolean;
  onSkipJob: () => void;
  onUnskipJob: () => void;
  onStartAnalysis: () => void;
  analysisStarted: boolean;
  canStartAnalysis: boolean;
}

export const UploadSection = ({
  flowMode,
  onSetFlowMode,
  uploadedFile,
  isDragging,
  uploadError,
  isUploading,
  cvData,
  needsClarification,
  clarificationQuestions,
  fileInputRef,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileInputChange,
  onClickUpload,
  onRemoveFile,
  jobUrl,
  setJobUrl,
  jobText,
  setJobText,
  jobData,
  isJobProcessing,
  jobError,
  urlValidationError,
  textValidationError,
  onJobClear,
  jobSkipped,
  onSkipJob,
  onUnskipJob,
  onStartAnalysis,
  analysisStarted,
  canStartAnalysis,
}: UploadSectionProps) => {
  // Discovery flow is a future Phase 5/6 capability. The backend orchestrator
  // already reserves the entry point (discovery_stub); the UI surfaces it as a
  // disabled CTA so it is discoverable but not yet selectable.
  const [showDiscoveryComingSoon, setShowDiscoveryComingSoon] = useState(false);
  return (
    <div className="flex flex-1 flex-col items-center justify-start">
      {/* Hero Section */}
      <div className="w-full max-w-6xl px-6 py-12 text-center">
        <h1 className="mb-6 text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-5xl lg:text-6xl">
          {flowMode === 'cv_only'
            ? 'Improve Your CV with AI'
            : flowMode === 'job_tailoring'
              ? 'Create Tailored Job Applications with AI'
              : 'What would you like to do?'}
        </h1>
        <p className="mx-auto mb-12 max-w-2xl text-lg text-slate-600 dark:text-slate-400 sm:text-xl">
          {flowMode === 'cv_only'
            ? 'Upload your resume for a structured quality review covering clarity, ATS readiness, quantified impact, and formatting'
            : flowMode === 'job_tailoring'
              ? 'Upload your resume and job description to generate a perfectly tailored resume and compelling cover letter that stands out'
              : 'Choose a flow to get started'}
        </p>

        {/* Mode Selection — shown before a flow is chosen */}
        {flowMode === null && (
          <div className="mx-auto w-full max-w-5xl">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {/* Review my CV */}
              <button
                onClick={() => onSetFlowMode('cv_only')}
                className="group flex flex-col items-center rounded-2xl border-2 border-slate-200 bg-white p-8 text-left shadow-lg transition-all hover:border-indigo-400 hover:shadow-xl dark:border-slate-700 dark:bg-slate-800 dark:hover:border-indigo-500"
              >
                <div className="mb-5 rounded-full bg-indigo-100 p-5 transition-colors group-hover:bg-indigo-200 dark:bg-indigo-900/30 dark:group-hover:bg-indigo-900/50">
                  <svg
                    className="h-10 w-10 text-indigo-600 dark:text-indigo-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h2 className="mb-2 text-xl font-semibold text-slate-900 dark:text-slate-100">
                  Review my CV
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Get a structured quality review: clarity, ATS readiness, quantified impact, and formatting
                </p>
              </button>

              {/* Tailor to a job */}
              <button
                onClick={() => onSetFlowMode('job_tailoring')}
                className="group flex flex-col items-center rounded-2xl border-2 border-slate-200 bg-white p-8 text-left shadow-lg transition-all hover:border-indigo-400 hover:shadow-xl dark:border-slate-700 dark:bg-slate-800 dark:hover:border-indigo-500"
              >
                <div className="mb-5 rounded-full bg-indigo-100 p-5 transition-colors group-hover:bg-indigo-200 dark:bg-indigo-900/30 dark:group-hover:bg-indigo-900/50">
                  <svg
                    className="h-10 w-10 text-indigo-600 dark:text-indigo-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <h2 className="mb-2 text-xl font-semibold text-slate-900 dark:text-slate-100">
                  Tailor to a job
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Match your CV to a specific job description and generate tailored application materials
                </p>
              </button>

              {/* Discover careers (Phase 5/6 - not yet available) */}
              <button
                type="button"
                onClick={() => setShowDiscoveryComingSoon(true)}
                aria-disabled="true"
                title="Coming soon"
                className="group relative flex cursor-not-allowed flex-col items-center rounded-2xl border-2 border-dashed border-slate-300 bg-white/60 p-8 text-left opacity-70 shadow-sm transition-all hover:opacity-90 dark:border-slate-700 dark:bg-slate-800/40"
              >
                <span className="absolute right-4 top-4 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
                  Coming soon
                </span>
                <div className="mb-5 rounded-full bg-slate-100 p-5 dark:bg-slate-700/40">
                  <svg
                    className="h-10 w-10 text-slate-500 dark:text-slate-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                    />
                  </svg>
                </div>
                <h2 className="mb-2 text-xl font-semibold text-slate-700 dark:text-slate-300">
                  Discover careers
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Explore roles, industries, and trajectories that fit your skills - phase 5/6
                </p>
              </button>
            </div>

            {showDiscoveryComingSoon && (
              <div
                role="status"
                className="mx-auto mt-6 max-w-xl rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 shadow-sm dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-200"
              >
                The career-discovery experience isn&rsquo;t available yet. It&rsquo;s wired into
                the orchestrator as a placeholder so the real implementation can drop in
                without changing the API or the UI. For now, pick{' '}
                <button
                  type="button"
                  className="underline underline-offset-2"
                  onClick={() => onSetFlowMode('cv_only')}
                >
                  Review my CV
                </button>{' '}
                or{' '}
                <button
                  type="button"
                  className="underline underline-offset-2"
                  onClick={() => onSetFlowMode('job_tailoring')}
                >
                  Tailor to a job
                </button>
                .
              </div>
            )}
          </div>
        )}

        {/* Main Upload Area — shown after flow is chosen */}
        {flowMode !== null && (
        <div className="mx-auto w-full max-w-4xl space-y-8">
          {/* Upload Cards Grid */}
          <div className={flowMode === 'cv_only' ? 'flex justify-center' : 'grid gap-8 lg:grid-cols-2'}>
            {/* Resume Upload Card */}
            <div className={`rounded-2xl bg-white p-8 shadow-lg dark:bg-slate-800${flowMode === 'cv_only' ? ' w-full max-w-lg' : ''}`}>
              <div className="mb-6 flex items-center justify-center">
                <div className="rounded-full bg-indigo-100 p-6 dark:bg-indigo-900/30">
                  <svg
                    className="h-16 w-16 text-indigo-600 dark:text-indigo-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
              </div>
              <h2 className="mb-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                Your Resume
              </h2>
              <p className="mb-6 text-sm text-slate-600 dark:text-slate-400">
                Upload your current resume as a PDF file
              </p>
              <ResumeUpload
                uploadedFile={uploadedFile}
                isDragging={isDragging}
                uploadError={uploadError}
                isUploading={isUploading}
                cvData={cvData}
                needsClarification={needsClarification}
                clarificationQuestions={clarificationQuestions}
                fileInputRef={fileInputRef}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                onFileInputChange={onFileInputChange}
                onClickUpload={onClickUpload}
                onRemoveFile={onRemoveFile}
              />
            </div>

            {/* Job Description Card — only shown in job_tailoring flow */}
            {flowMode === 'job_tailoring' && <div className="rounded-2xl bg-white p-8 shadow-lg dark:bg-slate-800">
              <div className="mb-6 flex items-center justify-center">
                <div className="rounded-full bg-indigo-100 p-6 dark:bg-indigo-900/30">
                  <svg
                    className="h-16 w-16 text-indigo-600 dark:text-indigo-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                </div>
              </div>
              <div className="mb-3 flex items-center justify-center gap-2">
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
                  Job Description
                </h2>
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-400">
                  Optional
                </span>
              </div>
              <p className="mb-6 text-sm text-slate-600 dark:text-slate-400">
                {jobSkipped 
                  ? 'Skipped - You can still improve your resume'
                  : 'Paste the job description or provide a URL'}
              </p>
              
              {!jobSkipped ? (
                <>
                  <JobInput
                    jobUrl={jobUrl}
                    setJobUrl={setJobUrl}
                    jobText={jobText}
                    setJobText={setJobText}
                    jobData={jobData}
                    isProcessing={isJobProcessing}
                    error={jobError}
                    urlValidationError={urlValidationError}
                    textValidationError={textValidationError}
                    onClear={onJobClear}
                  />
                  
                  {/* Skip Button - Only show if no job data yet */}
                  {!jobData && !isJobProcessing && (
                    <button
                      onClick={onSkipJob}
                      className="mt-4 w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                    >
                      Skip Job Description
                    </button>
                  )}
                </>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center dark:border-slate-700 dark:bg-slate-800/50">
                    <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
                      Job description skipped. You can add it later in the chat.
                    </p>
                  </div>
                  {/* Undo Skip Button */}
                  <button
                    onClick={onUnskipJob}
                    className="w-full rounded-lg border border-indigo-300 bg-indigo-50 px-4 py-3 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100 dark:border-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300 dark:hover:bg-indigo-900/50"
                  >
                    <span className="flex items-center justify-center gap-2">
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                      Add Job Description
                    </span>
                  </button>
                </div>
              )}
            </div>}
          </div>

          {/* Start Analysis Button */}
          {!analysisStarted && uploadedFile && (
            <div className="flex flex-col items-center gap-4">
              <button
                onClick={onStartAnalysis}
                disabled={!canStartAnalysis || isUploading || isJobProcessing}
                className="rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 px-8 py-4 text-lg font-semibold text-white shadow-lg transition-all hover:from-indigo-700 hover:to-indigo-800 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:from-indigo-600 disabled:hover:to-indigo-700 dark:from-indigo-500 dark:to-indigo-600 dark:hover:from-indigo-600 dark:hover:to-indigo-700"
              >
                {isUploading || isJobProcessing ? (
                  <span className="flex items-center gap-3">
                    <svg
                      className="h-5 w-5 animate-spin"
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
                  <span className="flex items-center gap-3">
                    <svg
                      className="h-6 w-6"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                    {flowMode === 'cv_only' ? 'Start CV Review' : 'Start Analysis'}
                  </span>
                )}
              </button>
              
              <p className="text-center text-sm text-slate-600 dark:text-slate-400">
                {flowMode === 'cv_only'
                  ? 'Review your CV for quality, clarity, and ATS readiness'
                  : (jobSkipped || !jobData
                    ? 'Analyze your resume for general improvements'
                    : 'Analyze your resume against the job requirements')}
              </p>
            </div>
          )}

          {/* Note: after Start Analysis, this view swaps to a dedicated loading screen */}
        </div>
        )}
      </div>

      {/* Instructions Section */}
      <div className="w-full max-w-6xl px-6 pb-12">
        <HowItWorks />
      </div>
    </div>
  );
};
