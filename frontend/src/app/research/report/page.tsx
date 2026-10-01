"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ReportAIInsights } from "@/components/research/ReportAIInsights";
import { ReportCompetitorComparison } from "@/components/research/ReportCompetitorComparison";
import { ReportExecutiveSummary } from "@/components/research/ReportExecutiveSummary";
import { getApiErrorMessage, getReport, listReports, mapBackendReportToResearchReport } from "@/lib/api";
import type { ResearchReport } from "@/types/report";

function ReportContent() {
  const searchParams = useSearchParams();
  const company = searchParams.get("company")?.trim() ?? "";
  const researchId = searchParams.get("research_id")?.trim() ?? "";
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(researchId));
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!researchId) {
      setReport(null);
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    const loadReport = async () => {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const reportList = await listReports(researchId);

        if (reportList.length > 0) {
          const latest = reportList[reportList.length - 1];
          const reportId = latest.id !== undefined ? String(latest.id) : "latest";
          const response = await getReport(researchId, reportId).catch(() => latest);

          if (!isMounted) {
            return;
          }

          const mapped = mapBackendReportToResearchReport(response, {
            name: company || "Company",
            overview: "",
            industry: "",
            products: [],
            audience: [],
            context: [],
          });

          setReport(mapped);
          return;
        }

        setReport(null);
        setErrorMessage("The backend has not generated a report for this research run yet. Please return to the progress screen and wait for the workflow to finish.");
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setReport(null);
        setErrorMessage(getApiErrorMessage(error, "The backend report is not available yet."));
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void loadReport();

    return () => {
      isMounted = false;
    };
  }, [company, researchId]);

  if (!company && !researchId) {
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
              A company name or website URL is required to view the company research report.
            </p>

            <Link href="/" className="mt-6 inline-flex h-[52px] items-center justify-center rounded-xl bg-[#326FEA] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25">
              Return to home
            </Link>
          </section>
        </div>
      </main>
    );
  }

  if (!researchId) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>
            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              Research run required
            </h1>
            <p className="mt-4 text-base leading-7 text-[#52627A]">
              Start a research run from the homepage to generate a report.
            </p>
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
            <p className="text-sm text-[#52627A]">Loading company research report from the backend...</p>
          </div>
        </div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              Report not ready
            </h1>

            <p className="mt-4 text-base leading-7 text-[#52627A]">
              {errorMessage || "The backend does not have a completed report for this research run yet."}
            </p>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link href={`/research/progress?company=${encodeURIComponent(company)}&research_id=${encodeURIComponent(researchId)}`} className="inline-flex h-[52px] items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-5 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20">
                Back to research progress
              </Link>
              <Link href="/" className="inline-flex h-[52px] items-center justify-center rounded-xl bg-[#326FEA] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25">
                Return to home
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }

  const findingGroups = [
    { title: "Products", items: report.findings.products.findings },
    { title: "Features", items: report.findings.features.findings },
    { title: "Pricing", items: report.findings.pricing.findings },
    { title: "Target Audience", items: report.findings.targetAudience.findings },
    { title: "Customer Feedback", items: report.findings.customerFeedback.findings },
  ];

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
                Company Research Report
              </p>
              <h1 className="text-3xl font-semibold tracking-[-0.06em] text-[#102A56] sm:text-4xl lg:text-5xl">
                {report.company.name}
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[#52627A] sm:text-base">
                This report reflects the live backend result for the current research run.
              </p>
            </header>

            <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Link href={`/research/progress?company=${encodeURIComponent(company || report.company.name)}&research_id=${encodeURIComponent(researchId)}`} className="inline-flex h-11 items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-4 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20">
                Back to research progress
              </Link>
              <Link href={`/research/company?company=${encodeURIComponent(company || report.company.name)}&research_id=${encodeURIComponent(researchId)}`} className="inline-flex h-11 items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-4 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20">
                Back to company understanding
              </Link>
            </div>

            <div className="space-y-5">
              <ReportExecutiveSummary report={report} />
              <ReportCompetitorComparison comparison={report.comparison} />
              <ReportAIInsights insights={report.aiInsights} />

              {findingGroups.map((group) =>
                group.items.length > 0 ? (
                  <section key={group.title} className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                    <h2 className="mb-4 text-xl font-semibold text-[#102A56]">{group.title}</h2>
                    <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                      {group.items.map((item) => (
                        <li key={`${group.title}-${item.competitorName}-${item.value}`} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                          {item.value}
                        </li>
                      ))}
                    </ul>
                  </section>
                ) : null,
              )}

              {Object.keys(report.sources).length > 0 ? (
                <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                  <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Sources</h2>
                  <div className="space-y-3">
                    {Object.values(report.sources).map((source) => (
                      <div key={source.id} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                        <div className="font-medium text-[#102A56]">{source.title}</div>
                        {source.url ? (
                          <a href={source.url} target="_blank" rel="noreferrer" className="mt-2 block text-sm text-[#326FEA] underline break-all">
                            {source.url}
                          </a>
                        ) : null}
                        {source.publisher ? <p className="mt-2 text-sm text-[#52627A]">{source.publisher}</p> : null}
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export default function ReportPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-8 shadow-[0_20px_40px_rgba(16,42,86,0.06)]">
              <p className="text-sm text-[#52627A]">Loading company research report...</p>
            </div>
          </div>
        </main>
      }
    >
      <ReportContent />
    </Suspense>
  );
}
