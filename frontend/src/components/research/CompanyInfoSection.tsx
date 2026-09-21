import type { ReactNode } from "react";

export function CompanyInfoSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[28px] border border-[var(--light-border)] bg-[var(--white)] p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-6">
      <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">{title}</p>
      {children}
    </section>
  );
}
