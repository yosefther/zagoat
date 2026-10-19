import Link from "next/link";

import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="container-page flex flex-1 flex-col items-start justify-center gap-4 py-24">
        <p className="font-mono text-sm text-muted">404</p>
        <h1 className="text-3xl font-bold">We couldn&apos;t find that page</h1>
        <p className="max-w-[var(--measure)] text-muted">
          The link may be old, or the page may have moved. Check the address, or browse the
          problem list.
        </p>
        <div className="flex gap-3">
          <Link href="/problems" className="btn-primary">
            Browse problems
          </Link>
          <Link href="/" className="btn-secondary">
            Go to the home page
          </Link>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
