import type { ReportInsight } from "@/types/report";

export function ReportAIInsights({ insights }: { insights: ReportInsight[] }) {
  return (
    <section className="rounded-[24px] border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
        AI Research Insights
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[var(--foreground)]">
        AI-assisted interpretation
      </h2>

      <div className="mt-5 space-y-4">
        {insights.map((insight) => (
          <div key={insight.title} className="rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--primary-blue)] sm:text-[11px]">
              {insight.kind === "analysis" ? "AI analysis" : "Pattern note"}
            </p>
            <p className="mt-2 text-lg font-medium text-[var(--foreground)]">{insight.title}</p>
            <p className="mt-2 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">{insight.summary}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
