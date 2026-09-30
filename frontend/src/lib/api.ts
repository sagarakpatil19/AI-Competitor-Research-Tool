import type { CompanyProfile } from "@/types/company";
import type { Competitor } from "@/types/competitor";
import type { CompetitorResearchFindings } from "@/types/competitor-findings";
import type { Evidence } from "@/types/evidence";
import type { ResearchReport, ReportComparisonRow, ReportFindingGroup, ReportInsight } from "@/types/report";
import type { Source } from "@/types/source";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type BackgroundOperationStatus = "queued" | "running" | "retrying" | "completed" | "failed";

export type BackgroundOperationResponse = {
  logical_id: string;
  research_run_id: number;
  operation: string;
  status: BackgroundOperationStatus;
  attempt_count: number;
  max_attempts: number;
  resource_reference: Record<string, unknown>;
  result?: unknown;
  failure_category?: string | null;
  failure_reason?: string | null;
  status_url: string;
};

export type ResearchResponse = {
  research_id: number;
  input_value: string;
  input_type: string | null;
  resolved_domain: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  failure_reason: string | null;
};

export type CompanyResearchResponse = {
  id: number;
  research_run_id: number;
  company_name: string | null;
  domain: string | null;
  description: string | null;
  industry: string | null;
  created_at: string;
  updated_at: string;
};

export type ResearchUnderstandResponse = {
  research: ResearchResponse;
  company_research: CompanyResearchResponse;
};

export type DiscoveredCompetitorResponse = {
  id: number;
  research_run_id: number;
  name: string;
  domain: string;
  created_at: string;
  updated_at: string;
};

export type ResearchDiscoverResponse = {
  research: ResearchResponse;
  competitors: DiscoveredCompetitorResponse[];
};

export type CompetitorResearchResponse = {
  id: number;
  competitor_id: number;
  description: string | null;
  industry: string | null;
  products_services: string | null;
  target_customers: string | null;
  business_model: string | null;
  created_at: string;
  updated_at: string;
};

export type BackendReportSection = {
  id?: string | number;
  section?: string;
  status?: string;
  display_order?: number;
  items?: Array<{
    item_type?: string;
    display_order?: number;
    ai_statement_id?: string | number | null;
    ai_comparison_id?: string | number | null;
    statement?: Partial<{
      id: string | number;
      analysis_id: string | number;
      statement_type: string;
      text: string;
      support_status: string;
      competitor_research_id: string | number | null;
      section: string;
      created_at: string;
    }>;
    comparison?: Partial<{
      id: string | number;
      analysis_id: string | number;
      comparison_type: string;
      dimension: string;
      statement: string;
      support_status: string;
      competitor_research_ids: Array<string | number>;
      created_at: string;
    }>;
    statement_type?: string;
    text?: string;
    comparison_type?: string;
    dimension?: string;
  }>;
};

export type BackendReportResponse = {
  id: number;
  research_run_id: number;
  analysis_id: number;
  status: string;
  version: number;
  completed_at?: string | null;
  failure_reason?: string | null;
  created_at?: string;
  updated_at?: string;
  sections?: BackendReportSection[];
  [key: string]: unknown;
};

function buildApiUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

function normalizeIdentifier(value: unknown): string {
  if (typeof value === "number" || typeof value === "string") {
    return String(value);
  }

  return "";
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "The backend request failed. Please try again.";
}

function parseJsonBody<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return Promise.resolve(undefined as T);
  }

  return response.json() as Promise<T>;
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Request failed";

    try {
      const payload = await parseJsonBody<{ detail?: unknown; message?: string; error?: string }>(response);
      const detail = payload?.detail;

      if (typeof detail === "string") {
        message = detail;
      } else if (detail && typeof detail === "object") {
        const detailObject = detail as Record<string, unknown>;
        const nestedMessage = typeof detailObject.message === "string" ? detailObject.message : undefined;
        const nestedError = typeof detailObject.error === "string" ? detailObject.error : undefined;
        message = nestedMessage ?? nestedError ?? "Request failed";
      } else if (typeof payload?.message === "string") {
        message = payload.message;
      } else if (typeof payload?.error === "string") {
        message = payload.error;
      }
    } catch {
      message = `${response.status} ${response.statusText || "request failed"}`;
    }

    throw new Error(message);
  }

  return parseJsonBody<T>(response);
}

