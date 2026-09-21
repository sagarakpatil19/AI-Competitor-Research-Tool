"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { CompetitorResearchFindingsComponent } from "@/components/research/CompetitorResearchFindings";
import type { CompetitorResearchFindings } from "@/types/competitor-findings";

const MOCK_COMPETITOR_FINDINGS: Record<string, CompetitorResearchFindings> = {
  slack: {
    competitorId: "slack",
    competitorName: "Slack",
    overview:
      "Slack is a team communication platform that organizes work around channels, direct messages, and shared collaboration. It is positioned as a communication layer that helps teams coordinate conversations, routines, and operational updates.",
    products: [
      "Channels — organized team conversations for shared work and updates.",
      "Huddles and meetings — lightweight collaboration for live conversations and decision making.",
      "Workflow integrations — tools that connect messaging with project and operational tools.",
    ],
    features: [
      "Real-time messaging that supports structured decision making across teams.",
      "Threaded conversations that help keep context attached to specific work items.",
      "Custom workflows and integration patterns for distributed teams.",
    ],
    pricing: [
      "Mock placeholder pricing: a free tier for basic collaboration use cases.",
      "Mock placeholder pricing: paid tiers intended for larger teams and more advanced administration.",
      "Mock placeholder pricing: the app is intentionally not using verified current pricing data.",
    ],
    targetAudience: [
      "Knowledge workers and team leads managing daily communication.",
      "Cross-functional teams that coordinate projects and operational updates.",
      "Organizations with distributed contributors relying on rapid collaboration patterns.",
    ],
    positioning: [
      "Slack sits in the team collaboration and coordination layer rather than the document-centric workspace layer.",
      "It competes most directly with communication-first and workflow coordination tools in the same productivity category.",
    ],
    customerFeedback: [
      "Mock feedback note: users often value channel organization and rapid communication.",
      "Mock feedback note: team adoption is often strongest when communication and operational workflows are tightly connected.",
      "Mock feedback note: the tool can become noisy for organizations with high message volume.",
    ],
    evidence: {
      overview: [
        {
          id: "slack-overview-evidence-1",
          findingId: "overview",
          statementContext: "Mock supporting context demonstrating how an evidence record sits beneath a research finding.",
          sourceId: "slack-source-overview-1",
        },
      ],
      products: [
        {
          id: "slack-products-evidence-1",
          findingId: "products",
          statementContext: "Mock supporting context showing how product-level findings can be traced to a source record.",
          sourceId: "slack-source-product-1",
        },
      ],
      features: [
        {
          id: "slack-features-evidence-1",
          findingId: "features",
          statementContext: "Mock supporting context showing that feature-level statements can be accompanied by supporting source metadata.",
          sourceId: "slack-source-feature-1",
        },
      ],
      pricing: [
        {
          id: "slack-pricing-evidence-1",
          findingId: "pricing",
          statementContext: "Mock supporting context for the pricing section to demonstrate the evidence layer without implying verified pricing facts.",
          sourceId: "slack-source-pricing-1",
        },
      ],
      targetAudience: [
        {
          id: "slack-target-audience-evidence-1",
          findingId: "targetAudience",
          statementContext: "Mock supporting context for audience interpretation used only to demonstrate the target-audience evidence pattern.",
          sourceId: "slack-source-audience-1",
        },
      ],
      positioning: [
        {
          id: "slack-positioning-evidence-1",
          findingId: "positioning",
          statementContext: "Mock supporting context illustrating how positioning statements can remain distinct from the underlying source record.",
          sourceId: "slack-source-positioning-1",
        },
      ],
      customerFeedback: [
        {
          id: "slack-feedback-evidence-1",
          findingId: "customerFeedback",
          statementContext: "Mock supporting context showing where customer feedback themes can later attach to evidence and source references.",
          sourceId: "slack-source-feedback-1",
        },
      ],
    },
    sources: {
      "slack-source-overview-1": {
        id: "slack-source-overview-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/slack-overview",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "slack-source-product-1": {
        id: "slack-source-product-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/slack-products",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "slack-source-feature-1": {
        id: "slack-source-feature-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/slack-features",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "slack-source-pricing-1": {
        id: "slack-source-pricing-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/slack-pricing",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "slack-source-audience-1": {
        id: "slack-source-audience-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/slack-audience",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "slack-source-positioning-1": {
        id: "slack-source-positioning-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/slack-positioning",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "slack-source-feedback-1": {
        id: "slack-source-feedback-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/slack-feedback",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
    },
  },
  asana: {
    competitorId: "asana",
    competitorName: "Asana",
    overview:
      "Asana is a work management platform designed to help teams plan, assign, and track execution across projects and recurring operational work. It is positioned as a structured project coordination tool for teams that need clarity and accountability.",
    products: [
      "Project planning — structured views for plans, deadlines, and tasks.",
      "Work tracking — project execution monitoring across ownership and progress.",
      "Team coordination — shared operational workflows for recurring work.",
    ],
    features: [
      "Task management and workflow coordination across teams.",
      "Project planning views designed to make work visible and accountable.",
      "Operational tracking for execution across multi-step work streams.",
    ],
    pricing: [
      "Mock placeholder pricing: a free plan for small-team or lightweight project management.",
      "Mock placeholder pricing: paid tiers for team work, reporting, and operational scale.",
      "Mock placeholder pricing: this section remains a UI demonstration only.",
    ],
    targetAudience: [
      "Operations teams and project managers organizing work.",
      "Cross-functional groups that need visible execution plans and accountability.",
      "Organizations balancing team coordination with project visibility.",
    ],
    positioning: [
      "Asana focuses on structured execution and work management rather than a broad knowledge workspace.",
      "It often competes in the same workflow planning layer as other collaboration and task management tools.",
    ],
    customerFeedback: [
      "Mock feedback note: users often value clarity around ownership and workflow visibility.",
      "Mock feedback note: teams appreciate the structured planning model for recurring work.",
      "Mock feedback note: some teams may want more flexibility for unstructured knowledge work.",
    ],
    evidence: {
      overview: [
        {
          id: "asana-overview-evidence-1",
          findingId: "overview",
          statementContext: "Mock supporting context illustrating how Asana overview claims can be linked to a specific evidence record.",
          sourceId: "asana-source-overview-1",
        },
      ],
      products: [
        {
          id: "asana-products-evidence-1",
          findingId: "products",
          statementContext: "Mock supporting context showing that product-level findings may require supporting references in a later data model.",
          sourceId: "asana-source-products-1",
        },
      ],
      features: [
        {
          id: "asana-features-evidence-1",
          findingId: "features",
          statementContext: "Mock supporting context for feature-level findings to demonstrate the evidence layer in the details view.",
          sourceId: "asana-source-features-1",
        },
      ],
      pricing: [
        {
          id: "asana-pricing-evidence-1",
          findingId: "pricing",
          statementContext: "Mock supporting context showing pricing evidence in the current frontend-only UI without claiming real pricing verification.",
          sourceId: "asana-source-pricing-1",
        },
      ],
      targetAudience: [
        {
          id: "asana-target-audience-evidence-1",
          findingId: "targetAudience",
          statementContext: "Mock supporting context for target-audience interpretation used strictly for the phase-7 frontend architecture demo.",
          sourceId: "asana-source-target-audience-1",
        },
      ],
      positioning: [
        {
          id: "asana-positioning-evidence-1",
          findingId: "positioning",
          statementContext: "Mock supporting context illustrating how positioning statements can be connected to source material without collapsing the distinction.",
          sourceId: "asana-source-positioning-1",
        },
      ],
      customerFeedback: [
        {
          id: "asana-feedback-evidence-1",
          findingId: "customerFeedback",
          statementContext: "Mock supporting context showing where customer feedback themes can later be tied to a source and associated metadata.",
          sourceId: "asana-source-feedback-1",
        },
      ],
    },
    sources: {
      "asana-source-overview-1": {
        id: "asana-source-overview-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/asana-overview",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "asana-source-products-1": {
        id: "asana-source-products-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/asana-products",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "asana-source-features-1": {
        id: "asana-source-features-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/asana-features",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "asana-source-pricing-1": {
        id: "asana-source-pricing-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/asana-pricing",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "asana-source-target-audience-1": {
        id: "asana-source-target-audience-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/asana-audience",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "asana-source-positioning-1": {
        id: "asana-source-positioning-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/asana-positioning",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "asana-source-feedback-1": {
        id: "asana-source-feedback-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/asana-feedback",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
    },
  },
  trello: {
    competitorId: "trello",
    competitorName: "Trello",
    overview:
      "Trello is a lightweight work management tool built around boards, cards, and visual task tracking. It is positioned as a flexible solution for teams that want simple status visibility and movement through work flows.",
    products: [
      "Board-based task management — simple visual tracking of work items.",
      "Card workflows — lightweight task and status movement across project stages.",
      "Collaboration support — shared planning and update visibility for smaller teams.",
    ],
    features: [
      "Simple board-based visual workflows for planning and progress.",
      "Card structures that support fast updates and lightweight project tracking.",
      "A low-friction coordination model suited to simpler team work.",
    ],
    pricing: [
      "Mock placeholder pricing: free tier for smaller groups or basic usage.",
      "Mock placeholder pricing: paid plans for expanded collaboration, integrations, and admin features.",
      "Mock placeholder pricing: this section is intentionally not verified current pricing data.",
    ],
    targetAudience: [
      "Small and medium teams seeking lightweight workflow management.",
      "People who prefer simple visual work tracking over deeper structured systems.",
      "Organizations with straightforward coordination needs across tasks and milestones.",
    ],
    positioning: [
      "Trello competes in the visual workflow and team coordination layer where simplified boards are valuable.",
      "It is often compared with tools that balance lightweight coordination and basic operational visibility.",
    ],
    customerFeedback: [
      "Mock feedback note: users often appreciate the simplicity and clarity of the board model.",
      "Mock feedback note: teams like the ease of setup and visual status tracking.",
      "Mock feedback note: some teams eventually need more structure or data depth as work grows.",
    ],
    evidence: {
      overview: [
        {
          id: "trello-overview-evidence-1",
          findingId: "overview",
          statementContext: "Mock supporting context showing how Trello overview claims can remain distinct from source metadata.",
          sourceId: "trello-source-overview-1",
        },
      ],
      products: [
        {
          id: "trello-products-evidence-1",
          findingId: "products",
          statementContext: "Mock supporting context to demonstrate a product finding with associated source metadata.",
          sourceId: "trello-source-products-1",
        },
      ],
      features: [
        {
          id: "trello-features-evidence-1",
          findingId: "features",
          statementContext: "Mock supporting context for Trello feature-level findings in the phase-7 evidence layout.",
          sourceId: "trello-source-features-1",
        },
      ],
      pricing: [
        {
          id: "trello-pricing-evidence-1",
          findingId: "pricing",
          statementContext: "Mock supporting context for pricing interpretation that avoids implying verified pricing data.",
          sourceId: "trello-source-pricing-1",
        },
      ],
      targetAudience: [
        {
          id: "trello-target-audience-evidence-1",
          findingId: "targetAudience",
          statementContext: "Mock supporting context for target-audience framing in the current frontend-only dataset.",
          sourceId: "trello-source-target-audience-1",
        },
      ],
      positioning: [
        {
          id: "trello-positioning-evidence-1",
          findingId: "positioning",
          statementContext: "Mock supporting context showing how positioning notes can coexist with source references without collapsing the distinction.",
          sourceId: "trello-source-positioning-1",
        },
      ],
      customerFeedback: [
        {
          id: "trello-feedback-evidence-1",
          findingId: "customerFeedback",
          statementContext: "Mock supporting context for customer feedback themes while preserving the separation between findings and sources.",
          sourceId: "trello-source-feedback-1",
        },
      ],
    },
    sources: {
      "trello-source-overview-1": {
        id: "trello-source-overview-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/trello-overview",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "trello-source-products-1": {
        id: "trello-source-products-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/trello-products",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "trello-source-features-1": {
        id: "trello-source-features-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/trello-features",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "trello-source-pricing-1": {
        id: "trello-source-pricing-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/trello-pricing",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "trello-source-target-audience-1": {
        id: "trello-source-target-audience-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/trello-audience",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "trello-source-positioning-1": {
        id: "trello-source-positioning-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/trello-positioning",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "trello-source-feedback-1": {
        id: "trello-source-feedback-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/trello-feedback",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
    },
  },
  coda: {
    competitorId: "coda",
    competitorName: "Coda",
    overview:
      "Coda blends documents, structured data, and workflow logic into a shared workspace. It is positioned as a flexible collaborative environment that combines documentation with lightweight operational capabilities.",
    products: [
      "Connected docs — shared documents with embedded structured data.",
      "Workspaces — collaborative environments for operational coordination.",
      "Automated workflows — built-in logic to streamline recurring processes and actions.",
    ],
    features: [
      "Document-driven collaboration with structured data capabilities.",
      "Workflow support that connects content and process within one interface.",
      "Customizable workspace patterns for knowledge and operational work.",
    ],
    pricing: [
      "Mock placeholder pricing: free or base plan for simple document collaboration.",
      "Mock placeholder pricing: paid plans for larger teams and more advanced workspace functionality.",
      "Mock placeholder pricing: this section is a mock demonstration only.",
    ],
    targetAudience: [
      "Teams that want documentation and operational workflows in one place.",
      "Cross-functional teams working across knowledge, planning, and process coordination.",
      "Organizations that value flexibility over rigid workflow tools.",
    ],
    positioning: [
      "Coda competes in the blended documents-and-workflows layer, overlapping with knowledge work and flexible productivity systems.",
      "It is closest to products that combine structured content and collaboration rather than simple task tracking alone.",
    ],
    customerFeedback: [
      "Mock feedback note: users like the flexibility to shape the workspace around their process.",
      "Mock feedback note: teams appreciate the mix of docs and operational structure.",
      "Mock feedback note: customization can impose a learning curve for new users.",
    ],
    evidence: {
      overview: [
        {
          id: "coda-overview-evidence-1",
          findingId: "overview",
          statementContext: "Mock supporting context showing how evidence can sit beneath a broad overview statement without mixing the concepts together.",
          sourceId: "coda-source-overview-1",
        },
      ],
      products: [
        {
          id: "coda-products-evidence-1",
          findingId: "products",
          statementContext: "Mock supporting context to demonstrate evidence under the products section in the current mock workflow.",
          sourceId: "coda-source-products-1",
        },
      ],
      features: [
        {
          id: "coda-features-evidence-1",
          findingId: "features",
          statementContext: "Mock supporting context for feature-level findings and their associated support references.",
          sourceId: "coda-source-features-1",
        },
      ],
      pricing: [
        {
          id: "coda-pricing-evidence-1",
          findingId: "pricing",
          statementContext: "Mock supporting context showing that pricing information is kept separate from a verified source layer in this design.",
          sourceId: "coda-source-pricing-1",
        },
      ],
      targetAudience: [
        {
          id: "coda-target-audience-evidence-1",
          findingId: "targetAudience",
          statementContext: "Mock supporting context illustrating the target-audience evidence pattern in the competitor findings experience.",
          sourceId: "coda-source-target-audience-1",
        },
      ],
      positioning: [
        {
          id: "coda-positioning-evidence-1",
          findingId: "positioning",
          statementContext: "Mock supporting context for the positioning section to show a clean claim-to-evidence-to-source chain.",
          sourceId: "coda-source-positioning-1",
        },
      ],
      customerFeedback: [
        {
          id: "coda-feedback-evidence-1",
          findingId: "customerFeedback",
          statementContext: "Mock supporting context for customer feedback themes, presented purely as a demonstration of the evidence architecture.",
          sourceId: "coda-source-feedback-1",
        },
      ],
    },
    sources: {
      "coda-source-overview-1": {
        id: "coda-source-overview-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/coda-overview",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "coda-source-products-1": {
        id: "coda-source-products-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/coda-products",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "coda-source-features-1": {
        id: "coda-source-features-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/coda-features",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "coda-source-pricing-1": {
        id: "coda-source-pricing-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/coda-pricing",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "coda-source-target-audience-1": {
        id: "coda-source-target-audience-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/coda-audience",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "coda-source-positioning-1": {
        id: "coda-source-positioning-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/coda-positioning",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
      "coda-source-feedback-1": {
        id: "coda-source-feedback-1",
        title: "Mock source",
        type: "Placeholder",
        url: "mock://placeholder-source/coda-feedback",
        publisher: "Frontend demo dataset",
        accessedAt: "Mock date",
      },
    },
  },
};

function CompetitorResearchPageContent() {
  const params = useParams<{ competitor?: string }>();
  const searchParams = useSearchParams();
  const companyQuery = searchParams.get("company")?.trim() ?? "";
  const [isResearching, setIsResearching] = useState(true);

  const competitorKey = useMemo(() => {
    const value = params?.competitor ?? "";
    return decodeURIComponent(value).trim().toLowerCase();
  }, [params]);

  useEffect(() => {
    if (!companyQuery || !competitorKey) {
      setIsResearching(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setIsResearching(false);
    }, 700);

    return () => window.clearTimeout(timer);
  }, [companyQuery, competitorKey]);

  const findings = MOCK_COMPETITOR_FINDINGS[competitorKey] ?? null;

  const hasPartialFindings =
    !findings ||
    findings.products.length === 0 ||
    findings.features.length === 0 ||
    findings.targetAudience.length === 0 ||
    findings.customerFeedback.length === 0;

  if (!companyQuery) {
    return (
      <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] p-6 shadow-[0_24px_60px_rgba(19,48,95,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[var(--primary-blue)] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-4xl">
              Company information is missing.
            </h1>

            <p className="mt-4 text-base leading-7 text-[var(--secondary-text)]">
              A company name or website URL is required to view competitor research findings.
            </p>

            <Link
              href="/"
              className="mt-6 inline-flex h-[52px] items-center justify-center rounded-xl bg-[var(--primary-blue)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/30"
            >
              Return to home
            </Link>
          </section>
        </div>
      </main>
    );
  }

  if (!competitorKey || !findings) {
    return (
      <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] p-6 shadow-[0_24px_60px_rgba(19,48,95,0.06)] sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[var(--primary-blue)] sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-4xl">
              Competitor information is missing.
            </h1>

            <p className="mt-4 text-base leading-7 text-[var(--secondary-text)]">
              No competitor findings were available for this route in the current frontend mock dataset.
            </p>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link
                href={`/research/competitors?company=${encodeURIComponent(companyQuery)}`}
                className="inline-flex h-[52px] items-center justify-center rounded-xl bg-[var(--primary-blue)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/30"
              >
                Back to competitor discovery
              </Link>
              <Link
                href="/"
                className="inline-flex h-[52px] items-center justify-center rounded-xl border border-[var(--light-border)] bg-white px-5 text-sm font-medium text-[var(--primary-navy)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/20"
              >
                Return to home
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex items-center justify-between rounded-full border border-[var(--light-border)] bg-[rgba(255,255,255,0.75)] px-4 py-3 shadow-[0_10px_24px_rgba(19,48,95,0.04)] backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[10px] font-semibold text-[var(--primary-blue)]">
              AI
            </div>
            <span className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--primary-navy)]">
              AI Competitor Research
            </span>
          </div>

          <Link
            href={`/research/competitors?company=${encodeURIComponent(companyQuery)}`}
            className="text-sm font-medium text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]"
          >
            ← Competitor Discovery
          </Link>
        </header>

        <section className="overflow-hidden rounded-[32px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] shadow-[0_24px_60px_rgba(19,48,95,0.06)]">
          <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <div className="mb-6 flex flex-wrap gap-2">
              {[
                { label: "Company", complete: true },
                { label: "Understanding", complete: true },
                { label: "Competitors", complete: true },
                { label: "Research", complete: true, active: true },
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
                Research
              </p>
              <h1 className="text-3xl font-semibold tracking-[-0.06em] text-[var(--primary-navy)] sm:text-4xl lg:text-[3rem]">
                Competitor Research
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                What we learned about {findings.competitorName} and the strengths, positioning, and expectations that shape its role in the market.
              </p>
            </header>

            {isResearching ? (
              <div className="rounded-[24px] border border-[var(--light-border)] bg-white p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-6">
                <div className="flex items-center gap-3">
                  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[var(--primary-blue)] border-t-transparent" aria-hidden="true" />
                  <p className="text-base font-medium text-[var(--primary-navy)]">Researching competitor findings...</p>
                </div>
              </div>
            ) : hasPartialFindings ? (
              <div className="rounded-[24px] border border-[var(--light-border)] bg-white p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-6">
                <p className="text-lg font-medium text-[var(--primary-navy)]">Some research details may be incomplete.</p>
                <p className="mt-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                  We have partial findings for {findings.competitorName}, but not every section is fully populated in this mock experience.
                </p>
              </div>
            ) : findings.products.length === 0 ? (
              <div className="rounded-[24px] border border-[var(--light-border)] bg-white p-5 shadow-[0_18px_34px_rgba(19,48,95,0.04)] sm:p-6">
                <p className="text-lg font-medium text-[var(--primary-navy)]">No research findings were identified.</p>
                <p className="mt-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                  There is no research data available for {findings.competitorName} in the current mock dataset.
                </p>
              </div>
            ) : (
              <>
                <div className="mb-6 rounded-[22px] border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-4 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                  <span className="font-semibold text-[var(--primary-navy)]">{findings.competitorName}:</span> a focused summary of what the research surfaced about the competitor and how it compares in the current market context.
                </div>

                <CompetitorResearchFindingsComponent findings={findings} />

                <div className="mt-8 flex justify-center">
                  <Link
                    href={`/research/report?company=${encodeURIComponent(companyQuery)}`}
                    aria-label="View Final Research Report"
                    className="inline-flex h-[52px] items-center justify-center rounded-xl bg-[var(--primary-blue)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/30"
                  >
                    View Final Report →
                  </Link>
                </div>
              </>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

export default function CompetitorResearchPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] p-8 shadow-[0_24px_60px_rgba(19,48,95,0.06)]">
              <p className="text-sm text-[var(--secondary-text)]">Loading competitor research findings...</p>
            </div>
          </div>
        </main>
      }
    >
      <CompetitorResearchPageContent />
    </Suspense>
  );
}
