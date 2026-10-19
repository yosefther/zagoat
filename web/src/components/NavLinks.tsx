"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Pricing hides on phones to keep the header on one line; the footer links to it too.
const NAV_LINKS = [
  { href: "/problems", label: "Problems", className: "" },
  { href: "/pricing", label: "Pricing", className: "hidden sm:inline-flex" },
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <>
      {NAV_LINKS.map((link) => {
        const current = pathname === link.href || pathname.startsWith(`${link.href}/`);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={current ? "page" : undefined}
            className={`btn-quiet px-2 sm:px-2.5 ${link.className} ${current ? "text-ink" : ""}`}
          >
            {link.label}
          </Link>
        );
      })}
    </>
  );
}
