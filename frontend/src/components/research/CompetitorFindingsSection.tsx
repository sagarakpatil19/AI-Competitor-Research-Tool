import type { ReactNode } from "react";

export function CompetitorFindingsSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[24px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 sm:p-5 lg:p-6">
      <h2 className="mb-4 text-xl font-semibold text-[var(--foreground)]">{title}</h2>
      {children}
    </section>
  );
}
