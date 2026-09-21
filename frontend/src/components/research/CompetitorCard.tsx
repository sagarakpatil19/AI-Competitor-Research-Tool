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
    <Link href={detailHref} className="group block rounded-[28px] border border-[var(--light-border)] bg-[var(--white)] p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] transition hover:-translate-y-0.5 hover:border-[var(--primary-blue)]/30 hover:shadow-[0_20px_40px_rgba(19,48,95,0.06)] sm:p-6">
      <article>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="text-xl font-semibold tracking-[-0.04em] text-[var(--primary-navy)]">{competitor.name}</h3>
            {competitor.category && (
              <p className="mt-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                {competitor.category}
              </p>
            )}
          </div>

          {competitor.website && (
            <span className="inline-flex items-center rounded-full border border-[var(--light-border)] bg-[var(--secondary-light-blue)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--primary-blue)]">
              {new URL(competitor.website).hostname.replace("www.", "")}
            </span>
          )}
        </div>

        {competitor.description && (
          <p className="mt-4 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">{competitor.description}</p>
        )}

        {competitor.discoveryReason && (
          <div className="mt-4 rounded-[20px] border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
              Why identified
            </p>
            <p className="mt-2 text-sm leading-6 text-[var(--secondary-text)]">{competitor.discoveryReason}</p>
          </div>
        )}

        <div className="mt-5 flex justify-end">
          <span className="inline-flex items-center justify-center rounded-2xl bg-[var(--primary-blue)] px-4 py-2.5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition group-hover:-translate-y-0.5">
            Research Competitor →
          </span>
        </div>
      </article>
    </Link>
  );
}
