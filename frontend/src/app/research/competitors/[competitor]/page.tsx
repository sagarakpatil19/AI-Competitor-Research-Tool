"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { CompetitorResearchFindingsComponent } from "@/components/research/CompetitorResearchFindings";
import type { CompetitorResearchFindings } from "@/types/competitor-findings";
import {
  fetchCompetitorEvidence,
  fetchCompetitorSources,
  getApiErrorMessage,
  mapBackendCompetitorFindings,
  pollBackgroundOperation,
  researchCompetitors,
} from "@/lib/api";

function CompetitorDetailsContent() {
  const params = useParams<{ competitor: string }>();
  const searchParams = useSearchParams();
  const researchId = searchParams.get("research_id")?.trim() ?? "";
  const competitorParam = Array.isArray(params.competitor) ? params.competitor[0] : params.competitor ?? "";
  const competitorId = decodeURIComponent(competitorParam);
  const companyName = searchParams.get("company")?.trim() ?? "Company";
  const [findings, setFindings] = useState<CompetitorResearchFindings | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(Boolean(researchId && competitorId));

  useEffect(() => {
    if (!researchId || !competitorId) {
      setFindings(null);
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    const loadFindings = async () => {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const numericCompetitorId = Number(competitorId);

        if (!Number.isInteger(numericCompetitorId) || numericCompetitorId <= 0) {
          throw new Error("The competitor route does not contain a valid backend competitor ID.");
        }

        const operation = await researchCompetitors(researchId, [numericCompetitorId]);
        const finishedOperation = await pollBackgroundOperation(operation.status_url, 120000, 2000);
        const result = (finishedOperation.result ?? {}) as { competitor_research?: unknown[] };
        const competitorResearch = result.competitor_research?.find((item) => {
          const value = item as { competitor_id?: number };
          return value.competitor_id === numericCompetitorId;
        });

        if (!competitorResearch) {
          throw new Error("The backend did not return research details for this competitor.");
        }

        const sourceResponse = (await fetchCompetitorSources(researchId, numericCompetitorId)) as { sources?: unknown[] };
        const evidenceResponse = (await fetchCompetitorEvidence(researchId, numericCompetitorId)) as { evidence?: unknown[] };
        const sourceMap = Object.fromEntries(
          (sourceResponse.sources ?? []).map((source) => {
            const value = source as { id?: number; canonical_url?: string; source_type?: string };
            return [String(value.id), {
              id: String(value.id),
              title: value.canonical_url ?? "Source",
              url: value.canonical_url,
              type: value.source_type ?? "Source",
            }];
          }),
        );
        const evidenceItems = (evidenceResponse.evidence ?? []).map((evidence) => {
          const value = evidence as { id?: number; competitor_research_id?: number; source_id?: number | null; content_excerpt?: string | null; content?: string | null };
          return {
            id: String(value.id),
            findingId: String(value.competitor_research_id ?? numericCompetitorId),
            statementContext: value.content_excerpt ?? value.content ?? "",
            sourceId: value.source_id === null || value.source_id === undefined ? "" : String(value.source_id),
          };
        }).filter((evidence) => evidence.statementContext.length > 0);
        const mapped = mapBackendCompetitorFindings(competitorResearch, competitorId, competitorId);
        mapped.sources = { ...mapped.sources, ...sourceMap };
        mapped.evidence = {
          ...mapped.evidence,
          overview: evidenceItems,
          products: [],
          features: [],
          pricing: [],
          targetAudience: [],
          positioning: [],
          customerFeedback: [],
        };

        if (!isMounted) {
          return;
        }

        setFindings(mapped);
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setFindings(null);
        setErrorMessage(getApiErrorMessage(error, "Competitor research details are unavailable from the backend right now."));
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void loadFindings();

    return () => {
      isMounted = false;
    };
  }, [competitorId, researchId]);

  if (!researchId) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#326FEA]">COMPETITOR RESEARCH</p>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">Research run required</h1>
            <p className="mt-4 text-base leading-7 text-[#52627A]">A live research run is required to inspect competitor findings.</p>
            <Link href="/" className="mt-6 inline-flex h-[52px] items-center justify-center rounded-xl bg-[#326FEA] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25">
              Return to home
            </Link>
          </section>
        </div>
      </main>
    );
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-8 shadow-[0_20px_40px_rgba(16,42,86,0.06)]">
            <p className="text-sm text-[#52627A]">Loading live competitor research details...</p>
          </div>
        </div>
      </main>
    );
  }

  if (!findings) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>
            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">Competitor details unavailable</h1>
            <p className="mt-4 text-base leading-7 text-[#52627A]">
              {errorMessage || `No competitor research is available for ${competitorId} yet.`}
            </p>
            <Link href={`/research/competitors?company=${encodeURIComponent(companyName)}&research_id=${encodeURIComponent(researchId)}`} className="mt-6 inline-flex h-[52px] items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-5 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20">
              Back to competitor list
            </Link>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <section className="overflow-hidden rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] shadow-[0_24px_60px_rgba(16,42,86,0.08)]">
          <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-10 lg:py-14">
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
                AI COMPETITOR RESEARCH
              </div>

              <Link href={`/research/competitors?company=${encodeURIComponent(companyName)}&research_id=${encodeURIComponent(researchId)}`} className="inline-flex h-11 items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-4 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20">
                ← Back to competitors
              </Link>
            </div>

            <header className="mb-8">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#326FEA] sm:text-xs">Competitor profile</p>
              <h1 className="text-3xl font-semibold tracking-[-0.06em] text-[#102A56] sm:text-4xl lg:text-5xl">{findings.competitorName}</h1>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-[#52627A] sm:text-base">
                {findings.overview || "No overview was returned by the backend yet."}
              </p>
            </header>

            <CompetitorResearchFindingsComponent findings={findings} />
          </div>
        </section>
      </div>
    </main>
  );
}

export default function CompetitorDetailsPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-8 shadow-[0_20px_40px_rgba(16,42,86,0.06)]">
              <p className="text-sm text-[#52627A]">Loading competitor analysis...</p>
            </div>
          </div>
        </main>
      }
    >
      <CompetitorDetailsContent />
    </Suspense>
  );
}
