import type { ReactNode } from "react";

export function CompetitorFindingsSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[24px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.82)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
      <h2 className="mb-4 text-xl font-semibold tracking-[-0.04em] text-[var(--primary-navy)]">{title}</h2>
      {children}
    </section>
  );
}
