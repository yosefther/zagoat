"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useRef } from "react";

import { useSession } from "@/lib/session";

export function UserMenu() {
  const session = useSession();
  const pathname = usePathname();
  const router = useRouter();
  const menu = useRef<HTMLDetailsElement>(null);

  if (session.status === "loading") {
    return <span className="inline-block h-9 w-20" aria-hidden="true" />;
  }

  if (session.status === "signed_out") {
    const params = new URLSearchParams({ return_to: pathname });
    return (
      <Link href={`/signin?${params}`} className="btn-secondary py-1.5 text-sm">
        Sign in
      </Link>
    );
  }

  const { user } = session;
  const label = user.name ?? user.email;

  async function onSignOut() {
    menu.current?.removeAttribute("open");
    await session.signOut();
    router.push("/");
  }

  return (
    <details ref={menu} className="relative">
      <summary
        className="flex cursor-pointer list-none items-center gap-2 rounded-full p-0.5 text-sm"
        aria-label={`Account menu for ${label}`}
      >
        {user.avatar_url ? (
          <Image
            src={user.avatar_url}
            alt=""
            width={32}
            height={32}
            unoptimized
            className="size-8 rounded-full border border-border"
          />
        ) : (
          <span
            aria-hidden="true"
            className="grid size-8 place-items-center rounded-full bg-code font-medium"
          >
            {label.slice(0, 1).toUpperCase()}
          </span>
        )}
      </summary>
      <div className="card absolute right-0 z-20 mt-2 flex w-56 flex-col p-1 text-sm shadow-lg">
        <p className="truncate px-3 py-2 text-muted">{user.email}</p>
        <Link
          href="/account"
          className="rounded-md px-3 py-2 text-ink no-underline hover:bg-code"
          onClick={() => menu.current?.removeAttribute("open")}
        >
          Account
        </Link>
        <button
          type="button"
          onClick={onSignOut}
          className="rounded-md px-3 py-2 text-left hover:bg-code"
        >
          Sign out
        </button>
      </div>
    </details>
  );
}
