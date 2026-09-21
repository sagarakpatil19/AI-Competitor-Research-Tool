import type { CompetitorResearchFindings } from "@/types/competitor-findings";
import { EvidenceList } from "./EvidenceList";
import { CompetitorFindingsSection } from "./CompetitorFindingsSection";

export function CompetitorResearchFindingsComponent({
  findings,
}: {
  findings: CompetitorResearchFindings;
}) {
  return (
    <div className="space-y-5">
      <CompetitorFindingsSection title="Company Overview">
        <p className="text-sm leading-7 text-[var(--secondary-text)] sm:text-base">{findings.overview}</p>

        {findings.positioning.length > 0 && (
          <div className="mt-4 rounded-[18px] border border-[var(--light-border)] bg-[var(--very-soft-blue)] p-3.5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)] sm:text-[11px]">
              Positioning
            </p>
            <ul className="mt-3 space-y-2 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
              {findings.positioning.map((item) => (
                <li key={item} className="flex gap-2">
                  <span aria-hidden="true" className="mt-2 inline-block h-1.5 w-1.5 rounded-full bg-[var(--primary-blue)]" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.overview} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Products">
        <ul className="space-y-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
          {findings.products.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-3.5 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.products} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Features">
        <ul className="space-y-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
          {findings.features.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-3.5 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.features} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Pricing">
        <ul className="space-y-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
          {findings.pricing.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-3.5 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.pricing} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Target Audience">
        <ul className="space-y-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
          {findings.targetAudience.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-3.5 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.targetAudience} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>

      <CompetitorFindingsSection title="Customer Feedback">
        <ul className="space-y-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
          {findings.customerFeedback.map((item) => (
            <li key={item} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-3.5 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4">
          <EvidenceList evidence={findings.evidence.customerFeedback} sources={findings.sources} />
        </div>
      </CompetitorFindingsSection>
    </div>
  );
}
