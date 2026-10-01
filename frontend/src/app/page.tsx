"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { createResearchRun, getApiErrorMessage } from "@/lib/api";
import { saveActiveResearchId } from "@/lib/research-state";

type FormStatus = "idle" | "error" | "submitting";

const howItWorks = [
  {
    step: "01",
    title: "Understand",
    description: "We analyze the company's website, products, audience and market position.",
    accent: "bg-[var(--soft-blue)]",
    icon: "document",
  },
  {
    step: "02",
    title: "Discover",
    description: "We find and research relevant competitors in the same market.",
    accent: "bg-[var(--very-soft-blue)]",
    icon: "nodes",
  },
  {
    step: "03",
    title: "Research & Compare",
    description: "We compare features, pricing, customer feedback and evidence-backed sources.",
    accent: "bg-[var(--soft-cyan)]",
    icon: "report",
  },
];

const flowSteps = [
  { label: "Company", text: "You enter a company" },
  { label: "Competitors", text: "We find relevant competitors" },
  { label: "Insights", text: "You get a clear report" },
];

const previewSections = [
  "Overview",
  "Competitors",
  "Features",
  "Pricing",
  "Target Audience",
  "Customer Feedback",
  "AI Insights",
  "Sources",
];

const MOCK_AUTH_KEY = "ai_competitor_research_mock_auth";

function isMockAuthenticated() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.localStorage.getItem(MOCK_AUTH_KEY) === "true";
}

