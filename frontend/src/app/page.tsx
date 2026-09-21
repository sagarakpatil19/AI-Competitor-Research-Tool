"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

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

export default function Home() {
  const router = useRouter();
  const [company, setCompany] = useState("");
  const [status, setStatus] = useState<FormStatus>("idle");
  const [validationMessage, setValidationMessage] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedCompany = company.trim();

    if (!trimmedCompany) {
      setStatus("error");
      setValidationMessage("Please enter a company name or website URL.");
      return;
    }

    setStatus("submitting");
    setValidationMessage("");

    const encodedCompany = encodeURIComponent(trimmedCompany);

    window.setTimeout(() => {
      router.push(`/research/progress?company=${encodedCompany}`);
    }, 700);
  };

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--primary-navy)]">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="sticky top-0 z-20 pb-4 pt-2">
          <nav className="flex items-center justify-between rounded-full border border-[var(--light-border)] bg-[rgba(255,255,255,0.75)] px-4 py-3 shadow-[0_10px_24px_rgba(19,48,95,0.04)] backdrop-blur-sm sm:px-6">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[10px] font-semibold text-[var(--primary-blue)]">
                AI
              </div>
              <span className="text-sm font-semibold tracking-[0.16em] text-[var(--primary-navy)] uppercase">
                AI Competitor Research
              </span>
            </div>

            <div className="hidden items-center gap-6 md:flex">
              <a href="#how-it-works" className="text-sm text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]">
                How it works
              </a>
              <a href="#about" className="text-sm text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]">
                About
              </a>
              <span className="text-sm text-[var(--secondary-text)]">GitHub</span>
            </div>

            <a
              href="#research"
              className="inline-flex items-center justify-center rounded-full bg-[var(--primary-blue)] px-4 py-2 text-sm font-semibold text-white shadow-[0_10px_20px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/30"
            >
              Start Research
            </a>
          </nav>
        </header>

        <section className="overflow-hidden rounded-[30px] border border-[var(--light-border)] bg-[linear-gradient(135deg,#F7FAFF_0%,#EEF5FF_52%,#F7FBFF_100%)] shadow-[0_24px_60px_rgba(31,72,135,0.06)]">
          <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-12 lg:px-10 lg:py-16">
            <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
              <div>
                <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.24em] text-[var(--primary-blue)] sm:text-xs">
                  Competitive Intelligence
                </p>

                <h1 className="max-w-[13ch] text-4xl font-semibold leading-[0.96] tracking-[-0.06em] text-[var(--primary-navy)] sm:text-5xl lg:text-[4rem] lg:leading-[0.95]">
                  Research any company.
                  <span className="mt-1 block text-[var(--primary-blue)]">Understand its competition.</span>
                </h1>

                <p className="mt-6 max-w-xl text-base leading-7 text-[var(--secondary-text)] sm:text-lg">
                  Discover competitors, compare products, pricing, features and customer feedback with evidence-backed research.
                </p>

                <form id="research" className="mt-8 max-w-2xl" onSubmit={handleSubmit} noValidate>
                  <div>
                    <label htmlFor="company" className="mb-2 block text-sm font-medium text-[var(--primary-navy)]">
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
                        className="h-[56px] w-full min-w-0 rounded-2xl border border-[var(--soft-blue)] bg-[var(--white)] px-4 text-base text-[var(--primary-navy)] placeholder:text-[var(--secondary-text)] shadow-[0_10px_24px_rgba(50,111,234,0.06)] transition focus:border-[var(--primary-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/20 disabled:cursor-not-allowed disabled:opacity-60 sm:flex-1"
                      />

                      <button
                        type="submit"
                        disabled={status === "submitting"}
                        className="inline-flex h-[56px] shrink-0 items-center justify-center rounded-2xl bg-[var(--primary-blue)] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.22)] transition hover:-translate-y-0.5 hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/25 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {status === "submitting" ? "Starting..." : "Research"}
                      </button>
                    </div>

                    {status === "error" && (
                      <p id="company-error" role="alert" className="mt-3 text-sm text-[var(--primary-blue)]">
                        {validationMessage}
                      </p>
                    )}

                    {status === "submitting" && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-[var(--secondary-text)]" aria-live="polite">
                        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[var(--primary-blue)] border-t-transparent" />
                        Preparing the research workflow...
                      </div>
                    )}
                  </div>
                </form>

                <div className="mt-7 flex flex-wrap items-center gap-3 text-[11px] font-medium uppercase tracking-[0.18em] text-[var(--secondary-text)]">
                  {flowSteps.map((step, index) => (
                    <div key={step.label} className="flex items-center gap-3">
                      <div className="rounded-full border border-[var(--light-border)] bg-[var(--white)] px-2.5 py-1.5 text-[10px] font-semibold text-[var(--primary-navy)]">
                        {step.label}
                      </div>
                      {index < flowSteps.length - 1 && <span aria-hidden="true">→</span>}
                    </div>
                  ))}
                </div>
              </div>

              <div className="relative">
                <div className="relative mx-auto w-full max-w-[480px] overflow-hidden rounded-[32px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F0F7FF_100%)] p-6 shadow-[0_24px_48px_rgba(19,48,95,0.06)]">
                  <div className="absolute left-6 top-6 h-16 w-16 rounded-full bg-[var(--soft-blue)] blur-2xl" aria-hidden="true" />
                  <div className="absolute bottom-6 right-6 h-20 w-20 rounded-full bg-[var(--soft-cyan)] blur-2xl" aria-hidden="true" />

                  <div className="relative rounded-[24px] border border-[var(--light-border)] bg-[var(--white)] p-4 shadow-[0_12px_30px_rgba(19,48,95,0.04)]">
                    <div className="flex items-center justify-between pb-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2.5 w-2.5 rounded-full bg-[var(--primary-blue)]" />
                        <div className="h-2.5 w-2.5 rounded-full bg-[var(--soft-blue)]" />
                        <div className="h-2.5 w-2.5 rounded-full bg-[var(--soft-cyan)]" />
                      </div>
                      <span className="rounded-full bg-[var(--soft-blue)] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
                        Research
                      </span>
                    </div>

                    <div className="mt-4 grid gap-3">
                      <div className="rounded-2xl border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-3">
                        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">Company</div>
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="text-sm font-semibold text-[var(--primary-navy)]">Notion</div>
                            <div className="text-[11px] text-[var(--secondary-text)]">Workspace platform</div>
                          </div>
                          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--white)] text-[11px] font-semibold text-[var(--primary-blue)]">
                            N
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { label: "Slack", color: "bg-[var(--soft-blue)]" },
                          { label: "Coda", color: "bg-[var(--soft-cyan)]" },
                          { label: "ClickUp", color: "bg-[var(--very-soft-blue)]" },
                        ].map((card) => (
                          <div key={card.label} className={`rounded-2xl border border-[var(--light-border)] ${card.color} p-3 text-center`}>
                            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--secondary-text)]">{card.label}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="relative mt-5 rounded-[26px] border border-[var(--light-border)] bg-[var(--white)] p-4 shadow-[0_12px_28px_rgba(19,48,95,0.04)]">
                    <div className="absolute -left-2 top-8 h-3 w-3 rounded-full bg-[var(--primary-blue)]" />
                    <div className="absolute left-12 top-8 h-px w-[90%] bg-[var(--light-border)]" />
                    <div className="absolute left-6 top-5 h-8 w-8 rounded-full bg-[var(--soft-blue)]" />
                    <div className="absolute right-4 top-6 h-2 w-2 rounded-full bg-[var(--primary-blue)]" />

                    <div className="ml-12 flex items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[10px] font-semibold text-[var(--primary-blue)]">
                        AI
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">Insights</div>
                        <div className="mt-1 text-sm font-medium text-[var(--primary-navy)]">Research-backed findings</div>
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-2 text-[11px] text-[var(--secondary-text)]">
                      <div className="rounded-xl border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-2">Find competitors</div>
                      <div className="rounded-xl border border-[var(--light-border)] bg-[var(--soft-cyan)] p-2">Compare products</div>
                      <div className="rounded-xl border border-[var(--light-border)] bg-[var(--very-soft-blue)] p-2">Understand the market</div>
                      <div className="rounded-xl border border-[var(--light-border)] bg-[var(--soft-blue)] p-2">From data to decisions</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="mx-auto max-w-6xl px-0 py-20">
          <div className="mb-10 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">How it works</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-4xl">
              Turn a company into competitive insights
            </h2>
            <p className="mt-3 text-base text-[var(--secondary-text)]">A simple process. A powerful output.</p>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            {howItWorks.map((item, index) => (
              <div key={item.step} className="group relative rounded-[28px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.7)] p-5 sm:p-6 shadow-[0_14px_28px_rgba(19,48,95,0.04)] transition hover:-translate-y-1 hover:shadow-[0_20px_36px_rgba(19,48,95,0.06)]">
                <div className="flex items-center justify-between">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${item.accent}`}>
                    {item.icon === "document" && <div className="h-6 w-5 rounded-md border border-[var(--primary-blue)] bg-[white]" />}
                    {item.icon === "nodes" && (
                      <div className="relative h-6 w-6">
                        <span className="absolute left-0 top-2 h-2 w-2 rounded-full bg-[var(--primary-blue)]" />
                        <span className="absolute right-0 top-0 h-2 w-2 rounded-full bg-[var(--soft-cyan)]" />
                        <span className="absolute right-0 bottom-0 h-2 w-2 rounded-full bg-[var(--soft-blue)]" />
                        <span className="absolute left-2 bottom-0 h-2 w-2 rounded-full bg-[var(--primary-navy)]" />
                      </div>
                    )}
                    {item.icon === "report" && <div className="h-6 w-5 rounded border border-[var(--primary-blue)] bg-[white]" />}
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">{item.step}</span>
                </div>

                <h3 className="mt-6 text-2xl font-semibold text-[var(--primary-navy)]">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-[var(--secondary-text)] sm:text-base">{item.description}</p>

                {index < howItWorks.length - 1 && (
                  <div className="mt-6 h-px w-full bg-[var(--light-border)]" />
                )}
              </div>
            ))}
          </div>
        </section>

        <section id="report-preview" className="mx-auto max-w-6xl py-2 pb-20">
          <div className="mb-8 max-w-2xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">Turn research into clarity</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-4xl">
              Competitive Research Report
            </h2>
            <p className="mt-3 text-base leading-7 text-[var(--secondary-text)]">
              Get a clear, structured report with everything you need to understand a company and its competitive landscape.
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-[0.88fr_1.12fr]">
            <div className="rounded-[28px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.7)] p-6 shadow-[0_14px_30px_rgba(19,48,95,0.04)]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--primary-blue)]">Checklist</p>
              <ul className="mt-5 space-y-3 text-sm text-[var(--primary-navy)]">
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
                  <li key={item} className="flex items-center gap-3 rounded-2xl border border-[var(--light-border)] bg-[var(--very-soft-blue)] px-3 py-2.5">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--primary-blue)] text-[10px] font-bold text-white">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="overflow-hidden rounded-[30px] border border-[var(--light-border)] bg-[var(--white)] shadow-[0_18px_30px_rgba(19,48,95,0.05)]">
              <div className="flex items-center justify-between border-b border-[var(--light-border)] bg-[var(--secondary-light-blue)] px-5 py-4">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--primary-blue)]">Competitive Research Report</p>
                  <h3 className="mt-2 text-xl font-semibold text-[var(--primary-navy)]">Notion</h3>
                </div>
                <div className="rounded-full border border-[var(--light-border)] bg-[var(--white)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--secondary-text)]">
                  Preview
                </div>
              </div>

              <div className="grid gap-4 p-4 lg:grid-cols-[1.05fr_1.35fr]">
                <div className="space-y-4">
                  <div className="rounded-2xl border border-[var(--light-border)] bg-[var(--very-soft-blue)] p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">Target company</p>
                    <p className="mt-2 text-sm font-medium text-[var(--primary-navy)]">Notion</p>
                  </div>

                  <div className="rounded-2xl border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">Competitor landscape</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full border border-[var(--light-border)] bg-[var(--white)] px-2.5 py-1.5 text-[var(--primary-navy)]">Slack</span>
                      <span className="rounded-full border border-[var(--light-border)] bg-[var(--white)] px-2.5 py-1.5 text-[var(--primary-navy)]">Coda</span>
                      <span className="rounded-full border border-[var(--light-border)] bg-[var(--white)] px-2.5 py-1.5 text-[var(--primary-navy)]">ClickUp</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {previewSections.map((section, index) => (
                    <div
                      key={section}
                      className={`rounded-2xl border p-4 transition hover:-translate-y-0.5 hover:shadow-[0_10px_22px_rgba(19,48,95,0.04)] ${
                        index % 2 === 0 ? "border-[var(--light-border)] bg-[var(--secondary-light-blue)]" : "border-[var(--soft-blue)] bg-[var(--very-soft-blue)]"
                      }`}
                    >
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--secondary-text)]">{section}</p>

                      {section === "Features" && (
                        <div className="mt-3 flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--primary-blue)]" />
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--soft-blue)]" />
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--soft-cyan)]" />
                          <span className="h-2.5 w-2.5 rounded-full bg-[var(--primary-navy)]/70" />
                        </div>
                      )}

                      {section === "Pricing" && (
                        <div className="mt-3 h-2.5 w-full rounded-full bg-[linear-gradient(90deg,#DCEAFF_0%,#DCEAFF_35%,#EDF4FF_35%,#EDF4FF_70%,#E3F8F5_70%,#E3F8F5_100%)]" />
                      )}

                      {section === "AI Insights" && (
                        <div className="mt-3 rounded-2xl border border-[var(--light-border)] bg-[var(--white)] p-2 text-[11px] leading-5 text-[var(--primary-navy)]">
                          Research-backed observations synthesized into a clear strategic narrative.
                        </div>
                      )}

                      {section === "Sources" && (
                        <div className="mt-3 flex items-center gap-2 text-[11px] text-[var(--secondary-text)]">
                          <span className="rounded-full bg-[var(--soft-blue)] px-2 py-1 text-[var(--primary-blue)]">Evidence</span>
                          <span>→</span>
                          <span className="rounded-full bg-[var(--soft-cyan)] px-2 py-1 text-[var(--primary-navy)]">Source</span>
                        </div>
                      )}

                      {section !== "Features" && section !== "Pricing" && section !== "AI Insights" && section !== "Sources" && (
                        <div className="mt-3 space-y-1 text-sm leading-6 text-[var(--secondary-text)]">
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
          <div className="rounded-[28px] border border-[var(--light-border)] bg-[var(--secondary-light-blue)] p-5 sm:p-6 lg:p-8">
            <div className="mb-6 flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">Research that shows its sources</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-4xl">
                  From sources to insights
                </h2>
              </div>
            </div>

            <p className="max-w-2xl text-base leading-7 text-[var(--secondary-text)]">
              Every insight is backed by real sources. You can trace information from the original source to the final insight.
            </p>

            <div className="mt-8 grid gap-4 md:grid-cols-4">
              {[
                { title: "Source", text: "Web pages, articles and reviews" },
                { title: "Evidence", text: "Key information extracted" },
                { title: "Finding", text: "Structured research data" },
                { title: "AI Insight", text: "Clear, easy-to-understand interpretation" },
              ].map((item, index) => (
                <div key={item.title} className="relative rounded-[24px] border border-[var(--light-border)] bg-[var(--white)] p-4">
                  <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-[var(--soft-blue)] text-[11px] font-bold text-[var(--primary-blue)]">
                    {index + 1}
                  </div>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">{item.title}</div>
                  <p className="mt-3 text-sm leading-6 text-[var(--secondary-text)]">{item.text}</p>
                  {index < 3 && <div className="mt-4 h-px w-full bg-[var(--light-border)]" />}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-5xl py-2 pb-20">
          <div className="rounded-[28px] border border-[var(--light-border)] bg-[var(--deep-navy)] p-6 text-white shadow-[0_18px_34px_rgba(11,35,72,0.14)] sm:p-8 lg:p-10">
            <div className="flex flex-col gap-6 text-center md:flex-row md:items-center md:justify-between md:text-left">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--soft-blue)]">Start here</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-white sm:text-4xl">
                  Start researching your competition.
                </h2>
                <p className="mt-3 text-base text-[var(--soft-blue)]">Enter a company name or website to get started.</p>
              </div>

              <a
                href="#research"
                className="inline-flex h-[52px] items-center justify-center rounded-2xl bg-white px-6 text-sm font-semibold text-[var(--deep-navy)] shadow-[0_12px_24px_rgba(255,255,255,0.12)] transition hover:-translate-y-0.5 hover:bg-[var(--soft-blue)]"
              >
                Start Research →
              </a>
            </div>
          </div>
        </section>

        <footer className="mx-auto max-w-6xl pb-10 pt-2 text-[var(--secondary-text)]">
          <div className="rounded-[26px] border border-[var(--light-border)] bg-[rgba(255,255,255,0.72)] px-4 py-6 sm:px-6 lg:px-8">
            <div className="grid gap-8 md:grid-cols-[1.3fr_1fr_1fr]">
              <div>
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[10px] font-semibold text-[var(--primary-blue)]">
                    AI
                  </div>
                  <span className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--primary-navy)]">AI Competitor Research</span>
                </div>
                <p className="mt-4 max-w-sm text-sm leading-7 text-[var(--secondary-text)]">
                  Research any company.
                  <span className="mt-1 block">Understand its competition.</span>
                </p>
              </div>

              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-navy)]">Product</p>
                <ul className="mt-3 space-y-2 text-sm">
                  <li>Research</li>
                  <li>Competitors</li>
                  <li>Reports</li>
                </ul>
              </div>

              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-navy)]">Project</p>
                <ul className="mt-3 space-y-2 text-sm">
                  <li>GitHub</li>
                  <li>About</li>
                </ul>
              </div>
            </div>

            <div className="mt-8 border-t border-[var(--light-border)] pt-5 text-xs uppercase tracking-[0.2em] text-[var(--secondary-text)]">
              © 2026 AI Competitor Research
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
