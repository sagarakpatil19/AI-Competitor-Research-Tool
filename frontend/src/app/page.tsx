"use client";

import { useEffect, useState } from "react";

type HealthState = "checking" | "connected" | "offline";

export default function Home() {
  const [healthState, setHealthState] = useState<HealthState>("checking");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

    fetch(`${apiUrl}/api/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Health check failed");
        }
        setHealthState("connected");
      })
      .catch(() => setHealthState("offline"));
  }, []);

  const healthLabel = {
    checking: "Checking API",
    connected: "API connected",
    offline: "API offline",
  }[healthState];

  return (
    <div className="min-h-screen bg-[var(--ink)] text-[var(--paper)]">
      <header className="border-b border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-lg bg-[var(--coral)] text-lg font-bold text-[var(--ink)]">R</span>
            <span className="text-sm font-semibold tracking-[0.2em] text-white">RESEARCH / ROOM</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
            <span className={`size-2 rounded-full ${healthState === "connected" ? "bg-[var(--mint)]" : healthState === "offline" ? "bg-[var(--coral)]" : "animate-pulse bg-[var(--gold)]"}`} />
            {healthLabel}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-16 lg:px-10 lg:py-24">
        <section className="grid gap-14 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <p className="mb-6 text-xs font-semibold uppercase tracking-[0.28em] text-[var(--coral)]">Competitive intelligence, without the noise</p>
            <h1 className="max-w-4xl text-5xl font-semibold leading-[0.98] tracking-[-0.04em] text-white sm:text-7xl">See the market clearly.</h1>
            <p className="mt-8 max-w-xl text-lg leading-8 text-[var(--muted)]">A focused workspace for turning public signals into decisions your team can act on.</p>
            <button className="mt-10 rounded-md bg-[var(--coral)] px-6 py-3 text-sm font-semibold text-[var(--ink)] transition-transform hover:-translate-y-0.5">Create your first project</button>
          </div>
          <div className="border-l border-white/10 pl-8 lg:mb-2">
            <p className="text-6xl font-semibold tracking-[-0.05em] text-[var(--gold)]">01</p>
            <p className="mt-4 max-w-xs text-sm leading-6 text-[var(--muted)]">Your research command center is ready. Add a company and its competitors to begin building a living market view.</p>
          </div>
        </section>

        <section className="mt-24 grid gap-px overflow-hidden rounded-lg border border-white/10 bg-white/10 sm:grid-cols-3">
          {["Projects", "Competitors", "Evidence"].map((label, index) => (
            <div className="bg-[var(--panel)] p-6" key={label}>
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">{label}</p>
              <p className="mt-8 text-4xl font-semibold text-white">{index === 0 ? "0" : "--"}</p>
              <p className="mt-2 text-sm text-[var(--muted)]">Ready to be explored</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
