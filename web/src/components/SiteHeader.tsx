import Link from "next/link";
import { Suspense } from "react";

import { UserMenu } from "@/components/UserMenu";
import { Wordmark } from "@/components/Wordmark";

const NAV_LINKS = [
  { href: "/problems", label: "Problems" },
  { href: "/pricing", label: "Pricing" },
];

export function SiteHeader() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="container-page flex h-16 items-center justify-between gap-4">
        <Wordmark />
        <nav aria-label="Main" className="flex items-center gap-2 sm:gap-4">
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
          {/* The menu reads the current path, which dynamic routes only know at request time. */}
          <Suspense fallback={<span className="inline-block h-9 w-20" aria-hidden="true" />}>
            <UserMenu />
          </Suspense>
        </nav>
      </div>
    </header>
  );
}
