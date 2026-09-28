"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo } from "react";
import type { ResearchReport } from "@/types/report";

const MOCK_REPORTS: Record<string, ResearchReport> = {
  notion: {
    company: {
      name: "Notion",
      overview:
        "Frontend mock research brief for a productivity platform that blends notes, documents, databases, and collaboration in one workspace. The company is positioned as a flexible operating system for teams managing knowledge and recurring work.",
      industry: "Productivity and collaboration",
      products: [
        { name: "Workspace", summary: "Shared notes, wikis, docs, and team knowledge." },
        { name: "Databases", summary: "Project tracking and lightweight operations." },
      ],
      audience: [
        { label: "Knowledge workers", description: "Individual planning and personal projects." },
        { label: "Operations teams", description: "Cross-functional coordination and documentation." },
      ],
      context: [
        { label: "Positioning", description: "Flexible operating system for work." },
        { label: "Use case", description: "Knowledge work and team coordination." },
      ],
    },
    executiveSummary:
      "This frontend-only mock summary positions Notion as a flexible workspace product for teams managing documentation, planning, and structured work in a single interface.",
    competitors: [
      { id: "slack", name: "Slack", summary: "Communication-focused collaboration platform." },
      { id: "asana", name: "Asana", summary: "Task and project coordination platform." },
      { id: "coda", name: "Coda", summary: "Document-and-workflow hybrid platform." },
    ],
    comparison: [
      {
        category: "Products",
        targetCompany: "Notion",
        competitors: [
          { name: "Slack", value: "Messaging and channel-based workflow communication." },
          { name: "Asana", value: "Task and project execution planning." },
          { name: "Coda", value: "Hybrid docs and structured workflow platform." },
        ],
      },
    ],
    findings: {
      products: {
        title: "Products",
        findings: [
          {
            competitorName: "Slack",
            value: "Messaging-first collaboration workspace.",
            evidence: [],
          },
          {
            competitorName: "Asana",
            value: "Task management for project execution.",
            evidence: [],
          },
          {
            competitorName: "Coda",
            value: "Document-database hybrid for structured work.",
            evidence: [],
          },
        ],
      },
      features: {
        title: "Features",
        findings: [
          {
            competitorName: "Slack",
            value: "Channel-based communication and integrations.",
            evidence: [],
          },
          {
            competitorName: "Asana",
            value: "Timeline views and task coordination.",
            evidence: [],
          },
          {
            competitorName: "Coda",
            value: "Document structure blended with automation.",
            evidence: [],
          },
        ],
      },
      pricing: {
        title: "Pricing",
        findings: [
          {
            competitorName: "Slack",
            value: "Tiered collaboration and enterprise plan model.",
            evidence: [],
          },
          {
            competitorName: "Asana",
            value: "Subscription tiers for team coordination workflows.",
            evidence: [],
          },
          {
            competitorName: "Coda",
            value: "Usage-based expansion and team collaboration pricing.",
            evidence: [],
          },
        ],
      },
      targetAudience: {
        title: "Target Audience",
        findings: [
          {
            competitorName: "Slack",
            value: "Teams primarily focused on communication and coordination.",
            evidence: [],
          },
          {
            competitorName: "Asana",
            value: "Operations leaders and project execution teams.",
            evidence: [],
          },
          {
            competitorName: "Coda",
            value: "Cross-functional teams needing docs plus workflows.",
            evidence: [],
          },
        ],
      },
      customerFeedback: {
        title: "Customer Feedback",
        findings: [
          {
            competitorName: "Slack",
            value: "Strong communication ergonomics and team workflows.",
            evidence: [],
          },
          {
            competitorName: "Asana",
            value: "High clarity for task visibility and ownership.",
            evidence: [],
          },
          {
            competitorName: "Coda",
            value: "Strong satisfaction for customizable workspaces.",
            evidence: [],
          },
        ],
      },
    },
    aiInsights: [
      {
        title: "Workspace convergence",
        summary: "Notion sits at the intersection of docs, planning, and flexible collaboration patterns.",
        kind: "analysis",
      },
    ],
    evidence: [],
    sources: {
      "mock-source-1": {
        id: "mock-source-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/notion",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
    },
  },
};

function getReport(company: string): ResearchReport | null {
  const normalizedCompany = company.trim().toLowerCase();

  if (!normalizedCompany) {
    return null;
  }

  return MOCK_REPORTS[normalizedCompany] ?? null;
}

function ReportContent() {
  const searchParams = useSearchParams();
  const company = searchParams.get("company")?.trim() ?? "";

  const report = useMemo(() => getReport(company), [company]);

  if (!company) {
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

  if (!report) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-6 shadow-[0_20px_40px_rgba(16,42,86,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[#DCE6F5] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[#326FEA] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              Mock report unavailable
            </h1>

            <p className="mt-4 text-base leading-7 text-[#52627A]">
              No mock report is configured for {company}. This page is a frontend-only demonstration of the report experience.
            </p>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/"
                className="inline-flex h-[52px] items-center justify-center rounded-xl bg-[#326FEA] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25"
              >
                Return to home
              </Link>
              <Link
                href={`/research/company?company=${encodeURIComponent(company)}`}
                className="inline-flex h-[52px] items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-5 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20"
              >
                Back to company understanding
              </Link>
            </div>
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
                This report is a frontend-only mock summary designed to demonstrate the report experience for the current research flow.
              </p>
            </header>

            <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Link
                href={`/research/progress?company=${encodeURIComponent(company)}`}
                className="inline-flex h-11 items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-4 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20"
              >
                Back to research progress
              </Link>

              <Link
                href={`/research/company?company=${encodeURIComponent(company)}`}
                className="inline-flex h-11 items-center justify-center rounded-xl border border-[#DCE6F5] bg-white px-4 text-sm font-medium text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20"
              >
                Back to company understanding
              </Link>
            </div>

            <div className="space-y-5">
              <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Overview</h2>
                <p className="text-sm leading-7 text-[#52627A] sm:text-base">{report.company.overview}</p>
              </section>

              <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Products</h2>
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {report.findings.products.findings.map((item) => (
                    <li key={`${item.competitorName}-${item.value}`} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      {item.value}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Features</h2>
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {report.findings.features.findings.map((item) => (
                    <li key={`${item.competitorName}-${item.value}`} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      {item.value}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Pricing</h2>
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {report.findings.pricing.findings.map((item) => (
                    <li key={`${item.competitorName}-${item.value}`} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      {item.value}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Target Audience</h2>
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {report.findings.targetAudience.findings.map((item) => (
                    <li key={`${item.competitorName}-${item.value}`} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      {item.value}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Customer Feedback</h2>
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {report.findings.customerFeedback.findings.map((item) => (
                    <li key={`${item.competitorName}-${item.value}`} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      {item.value}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-[24px] border border-[#DCE6F5] bg-[#F3F7FF] p-4 sm:p-5 lg:p-6">
                <h2 className="mb-4 text-xl font-semibold text-[#102A56]">Sources</h2>
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {Object.values(report.sources).map((source) => (
                    <li key={source.id} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      {source.title}
                    </li>
                  ))}
                </ul>
              </section>
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
