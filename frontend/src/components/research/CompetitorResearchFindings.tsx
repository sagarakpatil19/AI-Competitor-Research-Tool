import type { CompetitorResearchFindings } from "@/types/competitor-findings";
import { EvidenceList } from "./EvidenceList";
import { SourceCard } from "./SourceCard";
import { CompetitorFindingsSection } from "./CompetitorFindingsSection";

export function CompetitorResearchFindingsComponent({
  findings,
}: {
  findings: CompetitorResearchFindings;
}) {
  return (
    <div className="space-y-5">
      <CompetitorFindingsSection title="Overview">
        <p className="text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">{findings.overview}</p>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.overview} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Products">
        <ul className="space-y-3 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">
          {findings.products.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3.5">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.products} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Features">
        <ul className="space-y-3 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">
          {findings.features.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3.5">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.features} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Pricing">
        <ul className="space-y-3 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">
          {findings.pricing.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3.5">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.pricing} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Target Audience">
        <ul className="space-y-3 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">
          {findings.targetAudience.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3.5">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.targetAudience} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Positioning">
        <ul className="space-y-3 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">
          {findings.positioning.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3.5">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.positioning} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Customer Feedback">
        <ul className="space-y-3 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">
          {findings.customerFeedback.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3.5">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.customerFeedback} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Supporting References">
        <div className="space-y-3">
          {Object.values(findings.sources).map((source) => (
            <SourceCard key={source.id} source={source} />
          ))}
        </div>
      </CompetitorFindingsSection>
    </div>
  );
}
