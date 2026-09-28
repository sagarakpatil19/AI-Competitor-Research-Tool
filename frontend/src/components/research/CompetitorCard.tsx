import Link from "next/link";
import type { Competitor } from "@/types/competitor";

export function CompetitorCard({
  competitor,
  companyName,
}: {
  competitor: Competitor;
  companyName?: string;
}) {
  const detailHref = companyName
    ? `/research/competitors/${encodeURIComponent(competitor.id)}?company=${encodeURIComponent(companyName)}`
    : `/research/competitors/${encodeURIComponent(competitor.id)}`;

  return (
    <Link href={detailHref} className="block rounded-[24px] border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[0_12px_26px_rgba(16,42,86,0.02)] transition hover:border-[var(--primary-blue)]/30 hover:bg-[var(--surface-subtle)] sm:p-5">
      <article>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-semibold text-[var(--foreground)]">{competitor.name}</h3>
            {competitor.category && (
              <p className="mt-2 text-[11px] font-medium uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                {competitor.category}
              </p>
            )}
          </div>

          {competitor.website && (
            <span className="inline-flex items-center rounded-full border border-[var(--border)] bg-[var(--surface-subtle)] px-3 py-1.5 text-xs font-medium text-[var(--foreground)]">
              Visit website
            </span>
          )}
        </div>

        {competitor.description && (
          <p className="mt-4 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">{competitor.description}</p>
        )}

        {competitor.discoveryReason && (
          <div className="mt-4 rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-3.5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">
              Why identified
            </p>
            <p className="mt-2 text-sm leading-6 text-[var(--foreground)]">{competitor.discoveryReason}</p>
          </div>
        )}
      </article>
    </Link>
  );
}
