import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "zagoat",
  description: "Practice the real tasks AI interviews give you.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
