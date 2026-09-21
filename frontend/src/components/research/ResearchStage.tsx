import type { ResearchStage as ResearchStageType } from "@/types/research";

export function ResearchStage({
  stage,
  isCurrent,
  index,
}: {
  stage: ResearchStageType;
  isCurrent: boolean;
  index: number;
}) {
  const isCompleted = stage.status === "completed";
  const isRunning = stage.status === "running";
  const isPending = stage.status === "pending";
  const isFailed = stage.status === "failed";

  const labelMap = {
    completed: { text: "Completed", icon: "✓", classes: "bg-[var(--soft-blue)] text-[var(--primary-blue)]" },
    running: { text: "In progress", icon: "●", classes: "bg-[var(--secondary-light-blue)] text-[var(--primary-blue)]" },
    pending: { text: "Upcoming", icon: "○", classes: "bg-[var(--very-soft-blue)] text-[var(--secondary-text)]" },
    failed: { text: "Needs attention", icon: "!", classes: "bg-[#FDECEC] text-[#C94B4B]" },
  } as const;

  const statusInfo = labelMap[stage.status] ?? labelMap.pending;

  return (
    <div
      className={[
        "group relative rounded-[22px] border p-4 transition duration-200",
        isCurrent
          ? "border-[var(--primary-blue)]/35 bg-[var(--secondary-light-blue)] shadow-[0_12px_24px_rgba(50,111,234,0.08)]"
          : isRunning
            ? "border-[var(--primary-blue)]/25 bg-[var(--very-soft-blue)]"
            : isCompleted
              ? "border-[var(--soft-blue)] bg-[var(--secondary-light-blue)]"
              : isFailed
                ? "border-[#F5CACA] bg-[#FFF6F6]"
                : "border-[var(--light-border)] bg-[var(--white)]",
        "hover:-translate-y-0.5 hover:border-[var(--primary-blue)]/35 hover:bg-[var(--secondary-light-blue)]",
      ].join(" ")}
      aria-current={isCurrent ? "step" : undefined}
      aria-label={`${stage.title}: ${statusInfo.text}`}
    >
      <div className="flex items-start gap-4">
        <div
          className={[
            "relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl text-[11px] font-semibold",
            isCompleted
              ? "bg-[var(--soft-blue)] text-[var(--primary-blue)]"
              : isRunning
                ? "bg-[var(--primary-blue)] text-white shadow-[0_10px_18px_rgba(50,111,234,0.18)]"
                : isFailed
                  ? "bg-[#FDECEC] text-[#C94B4B]"
                  : "bg-[var(--very-soft-blue)] text-[var(--secondary-text)] border border-[var(--light-border)]",
          ].join(" ")}
          aria-hidden="true"
        >
          {String(index + 1).padStart(2, "0")}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-base font-semibold text-[var(--primary-navy)]">{stage.title}</p>
            <span
              className={[
                "inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]",
                statusInfo.classes,
              ].join(" ")}
            >
              <span aria-hidden="true">{statusInfo.icon}</span>
              {statusInfo.text}
            </span>
          </div>

          <p className="mt-2 text-sm leading-6 text-[var(--secondary-text)]">{stage.description}</p>
        </div>
      </div>
    </div>
  );
}
