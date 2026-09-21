import type { Evidence } from "@/types/evidence";
import type { Source } from "@/types/source";
import { SourceCard } from "./SourceCard";

export function EvidenceList({
  evidence,
  sources,
}: {
  evidence: Evidence[];
  sources: Record<string, Source>;
}) {
  if (evidence.length === 0) {
    return (
      <p className="text-sm leading-7 text-[var(--muted)] sm:text-base">
        No supporting evidence recorded for this finding yet.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)] sm:text-[11px]">
        Evidence
      </p>

      {evidence.map((item) => {
        const source = sources[item.sourceId] ?? null;

        return (
          <div
            key={item.id}
            className="rounded-[20px] border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-3.5 sm:p-4"
          >
            <p className="text-sm leading-7 text-[var(--primary-navy)] sm:text-base">
              {item.statementContext}
            </p>

            {source ? (
              <div className="mt-3">
                <SourceCard source={source} />
              </div>
            ) : (
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                Source unavailable for this evidence record.
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
