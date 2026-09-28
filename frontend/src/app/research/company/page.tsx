"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CompanyInfoSection } from "@/components/research/CompanyInfoSection";
import { CompanyOverview } from "@/components/research/CompanyOverview";
import type { CompanyProfile } from "@/types/company";

const MOCK_COMPANY_PROFILES: Record<string, CompanyProfile> = {
  notion: {
    name: "Notion",
    overview:
      "Notion is a productivity platform that brings notes, documents, databases, and collaboration into a single workspace. It is positioned as a flexible system for teams that want to manage knowledge, tasks, and workflows in one place.",
    industry: "Productivity software and knowledge management",
    products: [
      {
        name: "Workspace",
        summary: "A central environment for notes, docs, projects, and shared collaboration.",
      },
      {
        name: "Databases",
        summary: "Structured data views that support lightweight project and operational workflows.",
      },
      {
        name: "AI features",
        summary: "Built-in AI tools that help teams draft, summarize, and organize information.",
      },
    ],
    audience: [
      {
        label: "Knowledge workers",
        description: "Individuals and teams managing projects, documentation, and recurring operational work.",
      },
      {
        label: "Product and operations teams",
        description: "Teams that want a flexible operating layer for planning, tracking, and documentation.",
      },
    ],
    context: [
      {
        label: "Business model",
        description: "The company monetizes subscriptions for individuals and organizations, with emphasis on product breadth and retention.",
      },
      {
        label: "Market position",
        description: "It competes in a broad workspace and productivity category where flexibility and integrations matter as much as feature depth.",
      },
    ],
  },
};

