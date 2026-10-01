"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { CompanyInfoSection } from "@/components/research/CompanyInfoSection";
import { CompanyOverview } from "@/components/research/CompanyOverview";
import type { CompanyProfile } from "@/types/company";
import { getApiErrorMessage, toCompanyProfile, understandCompany } from "@/lib/api";

function CompanyContent() {
  const searchParams = useSearchParams();
  const companyQuery = searchParams.get("company")?.trim() ?? "";
  const researchId = searchParams.get("research_id")?.trim() ?? "";
  const [company, setCompany] = useState<CompanyProfile | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(researchId));
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!researchId) {
      setCompany(null);
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    const loadCompanyProfile = async () => {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const understandResponse = await understandCompany(researchId);
        const profile = toCompanyProfile(understandResponse.company_research);

        if (!isMounted) {
          return;
        }

        setCompany(profile);
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setCompany(null);
        setErrorMessage(getApiErrorMessage(error, "The company understanding is unavailable from the backend right now."));
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void loadCompanyProfile();

    return () => {
      isMounted = false;
    };
  }, [researchId]);

  if (!companyQuery && !researchId) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <header className="mb-6 flex items-center justify-between rounded-full border border-[#DCE6F5] bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(16,42,86,0.04)] backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#EAF2FF] bg-[#F3F7FF] text-[10px] font-semibold text-[#326FEA]">AI</div>
              <span className="text-sm font-semibold tracking-[0.16em] text-[#102A56] uppercase">AI Competitor Research</span>
            </div>
            <Link href="/" className="text-sm font-medium text-[#52627A] transition hover:text-[#326FEA]">Back to Home</Link>
          </header>

          <section className="rounded-[28px] border border-[#DCE6F5] bg-white p-6 shadow-[0_18px_34px_rgba(16,42,86,0.04)] sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#326FEA]">COMPANY UNDERSTANDING</p>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">Which company should we research?</h1>
            <p className="mt-4 text-base leading-7 text-[#52627A]">A company name or website URL is required to view the company understanding page.</p>

            <Link href="/" className="mt-6 inline-flex h-[52px] items-center justify-center rounded-2xl bg-[#326FEA] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25">Return to home</Link>
          </section>
        </div>
      </main>
    );
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-8 shadow-[0_20px_40px_rgba(16,42,86,0.06)]">
            <p className="text-sm text-[#52627A]">Loading live company understanding from the backend...</p>
          </div>
        </div>
      </main>
    );
  }

  if (!company) {
    return (
      <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="rounded-[28px] border border-[#DCE6F5] bg-white p-6 shadow-[0_18px_34px_rgba(16,42,86,0.04)] sm:p-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#326FEA]">COMPANY UNDERSTANDING</p>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-[#102A56] sm:text-4xl">Company profile unavailable</h1>
            <p className="mt-4 text-base leading-7 text-[#52627A]">
              {errorMessage || `The backend has not produced a company profile for ${companyQuery || "this run"} yet.`}
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/" className="inline-flex h-[52px] items-center justify-center rounded-2xl bg-[#326FEA] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[#245CCB] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/25">Return to home</Link>
              {companyQuery ? (
                <Link href={`/research/progress?company=${encodeURIComponent(companyQuery)}&research_id=${encodeURIComponent(researchId)}`} className="inline-flex h-[52px] items-center justify-center rounded-2xl border border-[#DCE6F5] bg-white px-5 text-sm font-semibold text-[#102A56] transition hover:border-[#326FEA]/30 hover:text-[#326FEA] focus:outline-none focus:ring-2 focus:ring-[#326FEA]/20">← Back to Research Progress</Link>
              ) : null}
            </div>
          </section>
        </div>
      </main>
    );
  }

  const initials = company.name.slice(0, 2).toUpperCase();

  return (
    <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex items-center justify-between rounded-full border border-[#DCE6F5] bg-white/80 px-4 py-3 shadow-[0_10px_24px_rgba(16,42,86,0.04)] backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#EAF2FF] bg-[#F3F7FF] text-[10px] font-semibold text-[#326FEA]">AI</div>
            <span className="text-sm font-semibold tracking-[0.16em] text-[#102A56] uppercase">AI Competitor Research</span>
          </div>

          <div className="hidden items-center gap-4 sm:flex">
            <Link href={`/research/progress?company=${encodeURIComponent(companyQuery || company.name)}&research_id=${encodeURIComponent(researchId)}`} className="text-sm font-medium text-[#52627A] transition hover:text-[#326FEA]">← Research Progress</Link>
          </div>
        </header>

        <section className="overflow-hidden rounded-[32px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] shadow-[0_24px_60px_rgba(16,42,86,0.08)]">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#326FEA]">Company Understanding</p>
                <h1 className="mt-3 break-words text-3xl font-semibold tracking-[-0.06em] text-[#102A56] sm:text-4xl lg:text-[3rem]">{company.name}</h1>
                <p className="mt-4 max-w-xl text-base leading-7 text-[#52627A]">{company.overview}</p>

                <div className="mt-6 flex flex-wrap gap-3">
                  <span className="rounded-full border border-[#DCE6F5] bg-white px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#52627A]">{company.industry}</span>
                  <span className="rounded-full border border-[#EAF2FF] bg-[#F3F7FF] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#326FEA]">Research foundation</span>
                </div>
              </div>

              <div className="rounded-[28px] border border-[#DCE6F5] bg-white p-5 shadow-[0_18px_36px_rgba(16,42,86,0.04)] sm:p-6">
                <div className="flex items-center justify-between gap-3 pb-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-[#EAF2FF] bg-[#F3F7FF] text-2xl font-semibold text-[#326FEA]">{initials}</div>
                  <span className="rounded-full border border-[#EAF2FF] bg-[#F3F7FF] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#326FEA]">Company profile</span>
                </div>

                <div className="space-y-3">
                  <div className="rounded-2xl border border-[#DCE6F5] bg-[#F3F7FF] p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#52627A]">Company</p>
                    <p className="mt-2 text-base font-semibold text-[#102A56]">{company.name}</p>
                  </div>
                  <div className="rounded-2xl border border-[#DCE6F5] bg-white p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#52627A]">Industry</p>
                    <p className="mt-2 text-sm text-[#102A56]">{company.industry}</p>
                  </div>
                  <div className="rounded-2xl border border-[#DCE6F5] bg-white p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#52627A]">Understanding</p>
                    <p className="mt-2 text-sm text-[#102A56]">Business model, market position, and audience fit</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 grid gap-5 lg:grid-cols-3">
              <CompanyInfoSection title="Products">
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {company.products.map((product) => (
                    <li key={product.name} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      <div className="font-semibold text-[#102A56]">{product.name}</div>
                      <div className="mt-1 text-sm text-[#52627A]">{product.summary}</div>
                    </li>
                  ))}
                </ul>
              </CompanyInfoSection>

              <CompanyInfoSection title="Audience">
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {company.audience.map((item) => (
                    <li key={item.label} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      <div className="font-semibold text-[#102A56]">{item.label}</div>
                      <div className="mt-1 text-sm text-[#52627A]">{item.description}</div>
                    </li>
                  ))}
                </ul>
              </CompanyInfoSection>

              <CompanyInfoSection title="Context">
                <ul className="space-y-3 text-sm leading-7 text-[#52627A] sm:text-base">
                  {company.context.map((item) => (
                    <li key={item.label} className="rounded-2xl border border-[#DCE6F5] bg-white p-3.5">
                      <div className="font-semibold text-[#102A56]">{item.label}</div>
                      <div className="mt-1 text-sm text-[#52627A]">{item.description}</div>
                    </li>
                  ))}
                </ul>
              </CompanyInfoSection>
            </div>

            <div className="mt-8">
              <CompanyOverview company={company} />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export default function CompanyPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#F7FAFF] text-[#102A56]">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
            <div className="rounded-[28px] border border-[#DCE6F5] bg-[linear-gradient(180deg,#FFFFFF_0%,#F7FAFF_100%)] p-8 shadow-[0_20px_40px_rgba(16,42,86,0.06)]">
              <p className="text-sm text-[#52627A]">Loading company understanding...</p>
            </div>
          </div>
        </main>
      }
    >
      <CompanyContent />
    </Suspense>
  );
}
