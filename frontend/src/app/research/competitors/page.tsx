"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { CompetitorList } from "@/components/research/CompetitorList";
import type { Competitor } from "@/types/competitor";

const MOCK_COMPETITORS: Record<string, Competitor[]> = {
  notion: [
    {
      id: "slack",
      name: "Slack",
      website: "https://slack.com",
      category: "Team collaboration",
      description: "A workspace for team communication, project coordination, and cross-functional work.",
      discoveryReason: "Overlaps with Notion in the same productivity and collaboration layer for team-based work.",
    },
    {
      id: "asana",
      name: "Asana",
      website: "https://asana.com",
      category: "Project and task management",
      description: "Helps teams plan work, track execution, and manage shared operational workflows.",
      discoveryReason: "Shares a similar product positioning around planning, workflows, and knowledge work coordination.",
    },
    {
      id: "trello",
      name: "Trello",
      website: "https://trello.com",
      category: "Workflow management",
      description: "Provides lightweight boards for organizing tasks, projects, and team work.",
      discoveryReason: "Competes in the broader workspace productivity category where flexible team planning is a central value proposition.",
    },
    {
      id: "coda",
      name: "Coda",
      website: "https://coda.io",
      category: "Docs and workspaces",
      description: "Combines documents, structured data, and workflow tools in a shared workspace.",
      discoveryReason: "Competes with Notion in the document-and-workspace model for teams seeking flexible information systems.",
    },
  ],
};

function CompetitorsContent() {
  const searchParams = useSearchParams();
  const companyQuery = searchParams.get("company")?.trim() ?? "";
  const [isDiscovering, setIsDiscovering] = useState(true);

  const company = companyQuery;
  const normalizedCompany = company.toLowerCase();

  useEffect(() => {
    if (!company) {
      setIsDiscovering(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setIsDiscovering(false);
    }, 800);

    return () => window.clearTimeout(timer);
  }, [company]);

  const competitors = useMemo(() => {
    if (!company) {
      return [] as Competitor[];
    }

    return MOCK_COMPETITORS[normalizedCompany] ?? [];
  }, [company, normalizedCompany]);

  const hasIncompleteDiscovery = competitors.some(
    (competitor) => !competitor.description || !competitor.discoveryReason,
  );

  if (!company) {
    return (
      <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-white/10 bg-[linear-gradient(135deg,rgba(18,24,22,0.98),rgba(16,20,19,0.96))] p-6 sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[var(--paper)]/80 sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-white sm:text-4xl">
              Company information is missing.
            </h1>

            <p className="mt-4 text-base leading-7 text-[var(--muted)]">
              A company name or website URL is required to view competitor discovery.
            </p>

            <Link
              href="/"
              className="mt-6 inline-flex h-[52px] items-center justify-center rounded-xl bg-[var(--coral)] px-5 text-sm font-semibold text-[var(--ink)] transition hover:-translate-y-0.5 hover:bg-[#ff937c] focus:outline-none focus:ring-2 focus:ring-[var(--coral)]/45"
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

          <Link href={`/research/company?company=${encodeURIComponent(company)}`} className="text-sm font-medium text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]">
            ← Company Understanding
          </Link>
        </header>

        <section className="overflow-hidden rounded-[32px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] shadow-[0_24px_60px_rgba(19,48,95,0.06)]">
          <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <div className="mb-6 flex flex-wrap gap-2">
              {[
                { label: "Company", complete: true },
                { label: "Understanding", complete: true },
                { label: "Competitors", complete: true, active: true },
                { label: "Research", complete: false },
                { label: "Report", complete: false },
              ].map((item) => (
                <div
                  key={item.label}
                  className={[
                    "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.16em]",
                    item.complete
                      ? "border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[var(--primary-blue)]"
                      : item.active
                        ? "border-[var(--primary-blue)] bg-[var(--primary-blue)] text-white"
                        : "border-[var(--light-border)] bg-white text-[var(--secondary-text)]",
                  ].join(" ")}
                >
                  <span>{item.complete ? "✓" : item.active ? "●" : "○"}</span>
                  {item.label}
                </div>
              ))}
            </div>

            <header className="mb-8">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)] sm:text-xs">
                Competitor Discovery
              </p>
              <h1 className="text-3xl font-semibold tracking-[-0.06em] text-[var(--primary-navy)] sm:text-4xl lg:text-[3rem]">
                Competitors identified for {company}
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                Our research process surfaced companies that may compete with {company} in the same category, based on product overlap and market positioning.
              </p>
            </header>

            {isDiscovering ? (
              <div className="rounded-[24px] border border-[var(--light-border)] bg-[var(--white)] p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-6">
                <div className="flex items-center gap-3">
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[var(--primary-blue)] border-t-transparent" aria-hidden="true" />
                  <p className="text-base font-medium text-[var(--primary-navy)]">Discovering competitors...</p>
                </div>
              </div>
            ) : competitors.length === 0 ? (
              <div className="rounded-[24px] border border-[var(--light-border)] bg-[var(--white)] p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-6">
                <p className="text-lg font-medium text-[var(--primary-navy)]">No relevant competitors were identified.</p>
                <p className="mt-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                  This frontend-only mock experience did not identify any relevant competitors for {company}.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {hasIncompleteDiscovery && (
                  <div className="rounded-[20px] border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-4 text-sm leading-6 text-[var(--secondary-text)]">
                    Some discovery details may be limited in this mock workflow, but the relevant competitors are still shown below.
                  </div>
                )}

                <CompetitorList competitors={competitors} companyName={company} />
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
        <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-white/10 bg-[linear-gradient(135deg,rgba(18,24,22,0.98),rgba(16,20,19,0.96))] p-8">
              <p className="text-sm text-[var(--muted)]">Loading competitor discovery...</p>
            </div>
          </div>
        </main>
      }
    >
      <CompetitorsContent />
    </Suspense>
  );
}