export async function createResearchRun(companyInput: string): Promise<ResearchResponse> {
  const trimmedInput = companyInput.trim();

  if (!trimmedInput) {
    throw new Error("A company name or website URL is required.");
  }

  return requestJson<ResearchResponse>(
    "/api/research",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ company: trimmedInput }),
    },
  );
}

export async function getResearchRun(researchId: string): Promise<ResearchResponse> {
  return requestJson<ResearchResponse>(`/api/research/${encodeURIComponent(researchId)}`);
}

export async function resolveResearchRun(researchId: string): Promise<ResearchResponse> {
  return requestJson<ResearchResponse>(`/api/research/${encodeURIComponent(researchId)}/resolve`, {
    method: "POST",
  });
}

export async function understandCompany(researchId: string): Promise<ResearchUnderstandResponse> {
  return requestJson<ResearchUnderstandResponse>(`/api/research/${encodeURIComponent(researchId)}/understand`, {
    method: "POST",
  });
}

export async function discoverCompetitors(researchId: string): Promise<BackgroundOperationResponse> {
  return requestJson<BackgroundOperationResponse>(`/api/research-runs/${encodeURIComponent(researchId)}/competitor-discovery`, {
    method: "POST",
  });
}

export async function researchCompetitors(researchId: string, competitorIds: number[]): Promise<BackgroundOperationResponse> {
  if (competitorIds.length === 0) {
    throw new Error("The backend requires at least one discovered competitor before research can start.");
  }

  return requestJson<BackgroundOperationResponse>(`/api/research/${encodeURIComponent(researchId)}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ competitor_ids: competitorIds }),
  });
}

export async function updateCompetitorResearch(
  researchId: string,
  competitorId: number,
  payload: Partial<Pick<CompetitorResearchResponse, "description" | "industry" | "products_services" | "target_customers" | "business_model">>,
): Promise<{ research: ResearchResponse; competitor_research: CompetitorResearchResponse }> {
  return requestJson(`/api/research/${encodeURIComponent(researchId)}/competitors/${competitorId}/research`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchCompetitorSources(researchId: string, competitorId: number): Promise<unknown> {
  return requestJson(`/api/research/${encodeURIComponent(researchId)}/competitors/${competitorId}/research/sources`);
}

export async function fetchCompetitorEvidence(researchId: string, competitorId: number): Promise<unknown> {
  return requestJson(`/api/research/${encodeURIComponent(researchId)}/competitors/${competitorId}/research/evidence`);
}

export async function submitAIAnalysis(
  researchId: string,
  options: {
    scope?: "competitor" | "research_run";
    competitor_research_id?: string | number;
    competitor_research_ids?: Array<string | number>;
    contract_version?: string | number;
    prompt_version?: string | number;
  } = {},
): Promise<BackgroundOperationResponse> {
  return requestJson<BackgroundOperationResponse>(`/api/research/${encodeURIComponent(researchId)}/ai-analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      scope: options.scope ?? "research_run",
      competitor_research_id: options.competitor_research_id,
      competitor_research_ids: options.competitor_research_ids,
      contract_version: options.contract_version,
      prompt_version: options.prompt_version,
    }),
  });
}

