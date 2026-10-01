import type { ReportComparisonRow } from "@/types/report";

export function ReportCompetitorComparison({ comparison }: { comparison: ReportComparisonRow[] }) {
  return (
    <section className="rounded-[24px] border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
        Competitor Landscape
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[var(--foreground)]">
        Comparison overview
      </h2>

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-y-2 text-left text-sm text-[var(--foreground-secondary)]">
          <thead>
            <tr>
              <th className="pr-4 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">
                Category
              </th>
              <th className="pr-4 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">
                Target Company
              </th>
              {comparison[0]?.competitors.map((competitor) => (
                <th key={competitor.name} className="pr-4 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">
                  {competitor.name}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {comparison.map((row) => (
              <tr key={row.category} className="align-top">
                <td className="rounded-l-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-3 font-medium text-[var(--foreground)]">
                  {row.category}
                </td>
                <td className="border border-[var(--border)] bg-[var(--surface)] p-3 leading-6 text-[var(--foreground)]">
                  {row.targetCompany}
                </td>
                {row.competitors.map((competitor) => (
                  <td key={`${row.category}-${competitor.name}`} className="border border-[var(--border)] bg-[var(--surface)] p-3 leading-6 text-[var(--foreground)]">
                    {competitor.value}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
