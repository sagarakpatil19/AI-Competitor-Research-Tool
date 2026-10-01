"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const MOCK_AUTH_KEY = "ai_competitor_research_mock_auth";

function isMockAuthenticated() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.localStorage.getItem(MOCK_AUTH_KEY) === "true";
}

export default function HistoryPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isMockAuthenticated()) {
      router.replace("/login");
    }
  }, [router]);

  if (!isMockAuthenticated()) {
    return null;
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-4 py-10 text-[var(--primary-navy)] sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">Research History</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[var(--primary-navy)] sm:text-4xl">
              Research History
            </h1>
          </div>

          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-[var(--light-border)] bg-[var(--white)] px-4 py-2 text-sm font-medium text-[var(--primary-navy)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
          >
            Back to home
          </Link>
        </div>

        <div className="rounded-[28px] border border-[var(--light-border)] bg-[var(--white)] p-6 shadow-[0_18px_32px_rgba(19,48,95,0.06)] sm:p-8">
          <div className="space-y-4 text-[var(--secondary-text)]">
            <p className="text-lg font-medium text-[var(--primary-navy)]">Your completed research will appear here.</p>
            <p className="text-base leading-7">No research history yet.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
