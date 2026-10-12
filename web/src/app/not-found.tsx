import Link from "next/link";

export default function NotFound() {
  return (
    <main className="container-page flex flex-1 flex-col items-start justify-center gap-4 py-24">
      <p className="font-mono text-sm text-muted">404</p>
      <h1 className="text-3xl font-bold">We couldn&apos;t find that page</h1>
      <p className="max-w-prose text-muted">
        The link may be old, or the page may have moved. Check the address or start from the
        home page.
      </p>
      <Link href="/" className="btn-primary no-underline">
        Go to the home page
      </Link>
    </main>
  );
}
