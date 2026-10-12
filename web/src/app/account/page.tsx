import type { Metadata } from "next";

import { AccountPanel } from "@/app/account/AccountPanel";

export const metadata: Metadata = { title: "Account" };

export default function AccountPage() {
  return (
    <main className="container-page flex flex-1 flex-col gap-8 py-16">
      <h1 className="text-3xl font-bold">Account</h1>
      <AccountPanel />
    </main>
  );
}
