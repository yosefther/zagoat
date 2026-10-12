import Link from "next/link";

import { ThemeToggle } from "@/components/ThemeToggle";

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border">
      <div className="container-page flex flex-col gap-4 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <nav aria-label="Legal">
          <ul className="flex flex-wrap items-center gap-4">
            <li>© zagoat</li>
            <li>
              <Link href="/privacy">Privacy</Link>
            </li>
            <li>
              <Link href="/terms">Terms</Link>
            </li>
          </ul>
        </nav>
        <ThemeToggle />
      </div>
    </footer>
  );
}
