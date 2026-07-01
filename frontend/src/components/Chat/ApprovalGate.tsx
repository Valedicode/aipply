/**
 * ApprovalGate - approve / edit / reject buttons for orchestrator approval gates.
 *
 * Edit reveals an inline textarea; submitting it calls onSubmit('edit', {feedback}).
 * Buttons hide themselves if not in `allowed_actions` so the same component
 * serves both soft gates (approve/reject only) and hard gates (approve/edit/reject).
 */

import { useState } from 'react';
import type { OrchestratorGateAction, OrchestratorGatePayload } from '@/types';
import { PreviewCard } from './PreviewCard';

interface ApprovalGateProps {
  gate: OrchestratorGatePayload;
  isLoading: boolean;
  onSubmit: (
    action: OrchestratorGateAction,
    opts?: { feedback?: string; choice?: string }
  ) => void | Promise<void>;
}

export const ApprovalGate = ({ gate, isLoading, onSubmit }: ApprovalGateProps) => {
  const [showEdit, setShowEdit] = useState(false);
  const [feedback, setFeedback] = useState('');

  const allows = (a: OrchestratorGateAction) => gate.allowed_actions.includes(a);

  const handleEditSubmit = async () => {
    if (!feedback.trim()) return;
    await onSubmit('edit', { feedback: feedback.trim() });
    setShowEdit(false);
    setFeedback('');
  };

  return (
    <div className="mx-auto max-w-3xl rounded-xl border border-indigo-200 bg-indigo-50/50 p-4 shadow-sm dark:border-indigo-900/50 dark:bg-indigo-950/20">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-300">
            Approval needed · {gate.step}
          </div>
          <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{gate.narration}</p>
        </div>
      </div>

      <div className="mb-4 rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
        <PreviewCard gate={gate} />
      </div>

      {showEdit ? (
        <div className="space-y-2">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="What should change? (e.g. 'Use stronger action verbs', 'Mention Kubernetes more')"
            className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            rows={3}
            disabled={isLoading}
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleEditSubmit}
              disabled={isLoading || !feedback.trim()}
              className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              Submit edit
            </button>
            <button
              type="button"
              onClick={() => {
                setShowEdit(false);
                setFeedback('');
              }}
              disabled={isLoading}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {allows('approve') && (
            <button
              type="button"
              onClick={() => onSubmit('approve')}
              disabled={isLoading}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Approve
            </button>
          )}
          {allows('edit') && (
            <button
              type="button"
              onClick={() => setShowEdit(true)}
              disabled={isLoading}
              className="rounded-md border border-indigo-300 bg-white px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-50 disabled:opacity-50 dark:border-indigo-700 dark:bg-slate-900 dark:text-indigo-300 dark:hover:bg-slate-800"
            >
              Edit with feedback
            </button>
          )}
          {allows('reject') && (
            <button
              type="button"
              onClick={() => onSubmit('reject')}
              disabled={isLoading}
              className="rounded-md border border-rose-300 bg-white px-3 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-50 dark:border-rose-700 dark:bg-slate-900 dark:text-rose-300 dark:hover:bg-slate-800"
            >
              Reject
            </button>
          )}
        </div>
      )}
    </div>
  );
};
