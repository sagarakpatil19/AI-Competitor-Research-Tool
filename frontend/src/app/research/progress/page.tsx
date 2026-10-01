"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { ResearchStageList } from "@/components/research/ResearchStageList";
import {
  createReport,
  discoverCompetitors,
  getApiErrorMessage,
  getResearchRun,
  listReports,
  mapBackendCompetitors,
  pollBackgroundOperation,
  researchCompetitors,
  resolveResearchRun,
  submitAIAnalysis,
  understandCompany,
} from "@/lib/api";
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
    id: "reviewing-evidence",
    title: "Reviewing evidence",
    description: "Reviewing backend-registered sources and evidence on competitor detail pages.",
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

function preserveManualEvidenceStage(stages: ResearchStage[]): ResearchStage[] {
  return stages.map((stage) => (stage.id === "reviewing-evidence" ? { ...stage, status: "pending" } : stage));
}

function stageStatusForApiStatus(apiStatus: string): ResearchStage[] {
  const normalized = apiStatus.toLowerCase();

  if (normalized === "completed") {
    return preserveManualEvidenceStage(RESEARCH_STAGE_DEFINITIONS.map((stage) => ({ ...stage, status: "completed" })));
  }

  if (normalized === "failed") {
    return preserveManualEvidenceStage(RESEARCH_STAGE_DEFINITIONS.map((stage, index) => ({
      ...stage,
      status: index === RESEARCH_STAGE_DEFINITIONS.length - 1 ? "failed" : index < RESEARCH_STAGE_DEFINITIONS.length - 1 ? "completed" : "pending",
    })));
  }

  if (normalized === "running" || normalized === "retrying" || normalized === "researching" || normalized === "analyzing") {
    return preserveManualEvidenceStage(RESEARCH_STAGE_DEFINITIONS.map((stage, index) => ({
      ...stage,
      status: index === 0 ? "completed" : index === 1 ? "running" : "pending",
    })));
  }

  if (normalized === "resolving") {
    return preserveManualEvidenceStage(RESEARCH_STAGE_DEFINITIONS.map((stage, index) => ({ ...stage, status: index === 0 ? "running" : "pending" })));
  }

  if (normalized === "discovering") {
    return preserveManualEvidenceStage(RESEARCH_STAGE_DEFINITIONS.map((stage, index) => ({ ...stage, status: index === 0 ? "completed" : index === 1 ? "running" : "pending" })));
  }

  return preserveManualEvidenceStage(RESEARCH_STAGE_DEFINITIONS.map((stage, index) => ({
    ...stage,
    status: index === 0 ? "running" : "pending",
  })));
}

function normalizeApiStatus(apiStatus: string | undefined): ResearchStatus {
  const normalized = (apiStatus ?? "queued").toLowerCase();

  if (normalized === "completed") {
    return "completed";
  }

  if (normalized === "failed") {
    return "failed";
  }

  if (normalized === "running" || normalized === "retrying") {
    return "running";
  }

  if (normalized === "queued" || normalized === "submitted") {
    return "queued";
  }

  if (["resolving", "discovering", "validating", "researching", "analyzing"].includes(normalized)) {
    return "running";
  }

  return "partial";
}

