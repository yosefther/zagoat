import { Barlow, Barlow_Condensed, Martian_Mono } from "next/font/google";

// Headlines: condensed, from highway and trail signage. Set large and tight.
export const barlowCondensed = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-barlow-condensed",
});

// Body and UI, from the same superfamily.
export const barlow = Barlow({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-barlow",
});

// Code only.
export const martianMono = Martian_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-martian",
});
