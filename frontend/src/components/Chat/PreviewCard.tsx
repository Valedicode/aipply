/**
 * PreviewCard - typed renderer for the preview payload of an orchestrator gate.
 *
 * Switches on the gate's `step` to pick a sensible compact rendering. Falls
 * back to a JSON dump in a code block for unknown steps so nothing is hidden.
 */

import type { OrchestratorGatePayload } from '@/types';

type PreviewMap = Record<string, unknown>;

interface PreviewCardProps {
  gate: OrchestratorGatePayload;
}

// --------------------------------------------------------------------------
// Step-specific preview shapes. The orchestrator backend is the source of
// truth; these are mirrors used only for rendering convenience.
// --------------------------------------------------------------------------

interface ScorePreview {
  aggregate_score?: number;
  level?: string;
  dimensions?: Array<{ name: string; score: number; weight: number }>;
  gap_analysis?: {
    matched_skills?: unknown[];
    transferable_skills?: unknown[];
    missing_skills?: unknown[];
  };
  interpretation?: string;
}

interface SelectionPreview {
  selected_bullets?: Array<{
    section: string;
    original_text: string;
    relevance_score: number;
  }>;
  section_order?: string[];
  sections_to_emphasize?: string[];
}

interface RewritePreview {
  rewritten_bullets?: Array<{
    original: string;
    rewritten: string;
    confidence: number;
    keywords_added?: string[];
  }>;
  keywords_inserted?: string[];
}

interface CoverLetterPreview {
  opening_paragraph?: string;
  body_paragraph_1?: string;
  body_paragraph_2?: string;
  body_paragraph_3?: string;
  closing_paragraph?: string;
  betreff?: string;
  grussformel?: string;
}

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="mb-3 last:mb-0">
    <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
      {title}
    </h4>
    {children}
  </div>
);

const Pill = ({ children }: { children: React.ReactNode }) => (
  <span className="inline-block rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-200">
    {children}
  </span>
);

function PresentScore({ preview }: { preview: PreviewMap }) {
  const p = preview as ScorePreview;
  const score = typeof p.aggregate_score === 'number' ? p.aggregate_score : null;
  const level = p.level ?? 'unknown';
  const dimensions = p.dimensions ?? [];
  const gap = p.gap_analysis ?? {};
  return (
    <div>
      <Section title="Score">
        <div className="text-2xl font-bold text-slate-900 dark:text-slate-50">
          {score !== null ? score.toFixed(2) : '—'}{' '}
          <span className="ml-2 text-sm font-normal uppercase text-slate-500">{level}</span>
        </div>
      </Section>
      {dimensions.length > 0 && (
        <Section title="Dimensions">
          <ul className="space-y-1 text-sm">
            {dimensions.map((d) => (
              <li key={d.name} className="flex justify-between font-mono">
                <span>{d.name}</span>
                <span className="text-slate-500">
                  {d.score.toFixed(2)} × {Math.round((d.weight || 0) * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </Section>
      )}
      <Section title="Gaps">
        <div className="text-sm">
          Matched: {(gap.matched_skills || []).length} · Transferable:{' '}
          {(gap.transferable_skills || []).length} · Missing:{' '}
          {(gap.missing_skills || []).length}
        </div>
      </Section>
      {p.interpretation && (
        <Section title="Interpretation">
          <p className="text-sm text-slate-700 dark:text-slate-300">{p.interpretation}</p>
        </Section>
      )}
    </div>
  );
}

function ApproveSelection({ preview }: { preview: PreviewMap }) {
  const p = preview as SelectionPreview;
  const bullets = p.selected_bullets ?? [];
  const order = p.section_order ?? [];
  const emphasis = p.sections_to_emphasize ?? [];
  return (
    <div>
      {order.length > 0 && (
        <Section title="Proposed section order">
          <div className="flex flex-wrap gap-1">
            {order.map((s) => (
              <Pill key={s}>{s}</Pill>
            ))}
          </div>
        </Section>
      )}
      {emphasis.length > 0 && (
        <Section title="Emphasised">
          <div className="flex flex-wrap gap-1">
            {emphasis.map((s) => (
              <Pill key={s}>{s}</Pill>
            ))}
          </div>
        </Section>
      )}
      {bullets.length > 0 && (
        <Section title={`Top bullets (${bullets.length})`}>
          <ul className="space-y-2 text-sm">
            {bullets.slice(0, 8).map((b, i) => (
              <li
                key={i}
                className="rounded border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-800"
              >
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  {b.section} · relevance{' '}
                  {typeof b.relevance_score === 'number' ? b.relevance_score.toFixed(2) : '?'}
                </div>
                <div className="text-slate-800 dark:text-slate-100">{b.original_text}</div>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function ApproveRewrite({ preview }: { preview: PreviewMap }) {
  const p = preview as RewritePreview;
  const bullets = p.rewritten_bullets ?? [];
  const keywords = p.keywords_inserted ?? [];
  return (
    <div>
      {keywords.length > 0 && (
        <Section title="Keywords woven in">
          <div className="flex flex-wrap gap-1">
            {keywords.map((k) => (
              <Pill key={k}>{k}</Pill>
            ))}
          </div>
        </Section>
      )}
      <Section title={`Rewrites (${bullets.length})`}>
        <ul className="space-y-2 text-sm">
          {bullets.slice(0, 8).map((b, i) => (
            <li
              key={i}
              className="rounded border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-800"
            >
              <div className="text-xs uppercase tracking-wide text-slate-500">
                confidence {typeof b.confidence === 'number' ? b.confidence.toFixed(2) : '?'}
              </div>
              <div className="text-slate-500 line-through">{b.original}</div>
              <div className="mt-1 text-slate-800 dark:text-slate-100">{b.rewritten}</div>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

function ApproveCoverLetter({ preview }: { preview: PreviewMap }) {
  const p = preview as CoverLetterPreview;
  const paras = [
    p.opening_paragraph,
    p.body_paragraph_1,
    p.body_paragraph_2,
    p.body_paragraph_3,
    p.closing_paragraph,
  ].filter((s): s is string => typeof s === 'string' && s.trim().length > 0);
  return (
    <div>
      {p.betreff && (
        <Section title="Betreff">
          <div className="text-sm font-semibold">{p.betreff}</div>
        </Section>
      )}
      <Section title="Letter">
        <div className="space-y-2 text-sm text-slate-800 dark:text-slate-100">
          {paras.map((para, i) => (
            <p key={i}>{para}</p>
          ))}
        </div>
      </Section>
      {p.grussformel && (
        <Section title="Grußformel">
          <div className="text-sm">{p.grussformel}</div>
        </Section>
      )}
    </div>
  );
}

function GenericJson({ preview }: { preview: PreviewMap }) {
  if (!preview || Object.keys(preview).length === 0) {
    return <p className="text-sm text-slate-500">No preview data for this gate.</p>;
  }
  return (
    <pre className="max-h-64 overflow-auto rounded bg-slate-50 p-2 text-xs text-slate-700 dark:bg-slate-800 dark:text-slate-200">
      {JSON.stringify(preview, null, 2)}
    </pre>
  );
}

export const PreviewCard = ({ gate }: PreviewCardProps) => {
  switch (gate.step) {
    case 'present_score':
      return <PresentScore preview={gate.preview} />;
    case 'approve_selection':
      return <ApproveSelection preview={gate.preview} />;
    case 'approve_rewrite':
      return <ApproveRewrite preview={gate.preview} />;
    case 'approve_cover_letter':
      return <ApproveCoverLetter preview={gate.preview} />;
    default:
      return <GenericJson preview={gate.preview} />;
  }
};