export async function createReport(researchRunId: string, analysisId: number | string): Promise<BackendReportResponse> {
  return requestJson<BackendReportResponse>(`/api/research-runs/${encodeURIComponent(researchRunId)}/reports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ analysis_id: analysisId }),
  });
}

export async function listReports(researchRunId: string): Promise<BackendReportResponse[]> {
  return requestJson<BackendReportResponse[]>(`/api/research-runs/${encodeURIComponent(researchRunId)}/reports`);
}

export async function getReport(researchRunId: string, reportId: string): Promise<BackendReportResponse> {
  return requestJson<BackendReportResponse>(`/api/research-runs/${encodeURIComponent(researchRunId)}/reports/${encodeURIComponent(reportId)}`);
}

export async function pollBackgroundOperation(
  statusUrl: string,
  timeoutMs = 120000,
  intervalMs = 2000,
): Promise<BackgroundOperationResponse> {
  const normalizedStatusUrl = statusUrl.startsWith("http") ? statusUrl : buildApiUrl(statusUrl);
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    const response = await fetch(normalizedStatusUrl, {
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Background operation status request failed (${response.status}).`);
    }

    const payload = (await response.json()) as BackgroundOperationResponse;
    const status = payload.status;

    if (!payload.status_url || !["queued", "running", "retrying", "completed", "failed"].includes(status)) {
      throw new Error("The backend returned a malformed background operation response.");
    }

    if (status === "completed" || status === "failed") {
      if (status === "failed") {
        throw new Error(payload.failure_reason || payload.failure_category || "The backend background operation failed.");
      }
      return payload;
    }

    await new Promise((resolve) => window.setTimeout(resolve, intervalMs));
  }

  throw new Error("Background operation timed out before completion.");
}

export function toCompanyProfile(raw: unknown): CompanyProfile {
  const value = (raw ?? {}) as Record<string, unknown>;

  const products = Array.isArray(value.products)
    ? value.products.map((product) => {
        if (typeof product === "string") {
          return { name: product, summary: "" };
        }

        const productRecord = (product ?? {}) as Record<string, unknown>;
        return {
          name: typeof productRecord.name === "string" ? productRecord.name : "Product",
          summary: typeof productRecord.summary === "string" ? productRecord.summary : typeof productRecord.description === "string" ? productRecord.description : "",
        };
      })
    : [];

  const audience = Array.isArray(value.audience)
    ? value.audience.map((entry) => {
        const record = (entry ?? {}) as Record<string, unknown>;
        return {
          label: typeof record.label === "string" ? record.label : "Audience",
          description: typeof record.description === "string" ? record.description : typeof record.summary === "string" ? record.summary : "",
        };
      })
    : [];

  const context = Array.isArray(value.context)
    ? value.context.map((entry) => {
        const record = (entry ?? {}) as Record<string, unknown>;
        return {
          label: typeof record.label === "string" ? record.label : "Context",
          description: typeof record.description === "string" ? record.description : typeof record.summary === "string" ? record.summary : "",
        };
      })
    : [];

  return {
    name: typeof value.name === "string" ? value.name : typeof value.company_name === "string" ? value.company_name : "",
    overview:
      typeof value.overview === "string"
        ? value.overview
        : typeof value.summary === "string"
          ? value.summary
          : "",
    industry:
      typeof value.industry === "string"
        ? value.industry
        : typeof value.market === "string"
          ? value.market
          : "",
    products,
    audience,
    context,
  };
}

function ensureRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .map((entry) => {
        if (typeof entry === "string") {
          return entry;
        }

        if (entry && typeof entry === "object") {
          const record = entry as Record<string, unknown>;
          if (typeof record.text === "string") {
            return record.text;
          }
          if (typeof record.statement === "string") {
            return record.statement;
          }
          if (typeof record.summary === "string") {
            return record.summary;
          }
        }

        return "";
      })
      .filter((entry) => entry.length > 0);
  }

  return [];
}

