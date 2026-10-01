import type { CompanyProfile } from "./company";
import type { Evidence } from "./evidence";
import type { Source } from "./source";

export type ReportComparisonRow = {
  category: string;
  targetCompany: string;
  competitors: Array<{
    name: string;
    value: string;
  }>;
};

export type ReportFindingGroup = {
  title: string;
  findings: Array<{
    competitorName: string;
    value: string;
    evidence: Evidence[];
  }>;
};

export type ReportInsight = {
  title: string;
  summary: string;
  kind: "analysis" | "pattern";
};

export type ResearchReport = {
  company: CompanyProfile;
  executiveSummary: string;
  competitors: Array<{
    id: string;
    name: string;
    summary: string;
  }>;
  comparison: ReportComparisonRow[];
  findings: {
    products: ReportFindingGroup;
    features: ReportFindingGroup;
    pricing: ReportFindingGroup;
    targetAudience: ReportFindingGroup;
    customerFeedback: ReportFindingGroup;
  };
  aiInsights: ReportInsight[];
  evidence: Evidence[];
  sources: Record<string, Source>;
};

export type CompanyResearchReport = ResearchReport;
