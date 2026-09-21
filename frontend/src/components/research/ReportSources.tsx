import type { Evidence } from "@/types/evidence";
import type { Source } from "@/types/source";
import { SourceCard } from "./SourceCard";

export function ReportSources({
  evidence,
  sources,
}: {
  evidence: Evidence[];
  sources: Record<string, Source>;
}) {
  return (
    <section className="rounded-[24px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.82)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
        Sources & Evidence
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[var(--primary-navy)]">
        Traceable evidence trail
      </h2>

      <div className="mt-5 space-y-4">
        {evidence.map((item) => {
          const source = sources[item.sourceId] ?? null;

          return (
            <div key={item.id} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-4 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--primary-blue)] sm:text-[11px]">
                Evidence record
              </p>
              <p className="mt-2 text-sm leading-7 text-[var(--primary-navy)] sm:text-base">{item.statementContext}</p>
              {source ? (
                <div className="mt-3">
                  <SourceCard source={source} />
                </div>
              ) : (
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                  Mock source metadata unavailable for this evidence item.
                </p>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
