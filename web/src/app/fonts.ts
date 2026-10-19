import { Bricolage_Grotesque, IBM_Plex_Sans, JetBrains_Mono } from "next/font/google";

// Headings and the hero: a grotesk with some character, to sit next to the faceted goat.
export const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-bricolage",
});

// Body and UI: calm for long reading.
export const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-sans",
});

// Code only: dotted zero and distinct 1/l/I.
export const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-jetbrains",
});
