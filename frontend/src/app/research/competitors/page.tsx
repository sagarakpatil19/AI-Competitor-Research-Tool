"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { CompetitorList } from "@/components/research/CompetitorList";
import type { Competitor } from "@/types/competitor";
import { discoverCompetitors, getApiErrorMessage, mapBackendCompetitors, pollBackgroundOperation, researchCompetitors } from "@/lib/api";

function CompetitorsContent() {
  const searchParams = useSearchParams();
  const companyQuery = searchParams.get("company")?.trim() ?? "";
  const researchId = searchParams.get("research_id")?.trim() ?? "";
  const [isDiscovering, setIsDiscovering] = useState(Boolean(researchId));
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!researchId) {
      setIsDiscovering(false);
      setCompetitors([]);
      return;
    }

    let isMounted = true;

    const loadCompetitors = async () => {
      setIsDiscovering(true);
      setErrorMessage("");

      try {
        const operation = await discoverCompetitors(researchId);
        const finishedOperation = await pollBackgroundOperation(operation.status_url, 120000, 2000);
        const mapped = mapBackendCompetitors(finishedOperation.result ?? []);

        if (mapped.length === 0) {
          throw new Error("The backend completed competitor discovery without returning any competitors.");
        }

        const competitorIds = mapped.map((competitor) => Number(competitor.id)).filter((id) => Number.isInteger(id) && id > 0);

        if (competitorIds.length !== mapped.length) {
          throw new Error("The backend returned a competitor without a valid numeric ID.");
        }

        const researchOperation = await researchCompetitors(researchId, competitorIds);
        await pollBackgroundOperation(researchOperation.status_url, 120000, 2000);

        if (!isMounted) {
          return;
        }

        setCompetitors(mapped);
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setCompetitors([]);
        setErrorMessage(getApiErrorMessage(error, "Competitor discovery is unavailable from the backend right now."));
      } finally {
        if (isMounted) {
          setIsDiscovering(false);
        }
      }
    };

    void loadCompetitors();

    return () => {
      isMounted = false;
    };
  }, [researchId]);

  if (!companyQuery && !researchId) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              Company information is missing.
            </h1>

            <p className="mt-4 text-base leading-7 text-[#52627A]">
              A company name or website URL is required to view competitor discovery.
            </p>

            <Link
              href="/"
              className="mt-6 inline-flex h-[52px] items-center justify-center rounded-xl bg-[#326FEA] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25"
            >
              Return to home
            </Link>
          </section>
        </div>
      </main>
    );
  }

  const hasIncompleteDiscovery = competitors.some(
    (competitor) => !competitor.description || !competitor.discoveryReason,
  );

  return (
    <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <section className="overflow-hidden rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] shadow-[0_24px_60px_rgba(16,42,86,0.08)]">
          <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-10 lg:py-14">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <header className="mb-8">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#326FEA] sm:text-xs">
                Competitor Discovery
              </p>
              <h1 className="text-3xl font-semibold tracking-[-0.06em] text-[#102A56] sm:text-4xl lg:text-5xl">
                Companies identified as potential competitors for {companyQuery || "your company"}.
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[#52627A] sm:text-base">
                This research step identifies companies that may compete with the researched company based on product and market positioning.
              </p>
            </header>

            <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Link
                href={`/research/company?company=${encodeURIComponent(companyQuery)}&research_id=${encodeURIComponent(researchId)}`}
                className="inline-flex h-11 items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-4 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20"
              >
                Back to company understanding
              </Link>

              <Link
                href="/"
                className="inline-flex h-11 items-center justify-center rounded-xl bg-[#326FEA] px-4 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25"
              >
                Return to home
              </Link>
            </div>

            {errorMessage ? (
              <div className="rounded-[20px] border border-[#F4D5D7] bg-[#FFF6F6] p-4 text-sm leading-6 text-[#7A2F2F]">
                {errorMessage}
              </div>
            ) : null}

            {isDiscovering ? (
              <div className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-5 sm:p-6">
                <div className="flex items-center gap-3">
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[#326FEA] border-t-transparent" aria-hidden="true" />
                  <p className="text-base font-medium text-[#102A56]">Discovering competitors from the backend...</p>
                </div>
              </div>
            ) : competitors.length === 0 ? (
              <div className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-5 sm:p-6">
                <p className="text-lg font-medium text-[#102A56]">No relevant competitors were identified.</p>
                <p className="mt-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  The backend did not return any relevant competitors for {companyQuery || "this run"}.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {hasIncompleteDiscovery && (
                  <div className="rounded-[20px] border border-[#DCE6F5] bg-[#EAF2FF] p-4 text-sm leading-6 text-[#52627A]">
                    Some discovery fields may be incomplete in the backend result.
                  </div>
                )}

                <CompetitorList competitors={competitors} companyName={companyQuery || "Company"} researchId={researchId} />
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

export default function CompetitorsPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-8 shadow-[0_20px_40px_rgba(16,42,86,0.06)]">
              <p className="text-sm text-[#52627A]">Loading competitor discovery...</p>
            </div>
          </div>
        </main>
      }
    >
      <CompetitorsContent />
    </Suspense>
  );
}
