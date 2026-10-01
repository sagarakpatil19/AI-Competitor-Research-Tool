"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

type FormErrors = Partial<Record<"name" | "email" | "password" | "confirmPassword", string>>;

export default function SignupPage() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});

  const handleChange = (field: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors: FormErrors = {};
    const name = form.name.trim();
    const email = form.email.trim();
    const password = form.password;
    const confirmPassword = form.confirmPassword;

    if (!name) {
      nextErrors.name = "Name is required.";
    }

    if (!email) {
      nextErrors.email = "Email is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = "Enter a valid email address.";
    }

    if (!password) {
      nextErrors.password = "Password is required.";
    }

    if (!confirmPassword) {
      nextErrors.confirmPassword = "Please confirm your password.";
    } else if (password && confirmPassword !== password) {
      nextErrors.confirmPassword = "Passwords do not match.";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }
  };

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--primary-navy)]">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-6 flex items-center justify-between rounded-full border border-[var(--light-border)] bg-[rgba(255,255,255,0.75)] px-4 py-3 shadow-[0_10px_24px_rgba(19,48,95,0.04)] backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] text-[10px] font-semibold text-[var(--primary-blue)]">
              AI
            </div>
            <span className="text-sm font-semibold uppercase tracking-[0.16em] text-[var(--primary-navy)]">
              AI Competitor Research
            </span>
          </div>

          <Link href="/" className="text-sm font-medium text-[var(--secondary-text)] transition hover:text-[var(--primary-blue)]">
            Back to Home
          </Link>
        </header>

        <section className="mx-auto max-w-md rounded-[30px] border border-[var(--light-border)] bg-[linear-gradient(180deg,#FFFFFF_0%,#F5F9FF_100%)] p-6 shadow-[0_24px_60px_rgba(19,48,95,0.06)] sm:p-8">
          <div className="mb-6 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--primary-blue)]">
              Create account
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.06em] text-[var(--primary-navy)]">
              Sign up
            </h1>
          </div>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label htmlFor="name" className="mb-2 block text-sm font-medium text-[var(--primary-navy)]">
                Name
              </label>
              <input
                id="name"
                type="text"
                value={form.name}
                onChange={(event) => handleChange("name", event.target.value)}
                placeholder="Your full name"
                className="h-[52px] w-full rounded-2xl border border-[var(--soft-blue)] bg-[var(--white)] px-4 text-base text-[var(--primary-navy)] placeholder:text-[var(--secondary-text)] shadow-[0_10px_24px_rgba(50,111,234,0.06)] transition focus:border-[var(--primary-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/20"
                aria-invalid={Boolean(errors.name)}
              />
              {errors.name && <p className="mt-2 text-sm text-[var(--primary-blue)]">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="signup-email" className="mb-2 block text-sm font-medium text-[var(--primary-navy)]">
                Email
              </label>
              <input
                id="signup-email"
                type="email"
                value={form.email}
                onChange={(event) => handleChange("email", event.target.value)}
                placeholder="you@example.com"
                className="h-[52px] w-full rounded-2xl border border-[var(--soft-blue)] bg-[var(--white)] px-4 text-base text-[var(--primary-navy)] placeholder:text-[var(--secondary-text)] shadow-[0_10px_24px_rgba(50,111,234,0.06)] transition focus:border-[var(--primary-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/20"
                aria-invalid={Boolean(errors.email)}
              />
              {errors.email && <p className="mt-2 text-sm text-[var(--primary-blue)]">{errors.email}</p>}
            </div>

            <div>
              <label htmlFor="signup-password" className="mb-2 block text-sm font-medium text-[var(--primary-navy)]">
                Password
              </label>
              <input
                id="signup-password"
                type="password"
                value={form.password}
                onChange={(event) => handleChange("password", event.target.value)}
                placeholder="Create a password"
                className="h-[52px] w-full rounded-2xl border border-[var(--soft-blue)] bg-[var(--white)] px-4 text-base text-[var(--primary-navy)] placeholder:text-[var(--secondary-text)] shadow-[0_10px_24px_rgba(50,111,234,0.06)] transition focus:border-[var(--primary-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/20"
                aria-invalid={Boolean(errors.password)}
              />
              {errors.password && <p className="mt-2 text-sm text-[var(--primary-blue)]">{errors.password}</p>}
            </div>

            <div>
              <label htmlFor="confirm-password" className="mb-2 block text-sm font-medium text-[var(--primary-navy)]">
                Confirm password
              </label>
              <input
                id="confirm-password"
                type="password"
                value={form.confirmPassword}
                onChange={(event) => handleChange("confirmPassword", event.target.value)}
                placeholder="Re-enter your password"
                className="h-[52px] w-full rounded-2xl border border-[var(--soft-blue)] bg-[var(--white)] px-4 text-base text-[var(--primary-navy)] placeholder:text-[var(--secondary-text)] shadow-[0_10px_24px_rgba(50,111,234,0.06)] transition focus:border-[var(--primary-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/20"
                aria-invalid={Boolean(errors.confirmPassword)}
              />
              {errors.confirmPassword && (
                <p className="mt-2 text-sm text-[var(--primary-blue)]">{errors.confirmPassword}</p>
              )}
            </div>

            <button
              type="submit"
              className="inline-flex h-[52px] w-full items-center justify-center rounded-2xl bg-[var(--primary-blue)] px-5 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(50,111,234,0.2)] transition hover:-translate-y-0.5 hover:bg-[var(--blue-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/25"
            >
              Sign Up
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[var(--secondary-text)]">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-[var(--primary-blue)] transition hover:text-[var(--blue-hover)]">
              Login
            </Link>
          </p>
        </section>
      </div>
    </main>
  );
}
