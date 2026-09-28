import type { ResearchReport } from "@/types/report";

export function ReportExecutiveSummary({ report }: { report: ResearchReport }) {
  return (
    <section className="rounded-[24px] border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
        Executive Summary
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[var(--foreground)]">
        What the research found
      </h2>
      <p className="mt-4 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">
        {report.executiveSummary}
      </p>
      <div className="mt-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-4 text-sm leading-6 text-[var(--foreground-secondary)]">
        <p className="font-medium text-[var(--foreground)]">Frontend-only mock synthesis</p>
        <p className="mt-2">
          This report is a frontend demonstration built from existing mock data, not a verified external research brief.
        </p>
      </div>
    </section>
  );
}
