export type ResearchStatus = "queued" | "running" | "completed" | "failed" | "partial";

export type ResearchStageStatus = "pending" | "running" | "completed" | "failed";

export type ResearchStageDefinition = {
  id: string;
  title: string;
  description: string;
};

export type ResearchStage = ResearchStageDefinition & {
  status: ResearchStageStatus;
};
