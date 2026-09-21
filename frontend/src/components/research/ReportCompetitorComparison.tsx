import type { ReportComparisonRow } from "@/types/report";

export function ReportCompetitorComparison({ comparison }: { comparison: ReportComparisonRow[] }) {
  return (
    <section className="rounded-[24px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.82)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
        Competitor Landscape
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[var(--primary-navy)]">
        Comparison overview
      </h2>

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-y-2 text-left text-sm text-[var(--secondary-text)]">
          <thead>
            <tr>
              <th className="pr-4 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">
                Category
              </th>
              <th className="pr-4 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">
                Target Company
              </th>
              {comparison[0]?.competitors.map((competitor) => (
                <th key={competitor.name} className="pr-4 pb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">
                  {competitor.name}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {comparison.map((row) => (
              <tr key={row.category} className="align-top">
                <td className="rounded-l-2xl border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-3 font-medium text-[var(--primary-navy)]">
                  {row.category}
                </td>
                <td className="border border-[var(--light-border)] bg-white p-3 leading-6 text-[var(--primary-navy)]">
                  {row.targetCompany}
                </td>
                {row.competitors.map((competitor) => (
                  <td key={`${row.category}-${competitor.name}`} className="border border-[var(--light-border)] bg-white p-3 leading-6 text-[var(--primary-navy)]">
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
