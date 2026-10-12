import Link from "next/link";

/**
 * Text wordmark until vector logo files land in /public/brand (see docs/design.md).
 * The lime tile with braces nods to the goat's curly-brace horns.
 */
export function Wordmark() {
  return (
    <Link
      href="/"
      className="inline-flex items-center gap-2 rounded-md text-ink no-underline"
      aria-label="zagoat home"
    >
      <span
        aria-hidden="true"
        className="grid size-7 place-items-center rounded-md bg-accent font-mono text-sm font-bold text-on-accent"
      >
        {"{}"}
      </span>
      <span className="font-display text-lg font-bold tracking-tight">zagoat</span>
    </Link>
  );
}