function buildSourceMap(rawSourceData: unknown): Record<string, Source> {
  if (!rawSourceData || typeof rawSourceData !== "object") {
    return {};
  }

  const sourceEntries = rawSourceData as Record<string, unknown>;
  const entries = Object.entries(sourceEntries).map(([key, entry]) => {
    const source = ensureRecord(entry);
    return [key, {
      id: normalizeIdentifier(source.id) || key,
      title: typeof source.title === "string" ? source.title : typeof source.name === "string" ? source.name : key,
      type: typeof source.type === "string" ? source.type : "Source",
      url: typeof source.url === "string" ? source.url : undefined,
      publisher: typeof source.publisher === "string" ? source.publisher : undefined,
      accessedAt: typeof source.accessed_at === "string" ? source.accessed_at : typeof source.accessedAt === "string" ? source.accessedAt : undefined,
    }] as const;
  });

  return Object.fromEntries(entries);
}

export function mapBackendCompetitors(raw: unknown): Competitor[] {
  const root = ensureRecord(raw);
  const candidateCollections = [
    root.competitors,
    root.candidates,
    root.results,
    root.items,
    root.data,
    root.competitor_discovery,
    root.competitorDiscovery,
  ];

  for (const collection of candidateCollections) {
    if (Array.isArray(collection)) {
      const mapped = collection.map((entry) => {
        const competitor = ensureRecord(entry);
        const backendCompetitorId = competitor.competitor_id ?? competitor.id;
        const domain = typeof competitor.domain === "string" ? competitor.domain : undefined;
        const canonicalUrl = typeof competitor.canonical_url === "string" ? competitor.canonical_url : undefined;
        return {
          id: normalizeIdentifier(backendCompetitorId) || String(competitor.name ?? competitor.candidate_name ?? "competitor"),
          name: typeof competitor.name === "string" ? competitor.name : typeof competitor.candidate_name === "string" ? competitor.candidate_name : typeof competitor.company_name === "string" ? competitor.company_name : "Competitor",
          website: canonicalUrl ?? (domain ? `https://${domain}` : undefined),
          category: typeof competitor.category === "string" ? competitor.category : typeof competitor.industry === "string" ? competitor.industry : undefined,
          description: typeof competitor.description === "string" ? competitor.description : undefined,
          discoveryReason: undefined,
        };
      });

      return mapped.filter((_competitor, index) => {
        const source = ensureRecord(collection[index]);
        return source.competitor_id === undefined || (typeof source.competitor_id === "number" && source.competitor_id > 0);
      });
    }
  }

  const flattenedResult = root.result;
  if (flattenedResult && typeof flattenedResult === "object") {
    return mapBackendCompetitors(flattenedResult);
  }

  return [];
}

export function mapBackendCompetitorFindings(raw: unknown, competitorId: string, competitorName?: string): CompetitorResearchFindings {
  const root = ensureRecord(raw);
  const overview = typeof root.description === "string" ? root.description : typeof root.overview === "string" ? root.overview : "";
  const evidence = ensureRecord(root.evidence);
  const sources = buildSourceMap(root.sources ?? root.source_map ?? root.sourceMap ?? {});

  return {
    competitorId,
    competitorName:
      typeof competitorName === "string" && competitorName.length > 0
        ? competitorName
        : typeof root.competitor_name === "string"
          ? root.competitor_name
          : typeof root.name === "string"
            ? root.name
            : competitorId,
    overview,
    products: asStringArray(root.products_services),
    features: [],
    pricing: [],
    targetAudience: asStringArray(root.target_customers),
    positioning: asStringArray(root.business_model),
    customerFeedback: [],
    evidence: {
      overview: Array.isArray(evidence.overview) ? (evidence.overview as Evidence[]) : [],
      products: Array.isArray(evidence.products) ? (evidence.products as Evidence[]) : [],
      features: Array.isArray(evidence.features) ? (evidence.features as Evidence[]) : [],
      pricing: Array.isArray(evidence.pricing) ? (evidence.pricing as Evidence[]) : [],
      targetAudience: Array.isArray(evidence.targetAudience) ? (evidence.targetAudience as Evidence[]) : [],
      positioning: Array.isArray(evidence.positioning) ? (evidence.positioning as Evidence[]) : [],
      customerFeedback: Array.isArray(evidence.customerFeedback) ? (evidence.customerFeedback as Evidence[]) : [],
    },
    sources,
  };
}

