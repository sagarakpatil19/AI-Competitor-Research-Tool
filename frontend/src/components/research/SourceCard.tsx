import type { Source } from "@/types/source";

export function SourceCard({ source }: { source: Source }) {
  const metadata = [
    source.type ? `Type: ${source.type}` : null,
    source.publisher ? `Publisher: ${source.publisher}` : null,
    source.accessedAt ? `Accessed: ${source.accessedAt}` : null,
  ].filter(Boolean) as string[];

  return (
    <div className="rounded-2xl border border-[var(--light-border)] bg-white p-3.5 shadow-[0_12px_24px_rgba(19,48,95,0.03)]">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-[var(--primary-navy)]">
          {source.title || "Mock source"}
        </p>
        <span className="rounded-full border border-[var(--soft-blue)] bg-[var(--secondary-light-blue)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
          Mock source
        </span>
      </div>

      {metadata.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs leading-6 text-[var(--secondary-text)] sm:text-sm">
          {metadata.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}

      {source.url && (
        <a
          href={source.url}
          target="_blank"
          rel="noreferrer noopener"
          className="mt-3 inline-flex items-center text-sm font-medium text-[var(--primary-blue)] underline decoration-[var(--primary-blue)]/60 underline-offset-4 transition hover:text-[var(--blue-hover)]"
        >
          View placeholder source link
        </a>
      )}
    </div>
  );
}
