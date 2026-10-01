import type { Evidence } from "./evidence";
import type { Source } from "./source";

export type CompetitorResearchFindings = {
  competitorId: string;
  competitorName: string;
  overview: string;
  products: string[];
  features: string[];
  pricing: string[];
  targetAudience: string[];
  positioning: string[];
  customerFeedback: string[];
  evidence: {
    overview: Evidence[];
    products: Evidence[];
    features: Evidence[];
    pricing: Evidence[];
    targetAudience: Evidence[];
    positioning: Evidence[];
    customerFeedback: Evidence[];
  };
  sources: Record<string, Source>;
};
