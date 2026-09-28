import type { CompanyProfile } from "@/types/company";

export function CompanyOverview({ company }: { company: CompanyProfile }) {
  return (
    <section className="rounded-[28px] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[0_18px_34px_rgba(16,42,86,0.04)] sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold tracking-[-0.04em] text-[var(--foreground)]">Company Overview</h2>
        <span className="rounded-full border border-[var(--border)] bg-[var(--surface-subtle)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
          Foundation
        </span>
      </div>
      <p className="text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">{company.overview}</p>
    </section>
  );
}