export default function Home() {
  const router = useRouter();
  const [company, setCompany] = useState("");
  const [status, setStatus] = useState<FormStatus>("idle");
  const [validationMessage, setValidationMessage] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const syncAuthState = () => setIsAuthenticated(isMockAuthenticated());

    syncAuthState();

    window.addEventListener("storage", syncAuthState);

    return () => {
      window.removeEventListener("storage", syncAuthState);
    };
  }, []);

  const handleLogout = () => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.removeItem(MOCK_AUTH_KEY);
    setIsAuthenticated(false);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedCompany = company.trim();

    if (!trimmedCompany) {
      setStatus("error");
      setValidationMessage("Please enter a company name or website URL.");
      return;
    }

    setStatus("submitting");
    setValidationMessage("");

    try {
      const response = await createResearchRun(trimmedCompany);
      saveActiveResearchId(String(response.research_id));

      const encodedCompany = encodeURIComponent(trimmedCompany);
      router.push(`/research/progress?company=${encodedCompany}&research_id=${encodeURIComponent(response.research_id)}`);
    } catch (error) {
      setStatus("error");
      setValidationMessage(getApiErrorMessage(error, "The research run could not be started. Please try again."));
    }
  };

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="sticky top-0 z-20 pb-4 pt-2">
          <nav className="flex items-center justify-between rounded-full border border-[var(--border)] bg-[var(--surface)]/80 px-4 py-3 shadow-[0_10px_24px_rgba(19,48,95,0.04)] backdrop-blur-sm sm:px-6">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--accent)] bg-[var(--surface-subtle)] text-[10px] font-semibold text-[var(--primary)]">
                AI
              </div>
              <span className="text-sm font-semibold tracking-[0.16em] text-[var(--foreground)] uppercase">
                AI Competitor Research
              </span>
            </div>

            <div className="hidden items-center gap-6 md:flex">
              <a href="#how-it-works" className="text-sm text-[var(--foreground-secondary)] transition hover:text-[var(--primary)]">
                How it works
              </a>
              <a href="#about" className="text-sm text-[var(--foreground-secondary)] transition hover:text-[var(--primary)]">
                About
              </a>
              <span className="text-sm text-[var(--foreground-secondary)]">GitHub</span>
              {isAuthenticated ? (
                <>
                  <Link href="/history" className="text-sm text-[var(--foreground-secondary)] transition hover:text-[var(--primary)]">
                    History
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="text-sm text-[var(--foreground-secondary)] transition hover:text-[var(--primary)]"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link href="/login" className="text-sm text-[var(--foreground-secondary)] transition hover:text-[var(--primary)]">
                    Login
                  </Link>
                  <Link href="/signup" className="text-sm text-[var(--foreground-secondary)] transition hover:text-[var(--primary)]">
                    Sign Up
                  </Link>
                </>
              )}
            </div>

            <div className="flex items-center gap-3">
              <ThemeToggle />
              <a
                href="#research"
                className="inline-flex items-center justify-center rounded-full bg-[var(--primary)] px-4 py-2 text-sm font-semibold text-[var(--background)] shadow-[0_10px_20px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/30"
              >
                Start Research
              </a>
            </div>
          </nav>
        </header>

        <section className="overflow-hidden rounded-[30px] border border-[var(--border)] bg-[linear-gradient(135deg,var(--background)_0%,var(--surface-subtle)_52%,var(--surface)_100%)] shadow-[0_24px_60px_rgba(31,72,135,0.06)]">
          <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-12 lg:px-10 lg:py-16">
            <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
              <div>
                <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--primary)] sm:text-xs">
                  Competitive Intelligence
                </p>

                <h1 className="max-w-[13ch] text-4xl font-semibold leading-[0.96] tracking-[-0.06em] text-[var(--foreground)] sm:text-5xl lg:text-[4rem] lg:leading-[0.95]">
                  Research any company.
                  <span className="mt-1 block text-[var(--primary)]">Understand its competition.</span>
                </h1>

                <p className="mt-6 max-w-xl text-base leading-7 text-[var(--foreground-secondary)] sm:text-lg">
                  Discover competitors, compare products, pricing, features and customer feedback with evidence-backed research.
                </p>

                <form id="research" className="mt-8 max-w-2xl" onSubmit={handleSubmit} noValidate>
                  <div>
                    <label htmlFor="company" className="mb-2 block text-sm font-medium text-[var(--foreground)]">
                      Company
                    </label>

                    <div className="flex flex-col gap-3 sm:flex-row sm:items-stretch">
                      <input
                        id="company"
                        name="company"
                        type="text"
                        value={company}
                        onChange={(event) => {
                          setCompany(event.target.value);
                          if (status === "error") {
                            setStatus("idle");
                            setValidationMessage("");
                          }
                        }}
                        placeholder="Enter company name or website URL"
                        aria-invalid={status === "error"}
                        aria-describedby={status === "error" ? "company-error" : undefined}
                        disabled={status === "submitting"}
                        className="h-[56px] w-full min-w-0 rounded-2xl border border-[var(--accent)] bg-[var(--surface)] px-4 text-base text-[var(--foreground)] placeholder:text-[var(--foreground-secondary)] shadow-[0_10px_24px_rgba(50,111,234,0.06)] transition focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 disabled:cursor-not-allowed disabled:opacity-60 sm:flex-1"
                      />

                      <button
                        type="submit"
                        disabled={status === "submitting"}
                        className="inline-flex h-[56px] shrink-0 items-center justify-center rounded-2xl bg-[var(--primary)] px-5 text-sm font-semibold text-[var(--background)] shadow-[0_12px_24px_rgba(50,111,234,0.22)] transition hover:-translate-y-0.5 hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/25 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {status === "submitting" ? "Starting..." : "Research"}
                      </button>
                    </div>

                    {status === "error" && (
                      <p id="company-error" role="alert" className="mt-3 text-sm text-[var(--primary)]">
                        {validationMessage}
                      </p>
                    )}

                    {status === "submitting" && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-[var(--foreground-secondary)]" aria-live="polite">
                        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[var(--primary)] border-t-transparent" />
                        Preparing the research workflow...
                      </div>
                    )}
                  </div>
                </form>

                <div className="mt-7 flex flex-wrap items-center gap-3 text-[11px] font-medium uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">
                  {flowSteps.map((step, index) => (
                    <div key={step.label} className="flex items-center gap-3">
                      <div className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-[10px] font-semibold text-[var(--foreground)]">
                        {step.label}
                      </div>
                      {index < flowSteps.length - 1 && <span aria-hidden="true">→</span>}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-center lg:justify-end">
                <div className="w-full max-w-[420px] rounded-[28px] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[0_18px_32px_rgba(19,48,95,0.06)] sm:p-6">
                  <div className="pb-4 text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">
                    RESEARCH SNAPSHOT
                  </div>

                  {isAuthenticated ? (
                    <>
                      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-3.5">
                        <div className="text-sm font-semibold text-[var(--foreground)]">Notion</div>
                        <div className="mt-1 text-xs leading-5 text-[var(--foreground-secondary)]">Workspace & productivity platform</div>
                      </div>

                      <div className="mt-5">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">Competitors</div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <span className="rounded-full border border-[var(--border)] bg-[var(--surface-subtle)] px-2.5 py-1.5 text-[10px] font-medium text-[var(--foreground)]">Slack</span>
                          <span className="rounded-full border border-[var(--border)] bg-[var(--surface-subtle)] px-2.5 py-1.5 text-[10px] font-medium text-[var(--foreground)]">Coda</span>
                          <span className="rounded-full border border-[var(--border)] bg-[var(--surface-subtle)] px-2.5 py-1.5 text-[10px] font-medium text-[var(--foreground)]">ClickUp</span>
                        </div>
                      </div>

                      <div className="mt-5">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">Research</div>
                        <div className="mt-3 space-y-2 text-sm text-[var(--foreground)]">
                          <div className="flex items-center justify-between gap-3">
                            <span>Company</span>
                            <span className="text-[var(--primary)]">✓</span>
                          </div>
                          <div className="flex items-center justify-between gap-3">
                            <span>Competitors</span>
                            <span className="text-[var(--primary)]">✓</span>
                          </div>
                          <div className="flex items-center justify-between gap-3">
                            <span>Evidence</span>
                            <span className="text-[var(--primary)]">✓</span>
                          </div>
                          <div className="flex items-center justify-between gap-3">
                            <span>Insights</span>
                            <span className="text-[var(--primary)]">●</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-5 border-t border-[var(--border)] pt-4 text-sm leading-6 text-[var(--foreground-secondary)]">
                        Evidence-backed research
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-3.5 text-sm font-semibold text-[var(--foreground)]">
                        No research started yet
                      </div>

                      <div className="mt-5">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">Research</div>
                        <div className="mt-3 space-y-2 text-sm text-[var(--foreground)]">
                          <div className="flex items-center justify-between gap-3">
                            <span>Company</span>
                            <span className="text-[var(--foreground-secondary)]">○</span>
                          </div>
                          <div className="flex items-center justify-between gap-3">
                            <span>Competitors</span>
                            <span className="text-[var(--foreground-secondary)]">○</span>
                          </div>
                          <div className="flex items-center justify-between gap-3">
                            <span>Evidence</span>
                            <span className="text-[var(--foreground-secondary)]">○</span>
                          </div>
                          <div className="flex items-center justify-between gap-3">
                            <span>Insights</span>
                            <span className="text-[var(--foreground-secondary)]">○</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-5 border-t border-[var(--border)] pt-4 text-sm leading-6 text-[var(--foreground-secondary)]">
                        Your research journey will appear here.
                      </div>
                    </>
                  )}
                </div>
              </div>

            </div>
          </div>
        </section>

        <section id="how-it-works" className="mx-auto max-w-6xl px-0 py-20">
          <div className="mb-10 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">How it works</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--foreground)] sm:text-4xl">
              Turn a company into competitive insights
            </h2>
            <p className="mt-3 text-base text-[var(--foreground-secondary)]">A simple process. A powerful output.</p>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            {howItWorks.map((item, index) => (
              <div key={item.step} className="group relative rounded-[28px] border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6 shadow-[0_14px_28px_rgba(19,48,95,0.04)] transition hover:-translate-y-1 hover:shadow-[0_20px_36px_rgba(19,48,95,0.06)]">
                <div className="flex items-center justify-between">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${item.accent}`}>
                    {item.icon === "document" && <div className="h-6 w-5 rounded-md border border-[var(--primary)] bg-[var(--surface)]" />}
                    {item.icon === "nodes" && (
                      <div className="relative h-6 w-6">
                        <span className="absolute left-0 top-2 h-2 w-2 rounded-full bg-[var(--primary)]" />
                        <span className="absolute right-0 top-0 h-2 w-2 rounded-full bg-[var(--accent)]" />
                        <span className="absolute right-0 bottom-0 h-2 w-2 rounded-full bg-[var(--surface-subtle)]" />
                        <span className="absolute left-2 bottom-0 h-2 w-2 rounded-full bg-[var(--foreground)]" />
                      </div>
                    )}
                    {item.icon === "report" && <div className="h-6 w-5 rounded border border-[var(--primary)] bg-[var(--surface)]" />}
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">{item.step}</span>
                </div>

                <h3 className="mt-6 text-2xl font-semibold text-[var(--foreground)]">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-[var(--foreground-secondary)] sm:text-base">{item.description}</p>

                {index < howItWorks.length - 1 && (
                  <div className="mt-6 h-px w-full bg-[var(--border)]" />
                )}
              </div>
            ))}
          </div>
        </section>

        <section id="report-preview" className="mx-auto max-w-6xl py-2 pb-20">
          <div className="mb-8 max-w-2xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">Turn research into clarity</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--foreground)] sm:text-4xl">
              Competitive Research Report
            </h2>
            <p className="mt-3 text-base leading-7 text-[var(--foreground-secondary)]">
              Get a clear, structured report with everything you need to understand a company and its competitive landscape.
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-[0.88fr_1.12fr]">
            <div className="rounded-[28px] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[0_14px_30px_rgba(19,48,95,0.04)]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--primary)]">Checklist</p>
              <ul className="mt-5 space-y-3 text-sm text-[var(--foreground)]">
                {[
                  "Company overview",
                  "Competitor landscape",
                  "Products & features",
                  "Pricing comparison",
                  "Target audience",
                  "Customer feedback",
                  "Evidence-backed insights",
                  "Sources and references",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] px-3 py-2.5">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--primary)] text-[10px] font-bold text-[var(--background)]">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="overflow-hidden rounded-[30px] border border-[var(--border)] bg-[var(--surface)] shadow-[0_18px_30px_rgba(19,48,95,0.05)]">
              <div className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface-subtle)] px-5 py-4">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--primary)]">Competitive Research Report</p>
                  <h3 className="mt-2 text-xl font-semibold text-[var(--foreground)]">Notion</h3>
                </div>
                <div className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--foreground-secondary)]">
                  Preview
                </div>
              </div>

              <div className="grid gap-4 p-4 lg:grid-cols-[1.05fr_1.35fr]">
                <div className="space-y-4">
                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">Target company</p>
                    <p className="mt-2 text-sm font-medium text-[var(--foreground)]">Notion</p>
                  </div>

                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-subtle)] p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">Competitor landscape</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-[var(--foreground)]">Slack</span>
                      <span className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-[var(--foreground)]">Coda</span>
                      <span className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1.5 text-[var(--foreground)]">ClickUp</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {previewSections.map((section, index) => (
                    <div
                      key={section}
                      className={`rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-[0_10px_22px_rgba(19,48,95,0.04)] ${
                        index % 2 === 0 ? "border-[var(--border)] bg-[var(--surface-subtle)]" : "border-[var(--accent)] bg-[var(--surface-subtle)]"
                      }`}
                    >
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground-secondary)]">{section}</p>

                      {section === "Features" && (
                        <div className="mt-3 flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--primary)]" />
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--surface-strong)]" />
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--foreground)]/70" />
                        </div>
                      )}

                      {section === "Pricing" && (
                        <div className="mt-3 h-2.5 w-full rounded-full bg-[linear-gradient(90deg,var(--accent)_0%,var(--accent)_35%,var(--surface-subtle)_35%,var(--surface-subtle)_70%,var(--surface-strong)_70%,var(--surface-strong)_100%)]" />
                      )}

                      {section === "AI Insights" && (
                        <div className="mt-3 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-2 text-[11px] leading-5 text-[var(--foreground)]">
                          Research-backed observations synthesized into a clear strategic narrative.
                        </div>
                      )}

                      {section === "Sources" && (
                        <div className="mt-3 flex items-center gap-2 text-[11px] text-[var(--foreground-secondary)]">
                          <span className="rounded-full bg-[var(--accent)] px-2 py-1 text-[var(--primary)]">Evidence</span>
                          <span>→</span>
                          <span className="rounded-full bg-[var(--surface-subtle)] px-2 py-1 text-[var(--foreground)]">Source</span>
                        </div>
                      )}

                      {section !== "Features" && section !== "Pricing" && section !== "AI Insights" && section !== "Sources" && (
                        <div className="mt-3 space-y-1 text-sm leading-6 text-[var(--foreground-secondary)]">
                          <div>• Summary</div>
                          <div>• Evidence-backed context</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="about" className="mx-auto max-w-5xl py-2 pb-20">
          <div className="rounded-[28px] border border-[var(--border)] bg-[var(--surface-subtle)] p-5 sm:p-6 lg:p-8">
            <div className="mb-6 flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">Research that shows its sources</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--foreground)] sm:text-4xl">
                  From sources to insights
                </h2>
              </div>
            </div>

            <p className="max-w-2xl text-base leading-7 text-[var(--foreground-secondary)]">
              Every insight is backed by real sources. You can trace information from the original source to the final insight.
            </p>

            <div className="mt-8 grid gap-4 md:grid-cols-4">
              {[
                { title: "Source", text: "Web pages, articles and reviews" },
                { title: "Evidence", text: "Key information extracted" },
                { title: "Finding", text: "Structured research data" },
                { title: "AI Insight", text: "Clear, easy-to-understand interpretation" },
              ].map((item, index) => (
                <div key={item.title} className="relative rounded-[24px] border border-[var(--border)] bg-[var(--surface)] p-4">
                  <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-[var(--accent)] text-[11px] font-bold text-[var(--primary)]">
                    {index + 1}
                  </div>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary)]">{item.title}</div>
                  <p className="mt-3 text-sm leading-6 text-[var(--foreground-secondary)]">{item.text}</p>
                  {index < 3 && <div className="mt-4 h-px w-full bg-[var(--border)]" />}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-5xl py-2 pb-20">
          <div className="rounded-[28px] border border-[var(--border)] bg-[var(--surface-strong)] p-6 text-[var(--foreground)] shadow-[0_18px_34px_rgba(11,35,72,0.14)] sm:p-8 lg:p-10">
            <div className="flex flex-col gap-6 text-center md:flex-row md:items-center md:justify-between md:text-left">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">Start here</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--foreground)] sm:text-4xl">
                  Start researching your competition.
                </h2>
                <p className="mt-3 text-base text-[var(--foreground-secondary)]">Enter a company name or website to get started.</p>
              </div>

              <a
                href="#research"
                className="inline-flex h-[52px] items-center justify-center rounded-2xl bg-[var(--surface)] px-6 text-sm font-semibold text-[var(--foreground)] shadow-[0_12px_24px_rgba(255,255,255,0.12)] transition hover:-translate-y-0.5 hover:bg-[var(--surface-subtle)]"
              >
                Start Research →
              </a>
            </div>
          </div>
        </section>

        <footer className="mx-auto max-w-6xl pb-10 pt-2 text-[var(--foreground-secondary)]">
          <div className="rounded-[26px] border border-[var(--border)] bg-[var(--surface)] px-4 py-6 sm:px-6 lg:px-8">
            <div className="grid gap-8 md:grid-cols-[1.3fr_1fr_1fr]">
              <div>
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--accent)] bg-[var(--surface-subtle)] text-[10px] font-semibold text-[var(--primary)]">
                    AI
                  </div>
                  <span className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--foreground)]">AI Competitor Research</span>
                </div>
                <p className="mt-4 max-w-sm text-sm leading-7 text-[var(--foreground-secondary)]">
                  Research any company.
                  <span className="mt-1 block">Understand its competition.</span>
                </p>
              </div>

              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground)]">Product</p>
                <ul className="mt-3 space-y-2 text-sm">
                  <li>Research</li>
                  <li>Competitors</li>
                  <li>Reports</li>
                </ul>
              </div>

              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--foreground)]">Project</p>
                <ul className="mt-3 space-y-2 text-sm">
                  <li>GitHub</li>
                  <li>About</li>
                </ul>
              </div>
            </div>

            <div className="mt-8 border-t border-[var(--border)] pt-5 text-xs uppercase tracking-[0.2em] text-[var(--foreground-secondary)]">
              © 2026 AI Competitor Research
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