export function mapBackendReportToResearchReport(raw: Partial<BackendReportResponse> | null | undefined, fallbackCompany?: CompanyProfile): ResearchReport {
  const report = raw ?? {};
  const company = fallbackCompany ?? {
    name: "Company",
    overview: "Research report is available from the backend.",
    industry: "",
    products: [],
    audience: [],
    context: [],
  };

  const sections = Array.isArray(report.sections) ? report.sections : [];

  const groupMap: Record<string, ReportFindingGroup> = {
    products: { title: "Products", findings: [] },
    features: { title: "Features", findings: [] },
    pricing: { title: "Pricing", findings: [] },
    targetAudience: { title: "Target Audience", findings: [] },
    customerFeedback: { title: "Customer Feedback", findings: [] },
  };

  for (const section of sections) {
    const sectionName = typeof section.section === "string" ? section.section.toLowerCase() : "";
    const normalizedSection =
      sectionName.includes("product") ? "products" :
      sectionName.includes("feature") ? "features" :
      sectionName.includes("price") ? "pricing" :
      sectionName.includes("audience") ? "targetAudience" :
      sectionName.includes("feedback") ? "customerFeedback" :
      sectionName;

    const group = groupMap[normalizedSection] ?? { title: section.section ?? "Findings", findings: [] };
    const findings = Array.isArray(section.items) ? section.items : [];

    group.findings = findings.map((item) => {
      const statement = item.statement ?? {};
      const comparison = item.comparison ?? {};
      const label = typeof statement.text === "string" && statement.text.trim().length > 0
        ? statement.text
        : typeof comparison.statement === "string"
          ? comparison.statement
          : item.item_type ?? "Insight";

      return {
        competitorName: typeof comparison.dimension === "string" && comparison.dimension.length > 0 ? comparison.dimension : "Competitor",
        value: label,
        evidence: [],
      };
    });

    if (normalizedSection in groupMap) {
      groupMap[normalizedSection] = group;
    }
  }

  const comparisonRows: ReportComparisonRow[] = sections
    .filter((section) => Array.isArray(section.items))
    .map((section) => ({
      category: typeof section.section === "string" ? section.section : "Comparison",
      targetCompany: company.name,
      competitors: (section.items ?? []).map((item) => ({
        name: item.comparison?.dimension ?? "Competitor",
        value: item.comparison?.statement ?? item.statement?.text ?? "No comparison detail available.",
      })),
    }));

  const aiInsights: ReportInsight[] = sections
    .flatMap((section) => (Array.isArray(section.items) ? section.items : []).map((item) => {
      const statement = item.statement ?? {};
      const text = typeof statement.text === "string" ? statement.text : typeof item.item_type === "string" ? item.item_type : "AI insight";
      return {
        title: section.section ?? "AI insight",
        summary: text,
        kind: "analysis",
      };
    }));

  return {
    company,
    executiveSummary:
      typeof report.status === "string" && report.status !== "completed"
        ? `The backend report is currently ${report.status}.`
        : `Report generated from the backend research findings. ${company.name} was analyzed across company understanding, competitor discovery, and supporting evidence.`,
    competitors: [],
    comparison: comparisonRows,
    findings: {
      products: groupMap.products,
      features: groupMap.features,
      pricing: groupMap.pricing,
      targetAudience: groupMap.targetAudience,
      customerFeedback: groupMap.customerFeedback,
    },
    aiInsights,
    evidence: [],
    sources: {},
  };
}

export function getApiErrorMessage(error: unknown, fallback = "Something went wrong while contacting the backend."): string {
  const message = getErrorMessage(error);
  return message && message !== "Request failed" ? message : fallback;
}

export function toNumber(value: unknown): number | undefined {
  if (typeof value === "number") {
    return value;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }

  return undefined;
}
