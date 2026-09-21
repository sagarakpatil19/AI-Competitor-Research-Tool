import type { CompanyProfile } from "@/types/company";

export function CompanyOverview({ company }: { company: CompanyProfile }) {
  return (
    <section className="rounded-[28px] border border-[var(--light-border)] bg-[var(--white)] p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold tracking-[-0.04em] text-[var(--primary-navy)]">Company Overview</h2>
        <span className="rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
          Foundation
        </span>
      </div>
      <p className="text-sm leading-7 text-[var(--secondary-text)] sm:text-base">{company.overview}</p>
    </section>
  );
}
