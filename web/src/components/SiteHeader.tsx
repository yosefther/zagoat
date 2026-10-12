import Link from "next/link";

import { Wordmark } from "@/components/Wordmark";

const NAV_LINKS = [{ href: "/pricing", label: "Pricing" }];

export function SiteHeader() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="container-page flex h-16 items-center justify-between gap-4">
        <Wordmark />
        <nav aria-label="Main">
          <ul className="flex items-center gap-1 text-sm font-medium sm:gap-4">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="rounded-md px-2 py-1.5 text-ink no-underline hover:underline"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
