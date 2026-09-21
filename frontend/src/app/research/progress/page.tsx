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
    description: "Building the foundation of the research and market context.",
  },
  {
    id: "discovering-competitors",
    title: "Discovering competitors",
    description: "Finding the companies that matter in the same market.",
  },
  {
    id: "researching-competitors",
    title: "Researching competitors",
    description: "Comparing products, pricing, positioning and customer signals.",
  },
  {
    id: "collecting-evidence",
    title: "Collecting evidence",
    description: "Connecting each finding to relevant public sources and support.",
  },
  {
    id: "generating-report",
    title: "Generating report",
    description: "Turning the research into a structured, decision-ready brief.",
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

  const nextStage =
    stageIndex < RESEARCH_STAGE_DEFINITIONS.length - 1
      ? RESEARCH_STAGE_DEFINITIONS[stageIndex + 1]
      : null;

  const stateMessage = useMemo(() => {
    if (isMissingCompany) {
      return "No company was provided for this research run.";
    }

    if (overallState === "queued") {
      return "Research queued and ready to begin.";
    }

    if (overallState === "running") {
      return "Research in progress.";
    }

    if (overallState === "completed") {
      return "Research complete and ready for review.";
    }

    if (overallState === "partial") {
      return "Some information was unavailable, but the research is moving forward.";
    }

    return "Something interrupted this research step. We can try again.";
  }, [isMissingCompany, overallState]);

  if (isMissingCompany) {
    return (
      <main className="min-h-screen bg-[var(--background)] text-[var(--primary-navy)]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <header className="mb-6 flex items-center justify-between rounded-full border border-[var(--light-border)] bg-[rgba(255,255,255,0.75)] px-4 py-3 shadow-[0_10px_24px_rgba(19,48,95,0.04)] backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[10px] font-semibold text-[var(--primary-blue)]">
                AI
              </div>
              <span className="text-sm font-semibold tracking-[0.16em] text-[var(--primary-navy)] uppercase">
                AI Competitor Research
              </span>
            </div>
            <Link href="/" className="text-sm font-medium text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]">
              Back to Home
            </Link>
          </header>

          <section className="rounded-[28px] border border-[var(--light-border)] bg-[var(--white)] p-6 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
              RESEARCHING COMPANY
            </p>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-4xl">
              Which company should we research?
            </h1>
            <p className="mt-4 text-base leading-7 text-[var(--secondary-text)]">
              Start with a company name or website URL to launch a new competitive research workflow.
            </p>

            <Link
              href="/"
              className="mt-6 inline-flex h-[52px] items-center justify-center rounded-2xl bg-[var(--primary-blue)] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/25"
            >
              Return to home
            </Link>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--primary-navy)]">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex items-center justify-between rounded-full border border-[var(--light-border)] bg-[rgba(255,255,255,0.75)] px-4 py-3 shadow-[0_10px_24px_rgba(19,48,95,0.04)] backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[10px] font-semibold text-[var(--primary-blue)]">
              AI
            </div>
            <span className="text-sm font-semibold tracking-[0.16em] text-[var(--primary-navy)] uppercase">
              AI Competitor Research
            </span>
          </div>

          <Link href="/" className="text-sm font-medium text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]">
            Back to Home
          </Link>
        </header>

        <section className="overflow-hidden rounded-[32px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] shadow-[0_24px_60px_rgba(19,48,95,0.06)]">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <div className="mb-8 flex items-center justify-between gap-4 border-b border-[var(--light-border)] pb-5">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
                  Researching Company
                </p>
                <h1 className="mt-3 text-3xl font-semibold tracking-[-0.06em] text-[var(--primary-navy)] sm:text-4xl lg:text-[3rem]">
                  {company}
                </h1>
              </div>

              <div className="inline-flex items-center gap-2 rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                <span className="inline-flex h-2.5 w-2.5 animate-pulse rounded-full bg-[var(--primary-blue)]" aria-hidden="true" />
                Research in progress
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.18fr_0.82fr] lg:items-start">
              <div className="rounded-[28px] border border-[var(--light-border)] bg-[var(--white)] p-5 shadow-[0_18px_36px_rgba(19,48,95,0.04)] sm:p-6">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--primary-blue)]">
                    Current Stage
                  </p>
                  <span className="inline-flex items-center gap-2 rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-[var(--primary-blue)]" aria-hidden="true" />
                    In progress
                  </span>
                </div>

                <h2 className="mt-4 text-2xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-3xl">
                  {currentStage.title}
                </h2>

                <p className="mt-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                  {currentStage.description}
                </p>

                <div className="mt-5 rounded-[22px] border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--secondary-text)]">
                      Next
                    </p>
                    <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                      {nextStage ? "Next step" : "Ready to review"}
                    </span>
                  </div>
                  <p className="mt-3 text-base font-medium text-[var(--primary-navy)]">
                    {nextStage ? `Researching ${nextStage.title.toLowerCase()}` : "Preparing your research report"}
                  </p>
                </div>

                <div className="mt-5 rounded-[22px] border border-[var(--light-border)] bg-[white] p-4">
                  <div className="flex items-center gap-3 text-sm text-[var(--secondary-text)]">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--soft-blue)] text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                      AI
                    </span>
                    <p className="leading-6">
                      We&apos;re building a structured view of this company and its competitive landscape.
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap gap-3">
                  <Link
                    href={`/research/company?company=${encodeURIComponent(company)}`}
                    className="inline-flex h-[52px] items-center justify-center rounded-2xl bg-[var(--primary-blue)] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/25"
                  >
                    Understand Company →
                  </Link>
                </div>
              </div>

              <div className="rounded-[28px] border border-[var(--light-border)] bg-[var(--white)] p-5 shadow-[0_18px_36px_rgba(19,48,95,0.04)] sm:p-6">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--secondary-text)]">
                    Research journey
                  </p>
                  <span className="rounded-full bg-[var(--secondary-light-blue)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                    Guided
                  </span>
                </div>

                <div className="relative mx-auto max-w-[340px] rounded-[24px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#F7FAFF_0%,#EEF5FF_100%)] p-5">
                  <div className="absolute left-1/2 top-3 h-[calc(100%-1.5rem)] w-px -translate-x-1/2 bg-[linear-gradient(180deg,rgba(50,111,234,0.15),rgba(50,111,234,0.55))]" aria-hidden="true" />

                  <div className="relative flex flex-col items-center gap-5">
                    {[
                      { label: "Company", tone: "bg-[var(--white)] text-[var(--primary-navy)]" },
                      { label: "Understanding", tone: "bg-[var(--secondary-light-blue)] text-[var(--primary-blue)]" },
                      { label: "Competitors", tone: "bg-[var(--soft-blue)] text-[var(--primary-navy)]" },
                      { label: "Research", tone: "bg-[var(--very-soft-blue)] text-[var(--primary-navy)]" },
                      { label: "Evidence", tone: "bg-[var(--soft-cyan)] text-[var(--primary-navy)]" },
                      { label: "Insights", tone: "bg-[var(--white)] text-[var(--primary-navy)]" },
                    ].map((item, index) => (
                      <div key={item.label} className="relative z-10 flex w-full items-center justify-center">
                        <div className={`flex h-12 min-w-[112px] items-center justify-center rounded-2xl border border-[var(--light-border)] px-3 text-center text-[10px] font-semibold uppercase tracking-[0.16em] sm:text-[11px] ${item.tone}`}>
                          {item.label}
                        </div>
                        {index < 5 && <div className="absolute left-1/2 top-full mt-1 h-5 w-px -translate-x-1/2 bg-[var(--primary-blue)]/25" aria-hidden="true" />}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-5 rounded-[20px] border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-4 text-sm leading-6 text-[var(--secondary-text)]">
                  Research can take a little time. We&apos;re gathering information from multiple sources and organizing it into a structured research report.
                </div>
              </div>
            </div>

            <div className="mt-8 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
                  Research stage details
                </p>
                <span className="text-[11px] text-[var(--secondary-text)]">{stages.filter((stage) => stage.status === "completed").length}/{stages.length} stages complete</span>
              </div>

              <ResearchStageList stages={stages} />
            </div>

            <div className="mt-8 rounded-[24px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] p-4 text-sm leading-7 text-[var(--secondary-text)] sm:p-5">
              <p className="font-medium text-[var(--primary-navy)]">Supportive note</p>
              <p className="mt-2">
                Some information may be unavailable or incomplete. We&apos;ll show what we found and where it came from so the final output stays evidence-first.
              </p>
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
        <main className="min-h-screen bg-[var(--background)] text-[var(--primary-navy)]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[var(--light-border)] bg-[white] p-8 shadow-[0_18px_34px_rgba(19,48,95,0.04)]">
              <p className="text-sm text-[var(--secondary-text)]">Loading research workflow...</p>
            </div>
          </div>
        </main>
      }
    >
      <ResearchProgressContent />
    </Suspense>
  );
}
