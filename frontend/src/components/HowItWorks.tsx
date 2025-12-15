'use client';

import { useState } from 'react';

interface StepData {
  number: number;
  title: string;
  description: string;
}

const steps: StepData[] = [
  {
    number: 1,
    title: 'Upload your resume PDF',
    description:
      'Drag and drop your existing resume or click to browse. Our AI analyzes your resume, extracting your skills, experience, and qualifications. If any information is unclear, we\'ll ask clarifying questions through chat to ensure accuracy.',
  },
  {
    number: 2,
    title: 'Add job description',
    description:
      'Paste the job description text directly or provide a URL to the job posting. Our AI analyzes the requirements, identifies key skills, and understands exactly what the employer is looking for to match with your profile.',
  },
  {
    number: 3,
    title: 'Chat with AI to fine-tune',
    description:
      'Our AI supervisor analyzes the gap between your resume and job requirements. Chat with the AI to refine your resume, request specific improvements, or ask for suggestions. The AI can transform your resume to be perfectly tailored to the job description.',
  },
  {
    number: 4,
    title: 'Generate tailored documents',
    description:
      'Request the AI to generate a tailored resume optimized for the job description, or create a compelling cover letter based on your resume and the job requirements. Download your professionally formatted documents as PDF when ready.',
  },
];

export const HowItWorks = () => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(stepNumber)) {
        newSet.delete(stepNumber);
      } else {
        newSet.add(stepNumber);
      }
      return newSet;
    });
  };

  return (
    <div className="rounded-2xl bg-white p-8 shadow-lg dark:bg-slate-800">
      <h3 className="mb-8 text-center text-2xl font-semibold text-slate-900 dark:text-slate-100">
        How It Works
      </h3>
      <ol className="space-y-6">
        {steps.map((step) => {
          const isExpanded = expandedSteps.has(step.number);
          return (
            <li key={step.number} className="flex gap-5">
              <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-indigo-600 text-lg font-semibold text-white shadow-sm dark:from-indigo-400 dark:to-indigo-500">
                {step.number}
              </span>
              <div className="flex-1 pt-1">
                <button
                  onClick={() => toggleStep(step.number)}
                  className="group flex w-full items-start justify-between gap-3 text-left transition-colors"
                >
                  <h4 className="text-lg font-semibold text-slate-900 transition-colors group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-400">
                    {step.title}
                  </h4>
                  <svg
                    className={`mt-1 h-5 w-5 flex-shrink-0 text-slate-400 transition-transform ${
                      isExpanded ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {isExpanded && (
                  <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                    {step.description}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
};


