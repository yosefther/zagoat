import type { Metadata, Viewport } from "next";

import { barlow, barlowCondensed, martianMono } from "@/app/fonts";
import { SessionProvider } from "@/lib/session";
import { DEFAULT_THEME, THEME_BOOT_SCRIPT } from "@/lib/theme";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "zagoat · Practice the real tasks AI interviews give you",
    template: "%s · zagoat",
  },
  description:
    "Realistic 30–60 minute AI engineering tasks: fix a RAG pipeline, debug training code, " +
    "write evals. Graded by hidden tests and metrics.",
  icons: {
    icon: [
      { url: "/brand/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/brand/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/brand/favicon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/brand/favicon-180.png", sizes: "180x180", type: "image/png" }],
  },
};

export const viewport: Viewport = {
  themeColor: [{ color: "#1b1e33" }],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-theme={DEFAULT_THEME}
      className={`${barlowCondensed.variable} ${barlow.variable} ${martianMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT_SCRIPT }} />
      </head>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only bg-brand px-3 py-2 text-on-brand focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50"
        >
          Skip to main content
        </a>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
