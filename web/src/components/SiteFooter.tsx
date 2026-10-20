import Link from "next/link";

import { Logo } from "@/components/Logo";

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-line">
      <div className="container-page flex flex-col gap-4 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <Logo size={22} />
        <nav aria-label="Legal">
          <ul className="flex flex-wrap items-center gap-5">
            <li>
              <Link href="/tasks" className="text-muted hover:text-ink">Tasks</Link>
            </li>
            <li>
              <Link href="/pricing" className="text-muted hover:text-ink">Pricing</Link>
            </li>
            <li>
              <Link href="/privacy" className="text-muted hover:text-ink">Privacy</Link>
            </li>
            <li>
              <Link href="/terms" className="text-muted hover:text-ink">Terms</Link>
            </li>
          </ul>
        </nav>
      </div>
    </footer>
  );
}