function CompanyContent() {
  const searchParams = useSearchParams();
  const companyQuery = searchParams.get("company")?.trim() ?? "";

  if (!companyQuery) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <header className="mb-6 flex items-center justify-between rounded-full border border-[#DCE6F5] bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(16,42,86,0.04)] backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#EAF2FF] bg-[#F3F7FF] text-[10px] font-semibold text-[#326FEA]">
                AI
              </div>
              <span className="text-sm font-semibold tracking-[0.16em] text-[#102A56] uppercase">
                AI Competitor Research
              </span>
            </div>
            <Link href="/" className="text-sm font-medium text-[#52627A] transition hover:text-[#326FEA]">
              Back to Home
            </Link>
          </header>

          <section className="rounded-[28px] border border-[#DCE6F5] bg-white p-6 shadow-[0_18px_34px_rgba(16,42,86,0.04)] sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#326FEA]">
              COMPANY UNDERSTANDING
            </p>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              Which company should we research?
            </h1>
            <p className="mt-4 text-base leading-7 text-[#52627A]">
              A company name or website URL is required to view the company understanding page.
            </p>

            <Link
              href="/"
              className="mt-6 inline-flex h-[52px] items-center justify-center rounded-2xl bg-[#326FEA] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25"
            >
              Return to home
            </Link>
          </section>
        </div>
      </main>
    );
  }

  const normalizedCompany = companyQuery.toLowerCase();
  const company = MOCK_COMPANY_PROFILES[normalizedCompany] ?? null;

  if (!company) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <header className="mb-6 flex items-center justify-between rounded-full border border-[#DCE6F5] bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(16,42,86,0.04)] backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#EAF2FF] bg-[#F3F7FF] text-[10px] font-semibold text-[#326FEA]">
                AI
              </div>
              <span className="text-sm font-semibold tracking-[0.16em] text-[#102A56] uppercase">
                AI Competitor Research
              </span>
            </div>
            <Link href="/" className="text-sm font-medium text-[#52627A] transition hover:text-[#326FEA]">
              Back to Home
            </Link>
          </header>

          <section className="rounded-[28px] border border-[#DCE6F5] bg-white p-6 shadow-[0_18px_34px_rgba(16,42,86,0.04)] sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#326FEA]">
              COMPANY UNDERSTANDING
            </p>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">
              Company profile unavailable
            </h1>
            <p className="mt-4 text-base leading-7 text-[#52627A]">
              No mock company profile is available for {companyQuery}. This page is intentionally limited to frontend demonstration data.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/"
                className="inline-flex h-[52px] items-center justify-center rounded-2xl bg-[#326FEA] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25"
              >
                Return to home
              </Link>
              <Link
                href={`/research/progress?company=${encodeURIComponent(companyQuery)}`}
                className="inline-flex h-[52px] items-center justify-center rounded-2xl border border-[#DCE6F5] bg-white px-5 text-sm font-semibold text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20"
              >
                ← Back to Research Progress
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }

  const initials = company.name.slice(0, 2).toUpperCase();

  return (
    <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex items-center justify-between rounded-full border border-[#DCE6F5] bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(16,42,86,0.04)] backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#EAF2FF] bg-[#F3F7FF] text-[10px] font-semibold text-[#326FEA]">
              AI
            </div>
            <span className="text-sm font-semibold tracking-[0.16em] text-[#102A56] uppercase">
              AI Competitor Research
            </span>
          </div>

          <div className="hidden items-center gap-4 sm:flex">
            <Link href={`/research/progress?company=${encodeURIComponent(companyQuery)}`} className="text-sm font-medium text-[#52627A] transition hover:text-[#326FEA]">
              ← Research Progress
            </Link>
          </div>
        </header>

        <section className="overflow-hidden rounded-[32px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] shadow-[0_24px_60px_rgba(16,42,86,0.08)]">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#326FEA]">
                  Company Understanding
                </p>
                <h1 className="mt-3 break-words text-3xl font-semibold tracking-[-0.06em] text-[#102A56] sm:text-4xl lg:text-[3rem]">
                  {company.name}
                </h1>
                <p className="mt-4 max-w-xl text-base leading-7 text-[#52627A]">
                  {company.overview}
                </p>

                <div className="mt-6 flex flex-wrap gap-3">
                  <span className="rounded-full border border-[#DCE6F5] bg-white px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#52627A]">
                    {company.industry}
                  </span>
                  <span className="rounded-full border border-[#EAF2FF] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#326FEA]">
                    Research foundation
                  </span>
                </div>
              </div>

              <div className="rounded-[28px] border border-[#DCE6F5] bg-white p-5 shadow-[0_18px_36px_rgba(16,42,86,0.04)] sm:p-6">
                <div className="flex items-center justify-between gap-3 pb-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-[#EAF2FF] bg-[#F3F7FF] text-2xl font-semibold text-[#326FEA]">
                    {initials}
                  </div>
                  <span className="rounded-full border border-[#EAF2FF] bg-[#F3F7FF] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#326FEA]">
                    Company profile
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="rounded-2xl border border-[#DCE6F5] bg-[#F3F7FF] p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#52627A]">Company</p>
                    <p className="mt-2 text-base font-semibold text-[#102A56]">{company.name}</p>
                  </div>
                  <div className="rounded-2xl border border-[#DCE6F5] bg-white p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#52627A]">Industry</p>
                    <p className="mt-2 text-sm text-[#102A56]">{company.industry}</p>
                  </div>
                  <div className="rounded-2xl border border-[#DCE6F5] bg-white p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#52627A]">Understanding</p>
                    <p className="mt-2 text-sm text-[#102A56]">Business model, market position, and audience fit</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="mt-8 space-y-6">
          <CompanyOverview company={company} />

          <div className="grid gap-6 lg:grid-cols-2">
            <CompanyInfoSection title="Products & Offerings">
              <div className="space-y-3">
                {company.products.map((product) => (
                  <div key={product.name} className="group rounded-[20px] border border-[#DCE6F5] bg-white p-4 transition hover:-translate-y-0.5 hover:border-[#326FEA]/35 hover:bg-[#F3F7FF]">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#EAF2FF] text-[10px] font-semibold uppercase tracking-[0.18em] text-[#326FEA]">
                        {product.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-base font-semibold text-[#102A56]">{product.name}</p>
                        <p className="mt-1 text-sm leading-6 text-[#52627A]">{product.summary}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CompanyInfoSection>

            <CompanyInfoSection title="Business Context">
              <div className="space-y-3">
                {company.context.map((item) => (
                  <div key={item.label} className="rounded-[20px] border border-[#DCE6F5] bg-white p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#326FEA]">{item.label}</p>
                    <p className="mt-2 text-sm leading-6 text-[#52627A]">{item.description}</p>
                  </div>
                ))}
              </div>
            </CompanyInfoSection>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <CompanyInfoSection title="Target Audience">
              <div className="grid gap-3 sm:grid-cols-2">
                {company.audience.map((audience) => (
                  <div key={audience.label} className="rounded-[20px] border border-[#DCE6F5] bg-[#F3F7FF] p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#326FEA]">{audience.label}</p>
                    <p className="mt-2 text-sm leading-6 text-[#52627A]">{audience.description}</p>
                  </div>
                ))}
              </div>
            </CompanyInfoSection>

            <CompanyInfoSection title="Why this matters for competitor research">
              <div className="rounded-[22px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-4">
                <div className="flex flex-col gap-3">
                  {[
                    "Company",
                    "Products",
                    "Audience",
                    "Market context",
                    "Competitors",
                  ].map((step, index) => (
                    <div key={step} className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#EAF2FF] text-[10px] font-semibold text-[#326FEA]">
                        {index + 1}
                      </div>
                      <span className="text-sm font-medium text-[#102A56]">{step}</span>
                      {index < 4 && <span className="text-[#326FEA]" aria-hidden="true">↓</span>}
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-sm leading-6 text-[#52627A]">
                  Understanding the company first gives the competitive research a clear foundation.
                </p>
              </div>
            </CompanyInfoSection>
          </div>

          <div className="rounded-[28px] border border-[#DCE6F5] bg-white p-5 shadow-[0_18px_34px_rgba(16,42,86,0.04)] sm:p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#326FEA]">
              Research Foundation
            </p>
            <p className="mt-3 text-base leading-7 text-[#52627A]">
              Next, we&apos;ll use this company profile to identify relevant competitors and compare them against the current market context.
            </p>

            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <Link
                href={`/research/competitors?company=${encodeURIComponent(companyQuery)}`}
                className="inline-flex h-[52px] items-center justify-center rounded-2xl bg-[#326FEA] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25"
              >
                Discover Competitors →
              </Link>
              <Link
                href={`/research/progress?company=${encodeURIComponent(companyQuery)}`}
                className="inline-flex h-[52px] items-center justify-center rounded-2xl border border-[#DCE6F5] bg-white px-5 text-sm font-semibold text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20"
              >
                ← Research Progress
              </Link>
            </div>
          </div>
        </div>

      </div>
    </main>
  );
}

export default function CompanyPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[#DCE6F5] bg-white p-8 shadow-[0_18px_34px_rgba(16,42,86,0.04)]">
              <p className="text-sm text-[#52627A]">Loading company understanding...</p>
            </div>
          </div>
        </main>
      }
    >
      <CompanyContent />
    </Suspense>
  );
}
