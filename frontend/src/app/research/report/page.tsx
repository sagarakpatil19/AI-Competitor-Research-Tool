"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo } from "react";
import { CompanyInfoSection } from "@/components/research/CompanyInfoSection";
import { CompanyOverview } from "@/components/research/CompanyOverview";
import { EvidenceList } from "@/components/research/EvidenceList";
import { ReportAIInsights } from "@/components/research/ReportAIInsights";
import { ReportCompetitorComparison } from "@/components/research/ReportCompetitorComparison";
import { ReportExecutiveSummary } from "@/components/research/ReportExecutiveSummary";
import { ReportSources } from "@/components/research/ReportSources";
import type { CompanyProfile } from "@/types/company";
import type { CompetitorResearchFindings } from "@/types/competitor-findings";
import type { ResearchReport } from "@/types/report";

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

const MOCK_COMPETITOR_FINDINGS: Record<string, CompetitorResearchFindings> = {
  slack: {
    competitorId: "slack",
    competitorName: "Slack",
    overview: "Slack is a communication-first workspace for team coordination and day-to-day work.",
    products: [
      "Channels — organized conversations for team updates and work coordination.",
      "Huddles and meetings — lightweight live collaboration for decision making.",
      "Workflow integrations — tools that connect messaging with operational tooling.",
    ],
    features: [
      "Real-time messaging that supports structured decision making across teams.",
      "Threaded conversations that keep work context attached to specific discussions.",
      "Custom workflows and integration patterns for distributed teams.",
    ],
    pricing: [
      "Mock placeholder pricing: a free tier for basic collaboration use cases.",
      "Mock placeholder pricing: paid tiers intended for larger teams and more advanced administration.",
    ],
    targetAudience: [
      "Knowledge workers and team leads managing daily communication.",
      "Cross-functional teams managing projects and operational updates.",
    ],
    positioning: [
      "Slack operates as a communication layer rather than a document-heavy workspace.",
      "It competes most directly with coordination-first productivity tools.",
    ],
    customerFeedback: [
      "Users often value channel organization and rapid communication.",
      "Teams adopt it most strongly when communication and operational workflows are tightly connected.",
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
  coda: {
    competitorId: "coda",
    competitorName: "Coda",
    overview: "Coda blends documents, structured data, and workflow logic into a shared workspace.",
    products: [
      "Connected docs — shared documents with embedded structured data.",
      "Workspaces — collaborative environments for operational coordination.",
      "Automated workflows — built-in logic for recurring processes and actions.",
    ],
    features: [
      "Document-driven collaboration with structured data capabilities.",
      "Workflow support that connects content and process within one interface.",
      "Customizable workspace patterns for knowledge and operational work.",
    ],
    pricing: [
      "Mock placeholder pricing: free or base plan for simple document collaboration.",
      "Mock placeholder pricing: paid plans for larger teams and more advanced workspace functionality.",
    ],
    targetAudience: [
      "Teams that want documentation and operational workflows in one place.",
      "Cross-functional teams working across knowledge, planning, and process coordination.",
    ],
    positioning: [
      "Coda competes in the blended documents-and-workflows layer.",
      "It sits close to tools that combine structured content and collaboration rather than simple task tracking alone.",
    ],
    customerFeedback: [
      "Users like the flexibility to shape the workspace around their process.",
      "Teams appreciate the mix of docs and operational structure.",
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
  asana: {
    competitorId: "asana",
    competitorName: "Asana",
    overview: "Asana is a work management platform designed to help teams plan, assign, and track execution across projects.",
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
      "Mock placeholder pricing: paid tiers for team work and reporting.",
    ],
    targetAudience: [
      "Operations teams and project managers organizing work.",
      "Cross-functional groups that need visible execution plans and accountability.",
    ],
    positioning: [
      "Asana emphasizes structured execution and work management rather than broad knowledge work.",
      "It often competes in the same workflow planning layer as other collaboration and task management tools.",
    ],
    customerFeedback: [
      "Users often value clarity around ownership and workflow visibility.",
      "Teams appreciate the structured planning model for recurring work.",
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
    overview: "Trello is a lightweight work management tool built around boards, cards, and visual task tracking.",
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
      "Mock placeholder pricing: paid plans for expanded collaboration and admin features.",
    ],
    targetAudience: [
      "Small and medium teams seeking lightweight workflow management.",
      "People who prefer simple visual work tracking over deeper structured systems.",
    ],
    positioning: [
      "Trello competes in the visual workflow and team coordination layer.",
      "It is often compared with tools that balance lightweight coordination and basic operational visibility.",
    ],
    customerFeedback: [
      "Users often appreciate the simplicity and clarity of the board model.",
      "Teams like the ease of setup and visual status tracking.",
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
};

function buildResearchReport(companyName: string): ResearchReport | null {
  const normalizedCompany = companyName.trim().toLowerCase();
  const company = MOCK_COMPANY_PROFILES[normalizedCompany];

  if (!company) {
    return null;
  }

  const competitors = Object.values(MOCK_COMPETITOR_FINDINGS).map((finding) => ({
    id: finding.competitorId,
    name: finding.competitorName,
    summary: finding.overview,
  }));

  const sourceMap = Object.values(MOCK_COMPETITOR_FINDINGS).reduce(
    (accumulator, competitor) => ({ ...accumulator, ...competitor.sources }),
    {} as Record<string, any>,
  );

  const evidence = Object.values(MOCK_COMPETITOR_FINDINGS)
    .flatMap((competitor) => Object.values(competitor.evidence).flat())
    .filter(Boolean);

  const comparison = [
    {
      category: "Products",
      targetCompany: company.products.map((product) => product.name).join(" • "),
      competitors: competitors.map((competitor) => ({
        name: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.products.slice(0, 2).join(" • ") ?? "Mock product summary",
      })),
    },
    {
      category: "Core features",
      targetCompany: company.products.map((product) => product.name).join(" • "),
      competitors: competitors.map((competitor) => ({
        name: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.features.slice(0, 2).join(" • ") ?? "Mock feature summary",
      })),
    },
    {
      category: "Pricing model",
      targetCompany: "Frontend-only mock pricing structure",
      competitors: competitors.map((competitor) => ({
        name: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.pricing.slice(0, 2).join(" • ") ?? "Mock pricing summary",
      })),
    },
    {
      category: "Target audience",
      targetCompany: company.audience.map((segment) => segment.label).join(" • "),
      competitors: competitors.map((competitor) => ({
        name: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.targetAudience.slice(0, 2).join(" • ") ?? "Mock audience summary",
      })),
    },
    {
      category: "Positioning",
      targetCompany: company.context[1]?.description ?? "Flexible work system",
      competitors: competitors.map((competitor) => ({
        name: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.positioning.slice(0, 2).join(" • ") ?? "Mock positioning summary",
      })),
    },
  ];

  const findings = {
    products: {
      title: "Products",
      findings: competitors.map((competitor) => ({
        competitorName: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.products[0] ?? "Mock product finding",
        evidence: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.evidence.products ?? [],
      })),
    },
    features: {
      title: "Features",
      findings: competitors.map((competitor) => ({
        competitorName: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.features[0] ?? "Mock feature finding",
        evidence: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.evidence.features ?? [],
      })),
    },
    pricing: {
      title: "Pricing",
      findings: competitors.map((competitor) => ({
        competitorName: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.pricing[0] ?? "Mock pricing finding",
        evidence: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.evidence.pricing ?? [],
      })),
    },
    targetAudience: {
      title: "Target Audience",
      findings: competitors.map((competitor) => ({
        competitorName: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.targetAudience[0] ?? "Mock audience finding",
        evidence: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.evidence.targetAudience ?? [],
      })),
    },
    customerFeedback: {
      title: "Customer Feedback",
      findings: competitors.map((competitor) => ({
        competitorName: competitor.name,
        value: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.customerFeedback[0] ?? "Mock feedback finding",
        evidence: MOCK_COMPETITOR_FINDINGS[competitor.id.toLowerCase()]?.evidence.customerFeedback ?? [],
      })),
    },
  };

  const aiInsights = [
    {
      title: "Overlapping workspace functionality",
      summary:
        "Mock AI-assisted analysis: Slack, Asana, Coda, and Trello all emphasize collaboration and structured work coordination, while Notion remains positioned as the broader workspace layer for knowledge and operations.",
      kind: "analysis" as const,
    },
    {
      title: "Positioning differences",
      summary:
        "Mock AI-assisted interpretation: Notion appears to emphasize flexibility and documentation-heavy workflows, while the competitor set is more segmented across communication, task execution, and work management patterns.",
      kind: "pattern" as const,
    },
    {
      title: "Audience segmentation",
      summary:
        "Mock AI-assisted interpretation: the competitor set skews toward team coordination, operations, and project execution, while the target company can appeal to both knowledge workers and cross-functional operational teams.",
      kind: "analysis" as const,
    },
  ];

  return {
    company,
    executiveSummary:
      "This frontend-only research preview compares Notion against multiple competitor categories, including communication, task planning, and workspace-driven collaboration tools. The mock analysis highlights how the target company sits at the intersection of knowledge work, documentation, and flexible team operations, while the competitor set emphasizes narrower but deeper segmentation across coordination and execution workflows.",
    competitors,
    comparison,
    findings,
    aiInsights,
    evidence,
    sources: sourceMap,
  };
}

function ReportContent() {
  const searchParams = useSearchParams();
  const companyQuery = searchParams.get("company")?.trim() ?? "";

  const report = useMemo(() => buildResearchReport(companyQuery), [companyQuery]);

  if (!companyQuery) {
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
              A company name or website URL is required to view the final research report.
            </p>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/"
                className="inline-flex h-[52px] items-center justify-center rounded-xl bg-[var(--coral)] px-5 text-sm font-semibold text-[var(--ink)] transition hover:-translate-y-0.5 hover:bg-[#ff937c] focus:outline-none focus:ring-2 focus:ring-[var(--coral)]/45"
              >
                Return to home
              </Link>
              <Link
                href="/research/company"
                className="inline-flex h-[52px] items-center justify-center rounded-xl border border-white/10 bg-white/5 px-5 text-sm font-medium text-[var(--paper)] transition hover:border-[var(--coral)]/50 hover:text-white focus:outline-none focus:ring-2 focus:ring-[var(--coral)]/45"
              >
                Back to company understanding
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-white/10 bg-[linear-gradient(135deg,rgba(18,24,22,0.98),rgba(16,20,19,0.96))] p-6 sm:p-8">
            <div className="mb-6 inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.26em] text-[var(--paper)]/80 sm:text-[11px]">
              AI COMPETITOR RESEARCH
            </div>

            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-white sm:text-4xl">
              Mock report unavailable
            </h1>

            <p className="mt-4 text-base leading-7 text-[var(--muted)]">
              No mock report is configured for {companyQuery}. This page is intentionally limited to frontend demonstration data.
            </p>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/"
                className="inline-flex h-[52px] items-center justify-center rounded-xl bg-[var(--coral)] px-5 text-sm font-semibold text-[var(--ink)] transition hover:-translate-y-0.5 hover:bg-[#ff937c] focus:outline-none focus:ring-2 focus:ring-[var(--coral)]/45"
              >
                Return to home
              </Link>
              <Link
                href={`/research/company?company=${encodeURIComponent(companyQuery)}`}
                className="inline-flex h-[52px] items-center justify-center rounded-xl border border-white/10 bg-white/5 px-5 text-sm font-medium text-[var(--paper)] transition hover:border-[var(--coral)]/50 hover:text-white focus:outline-none focus:ring-2 focus:ring-[var(--coral)]/45"
              >
                Back to company understanding
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }

  const backLink = report.competitors[0]
    ? `/research/competitors/${encodeURIComponent(report.competitors[0].id)}?company=${encodeURIComponent(companyQuery)}`
    : `/research/competitors?company=${encodeURIComponent(companyQuery)}`;

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
            href={backLink}
            className="text-sm font-medium text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]"
          >
            ← Competitor Research
          </Link>
        </header>

        <section className="overflow-hidden rounded-[32px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] shadow-[0_24px_60px_rgba(19,48,95,0.06)]">
          <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <div className="mb-6 flex flex-wrap gap-2">
              {[
                { label: "Company", complete: true },
                { label: "Understanding", complete: true },
                { label: "Competitors", complete: true },
                { label: "Research", complete: true },
                { label: "Evidence", complete: true },
                { label: "Report", complete: true, active: true },
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
                Final Research Report
              </p>
              <h1 className="text-3xl font-semibold tracking-[-0.06em] text-[var(--primary-navy)] sm:text-4xl lg:text-[3rem]">
                {report.company.name}
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--secondary-text)] sm:text-base">
                A concise synthesis of the research findings and supporting evidence collected through the research journey for {companyQuery}.
              </p>
            </header>

            <div className="space-y-5">
              <ReportExecutiveSummary report={report} />

              <section className="rounded-[24px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.82)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
                  Company Overview
                </p>
                <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[var(--primary-navy)]">
                  {report.company.name}
                </h2>
                <div className="mt-5 space-y-5">
                  <CompanyOverview company={report.company} />

                  <CompanyInfoSection title="Industry">
                    <p className="text-sm leading-7 text-[var(--secondary-text)] sm:text-base">{report.company.industry}</p>
                  </CompanyInfoSection>

                  <CompanyInfoSection title="Products">
                    <div className="space-y-3">
                      {report.company.products.map((product) => (
                        <div key={product.name} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-4 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
                          <p className="text-base font-medium text-[var(--primary-navy)]">{product.name}</p>
                          <p className="mt-1 text-sm leading-6 text-[var(--secondary-text)]">{product.summary}</p>
                        </div>
                      ))}
                    </div>
                  </CompanyInfoSection>

                  <CompanyInfoSection title="Target Audience">
                    <div className="space-y-3">
                      {report.company.audience.map((audience) => (
                        <div key={audience.label} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-4 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
                          <p className="text-base font-medium text-[var(--primary-navy)]">{audience.label}</p>
                          <p className="mt-1 text-sm leading-6 text-[var(--secondary-text)]">{audience.description}</p>
                        </div>
                      ))}
                    </div>
                  </CompanyInfoSection>

                  <CompanyInfoSection title="Business Context">
                    <div className="space-y-3">
                      {report.company.context.map((item) => (
                        <div key={item.label} className="rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-4 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
                          <p className="text-base font-medium text-[var(--primary-navy)]">{item.label}</p>
                          <p className="mt-1 text-sm leading-6 text-[var(--secondary-text)]">{item.description}</p>
                        </div>
                      ))}
                    </div>
                  </CompanyInfoSection>
                </div>
              </section>

              <ReportCompetitorComparison comparison={report.comparison} />

              <section className="rounded-[24px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.82)] p-4 shadow-[0_14px_30px_rgba(16,42,86,0.04)] sm:p-5 lg:p-6">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
                  Competitor Research Findings
                </p>
                <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[var(--primary-navy)]">
                  Key findings by category
                </h2>

                <div className="mt-5 space-y-5">
                  {Object.values(report.findings).map((group) => (
                    <div key={group.title} className="rounded-[20px] border border-[var(--light-border)] bg-[var(--white)] p-4 shadow-[0_8px_20px_rgba(19,48,95,0.02)]">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)] sm:text-[11px]">
                        {group.title}
                      </p>

                      <div className="mt-4 space-y-4">
                        {group.findings.map((finding) => (
                          <div key={`${group.title}-${finding.competitorName}`} className="rounded-2xl border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-4">
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)] sm:text-[11px]">
                              {finding.competitorName}
                            </p>
                            <p className="mt-2 text-sm leading-7 text-[var(--primary-navy)] sm:text-base">{finding.value}</p>

                            {finding.evidence.length > 0 && (
                              <div className="mt-4">
                                <EvidenceList evidence={finding.evidence} sources={report.sources} />
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <ReportAIInsights insights={report.aiInsights} />
              <ReportSources evidence={report.evidence} sources={report.sources} />
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
        <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-white/10 bg-[linear-gradient(135deg,rgba(18,24,22,0.98),rgba(16,20,19,0.96))] p-8">
              <p className="text-sm text-[var(--muted)]">Loading final research report...</p>
            </div>
          </div>
        </main>
      }
    >
      <ReportContent />
    </Suspense>
  );
}
