import Image from "next/image";
import Link from "next/link";

/** The zagoat logo, used as-is (never recolored or redrawn), next to the lowercase name. */
export function Logo({ size = 28, withName = true }: { size?: number; withName?: boolean }) {
  return (
    <Link
      href="/"
      className="inline-flex shrink-0 items-center gap-2 rounded-sm text-ink no-underline"
      aria-label="zagoat home"
    >
      <Image src="/brand/logo-128.png" alt="" width={size} height={size} priority />
      {withName && <span className="font-heading text-lg font-bold">zagoat</span>}
    </Link>
  );
}
