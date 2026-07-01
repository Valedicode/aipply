/**
 * ChoiceGate - one-button-per-option picker for orchestrator choice gates
 * (e.g. PDF/DOCX/both, English/German/skip).
 *
 * Falls back to a reject button only when 'reject' is in allowed_actions.
 */

import type { OrchestratorGateAction, OrchestratorGatePayload } from '@/types';

interface ChoiceGateProps {
  gate: OrchestratorGatePayload;
  isLoading: boolean;
  onSubmit: (
    action: OrchestratorGateAction,
    opts?: { feedback?: string; choice?: string }
  ) => void | Promise<void>;
}

const PRETTY_LABELS: Record<string, string> = {
  pdf: 'PDF only',
  docx: 'Word only',
  both: 'PDF + Word',
  english: 'English',
  german: 'German (Anschreiben)',
  skip: 'Skip',
};

export const ChoiceGate = ({ gate, isLoading, onSubmit }: ChoiceGateProps) => {
  const choices = gate.choices || [];
  const allowsReject = gate.allowed_actions.includes('reject');

  return (
    <div className="mx-auto max-w-3xl rounded-xl border border-amber-200 bg-amber-50/50 p-4 shadow-sm dark:border-amber-900/50 dark:bg-amber-950/20">
      <div className="mb-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
          Pick one · {gate.step}
        </div>
        <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{gate.narration}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {choices.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => onSubmit('choose', { choice: c })}
            disabled={isLoading}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {PRETTY_LABELS[c] ?? c}
          </button>
        ))}
        {allowsReject && (
          <button
            type="button"
            onClick={() => onSubmit('reject')}
            disabled={isLoading}
            className="rounded-md border border-rose-300 bg-white px-3 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-50 dark:border-rose-700 dark:bg-slate-900 dark:text-rose-300 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
};
