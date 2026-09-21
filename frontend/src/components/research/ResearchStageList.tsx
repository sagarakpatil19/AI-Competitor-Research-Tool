import type { ResearchStage } from "@/types/research";
import { ResearchStage as ResearchStageItem } from "./ResearchStage";

export function ResearchStageList({ stages }: { stages: ResearchStage[] }) {
  const currentStageIndex = stages.findIndex((stage) => stage.status === "running");

  return (
    <div className="relative space-y-3 pl-2 before:absolute before:left-[1.1rem] before:top-3 before:bottom-3 before:w-px before:bg-[var(--light-border)]">
      {stages.map((stage, index) => (
        <div key={stage.id} className="relative pl-10">
          <ResearchStageItem
            stage={stage}
            index={index}
            isCurrent={index === currentStageIndex || (currentStageIndex === -1 && index === stages.length - 1 && stage.status === "pending")}
          />
        </div>
      ))}
    </div>
  );
}
