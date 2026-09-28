"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { ResearchStageList } from "@/components/research/ResearchStageList";
import type { ResearchStage, ResearchStatus, ResearchStageStatus } from "@/types/research";

const RESEARCH_STAGE_DEFINITIONS = [
  {
    id: "understanding-company",
    title: "Understanding company",
    description: "Mapping the business, market position, and strategic context.",
  },
  {
    id: "discovering-competitors",
    title: "Discovering competitors",
    description: "Identifying the most relevant competitors in the market.",
  },
  {
    id: "researching-competitors",
    title: "Researching competitors",
    description: "Comparing product positioning, strengths, and strategic differences.",
  },
  {
    id: "collecting-evidence",
    title: "Collecting evidence",
    description: "Gathering public signals and supporting references for the brief.",
  },
  {
    id: "generating-report",
    title: "Generating report",
    description: "Structuring the findings into a concise competitive research summary.",
  },
] as const;

function createInitialStages(): ResearchStage[] {
  return RESEARCH_STAGE_DEFINITIONS.map((stage) => ({
    ...stage,
    status: "pending",
  }));
}

function ResearchProgressContent() {
  const searchParams = useSearchParams();
  const company = searchParams.get("company")?.trim() ?? "";
  const [stageIndex, setStageIndex] = useState(0);
  const [overallState, setOverallState] = useState<ResearchStatus>("queued");
  const [stages, setStages] = useState<ResearchStage[]>(createInitialStages);

  const isMissingCompany = !company;

  useEffect(() => {
    if (isMissingCompany) {
      return;
    }

    if (stageIndex >= RESEARCH_STAGE_DEFINITIONS.length) {
      setOverallState("completed");
      setStages((currentStages) =>
        currentStages.map((stage) => ({ ...stage, status: "completed" })),
      );
      return;
    }

    const nextStages = RESEARCH_STAGE_DEFINITIONS.map((definition, index) => {
      const stageStatus: ResearchStageStatus =
        index < stageIndex ? "completed" : index === stageIndex ? "running" : "pending";

      return {
        ...definition,
        status: stageStatus,
      };
    });

    setStages(nextStages);
    setOverallState(stageIndex === 0 ? "queued" : "running");
  }, [isMissingCompany, stageIndex]);

  useEffect(() => {
    if (isMissingCompany || stageIndex >= RESEARCH_STAGE_DEFINITIONS.length) {
      return;
    }

    const timer = window.setTimeout(() => {
      setStageIndex((currentStageIndex) => currentStageIndex + 1);
    }, 1400);

    return () => window.clearTimeout(timer);
  }, [isMissingCompany, stageIndex]);

  const currentStage =
    stageIndex < RESEARCH_STAGE_DEFINITIONS.length
      ? RESEARCH_STAGE_DEFINITIONS[stageIndex]
      : RESEARCH_STAGE_DEFINITIONS[RESEARCH_STAGE_DEFINITIONS.length - 1];

  const stateMessage = useMemo(() => {
    if (isMissingCompany) {
      return "No company was provided for this research run.";
    }

    if (overallState === "queued") {
      return "Research queued and ready to begin.";
    }

    if (overallState === "running") {
      return "Research in progress...";
    }

    if (overallState === "completed") {
      return "Research complete and ready for review.";
    }

    if (overallState === "partial") {
      return "Research partially complete.";
    }

    return "Research failed. Please retry.";
  }, [isMissingCompany, overallState]);

  if (isMissingCompany) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              No company was provided for this research run.
            </h1>

            <p className="mt-4 text-base leading-7 text-[#52627A]">
              Start with a company name or website URL to launch a new competitive research workflow.
            </p>

            <Link
              href="/"
              className="mt-6 inline-flex h-[52px] items-center justify-center rounded-xl bg-[#326FEA] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/30"
            >
              Return to home
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
          <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10 lg:px-10 lg:py-14">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <header className="mb-8">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#326FEA] sm:text-xs">
                Research workflow
              </p>
              <h1 className="max-w-[12ch] text-3xl font-semibold leading-[1] tracking-[-0.06em] text-[#102A56] sm:text-4xl lg:text-5xl">
                Researching {company}
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[#52627A] sm:text-base">
                Your research workflow is being prepared using public information and supporting evidence.
              </p>
            </header>

            <div className="space-y-4 rounded-[24px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 sm:p-5 lg:p-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--foreground-secondary)]">
                    Overall state
                  </p>
                  <p aria-live="polite" className="mt-2 text-base font-medium text-[var(--foreground)]">
                    {stateMessage}
                  </p>
                </div>

                <Link
                  href="/"
                  className="inline-flex h-11 items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-4 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#102A56] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25"
                >
                  Start another company
                </Link>
              </div>

              <ResearchStageList stages={stages} />
            </div>

            <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 text-sm text-[var(--foreground-secondary)] sm:p-5">
              <p className="font-medium text-[var(--foreground)]">Current stage</p>
              <p className="mt-2 text-base text-[var(--foreground)]">{currentStage.title}</p>
              <p className="mt-1 leading-6 text-[var(--foreground-secondary)]">{currentStage.description}</p>
            </div>

            <div className="mt-8 flex justify-center">
              <Link
                href={`/research/report?company=${encodeURIComponent(company)}`}
                aria-label="View Company Research Report"
                className="inline-flex h-[52px] items-center justify-center rounded-xl bg-[#326FEA] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/30"
              >
                View Company Research Report
              </Link>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export default function ResearchProgressPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-8 shadow-[0_20px_40px_rgba(16,42,86,0.06)]">
              <p className="text-sm text-[#52627A]">Loading research workflow...</p>
            </div>
          </div>
        </main>
      }
    >
      <ResearchProgressContent />
    </Suspense>
  );
}
