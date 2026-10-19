import { Suspense } from "react";

import { Logo } from "@/components/Logo";
import { NavLinks } from "@/components/NavLinks";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UserMenu } from "@/components/UserMenu";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-page/95 backdrop-blur">
      <div className="container-page flex h-[var(--header-height)] items-center gap-3 sm:gap-6">
        <Logo />
        <nav aria-label="Main" className="flex flex-1 items-center text-sm sm:gap-1">
          <Suspense fallback={null}>
            <NavLinks />
          </Suspense>
        </nav>
        <div className="flex items-center gap-1 sm:gap-2">
          <ThemeToggle />
          {/* The menu reads the current path, which dynamic routes only know at request time. */}
          <Suspense fallback={<span className="inline-block h-9 w-16" aria-hidden="true" />}>
            <UserMenu />
          </Suspense>
        </div>
      </div>
    </header>
  );
}
