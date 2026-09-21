export type CompanyProduct = {
  name: string;
  summary: string;
};

export type CompanyAudience = {
  label: string;
  description: string;
};

export type CompanyContext = {
  label: string;
  description: string;
};

export type CompanyProfile = {
  name: string;
  overview: string;
  industry: string;
  products: CompanyProduct[];
  audience: CompanyAudience[];
  context: CompanyContext[];
};
