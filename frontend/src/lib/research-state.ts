const ACTIVE_RESEARCH_KEY = "ai_competitor_research_active_run";

export function saveActiveResearchId(researchId: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(ACTIVE_RESEARCH_KEY, researchId);
}

export function readActiveResearchId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawValue = window.localStorage.getItem(ACTIVE_RESEARCH_KEY);
  return rawValue && rawValue.trim().length > 0 ? rawValue : null;
}

export function clearActiveResearchId(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(ACTIVE_RESEARCH_KEY);
}
