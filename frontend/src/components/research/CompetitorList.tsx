import type { Competitor } from "@/types/competitor";
import { CompetitorCard } from "./CompetitorCard";

export function CompetitorList({
  competitors,
  companyName,
}: {
  competitors: Competitor[];
  companyName?: string;
}) {
  if (competitors.length === 0) {
    return (
      <div className="rounded-[24px] border border-white/10 bg-[rgba(255,255,255,0.02)] p-6 text-sm leading-7 text-[var(--muted)] sm:text-base">
        No relevant competitors were identified.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {competitors.map((competitor) => (
        <CompetitorCard key={competitor.id} competitor={competitor} companyName={companyName} />
      ))}
    </div>
  );
}