function ResearchProgressContent() {
  const searchParams = useSearchParams();
  const company = searchParams.get("company")?.trim() ?? "";
  const researchId = searchParams.get("research_id")?.trim() ?? "";
  const [overallState, setOverallState] = useState<ResearchStatus>("queued");
  const [stages, setStages] = useState<ResearchStage[]>(createInitialStages);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(Boolean(researchId));

  useEffect(() => {
    if (!researchId) {
      setIsLoading(false);
      setOverallState("queued");
      setStages(createInitialStages());
      return;
    }

    let isMounted = true;

    const loadResearchState = async () => {
      setIsLoading(true);
      setErrorMessage("");

      try {
        let run = await getResearchRun(researchId);

        if (run.status === "submitted") {
          run = await resolveResearchRun(researchId);
        }

        await understandCompany(researchId);
        setStages(stageStatusForApiStatus("resolving"));

        const discoveryOperation = await discoverCompetitors(researchId);
        const discoveryResult = await pollBackgroundOperation(discoveryOperation.status_url, 120000, 2000);
        const competitors = mapBackendCompetitors(discoveryResult.result ?? []);
        const competitorIds = competitors.map((competitor) => Number(competitor.id)).filter((id) => Number.isInteger(id) && id > 0);

        if (competitorIds.length === 0) {
          throw new Error("The backend completed competitor discovery without returning valid competitor IDs.");
        }

        const researchOperation = await researchCompetitors(researchId, competitorIds);
        const researchResult = await pollBackgroundOperation(researchOperation.status_url, 120000, 2000);
        const researchItems = ((researchResult.result ?? {}) as { competitor_research?: Array<{ id?: number }> }).competitor_research ?? [];
        const competitorResearchIds = researchItems.map((item) => item.id).filter((id): id is number => typeof id === "number" && id > 0);

        if (competitorResearchIds.length === 0) {
          throw new Error("The backend completed competitor research without returning research record IDs.");
        }

        const analysisOperation = await submitAIAnalysis(researchId, {
          scope: "research_run",
          competitor_research_ids: competitorResearchIds,
        });
        const analysisResult = await pollBackgroundOperation(analysisOperation.status_url, 120000, 2000);
        const analysisId = Number((analysisResult.result as { id?: number } | null)?.id);

        if (!Number.isInteger(analysisId) || analysisId <= 0) {
          throw new Error("The completed AI analysis did not return a valid analysis ID for report generation.");
        }

        const reports = await listReports(researchId);
        const currentReport = reports.find((report) => report.analysis_id === analysisId);

        if (!currentReport) {
          await createReport(researchId, analysisId);
        }

        run = await getResearchRun(researchId);
        const resolvedStatus = run.status;

        if (!isMounted) {
          return;
        }

        setOverallState(normalizeApiStatus(resolvedStatus));
        setStages(stageStatusForApiStatus(resolvedStatus));
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setOverallState("failed");
        setStages(stageStatusForApiStatus("failed"));
        setErrorMessage(getApiErrorMessage(error, "Unable to load the current research state from the backend."));
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void loadResearchState();

    return () => {
      isMounted = false;
    };
  }, [researchId]);

  const currentStage =
    overallState === "completed"
      ? RESEARCH_STAGE_DEFINITIONS[RESEARCH_STAGE_DEFINITIONS.length - 1]
      : overallState === "failed"
        ? RESEARCH_STAGE_DEFINITIONS[RESEARCH_STAGE_DEFINITIONS.length - 1]
        : RESEARCH_STAGE_DEFINITIONS[0];

  const stateMessage = useMemo(() => {
    if (!researchId) {
      return "No active research run is available.";
    }

    if (errorMessage) {
      return errorMessage;
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

    if (overallState === "failed") {
      return "The research operation failed. Please review the backend status or retry.";
    }

    return "Research is in progress.";
  }, [errorMessage, overallState, researchId]);

  if (!researchId) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              No active research run was supplied.
            </h1>

            <p className="mt-4 text-base leading-7 text-[#52627A]">
              Start a new company research run from the home page to continue the workflow.
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
                Researching {company || "your company"}
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[#52627A] sm:text-base">
                The status below reflects the live backend lifecycle for this research run.
              </p>
            </header>

            <div className="space-y-4 rounded-[24px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 sm:p-5 lg:p-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--foreground-secondary)]">
                    Overall state
                  </p>
                  <p aria-live="polite" className="mt-2 text-base font-medium text-[var(--foreground)]">
                    {isLoading ? "Loading live backend state..." : stateMessage}
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
                href={`/research/report?company=${encodeURIComponent(company || "")}&research_id=${encodeURIComponent(researchId)}`}
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
