"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

// three.js loads only in the browser, after the page is interactive.
const HeroScene = dynamic(() => import("@/components/hero/HeroScene"), { ssr: false });

const MIN_LIVE_WIDTH = 768;

function canRunScene(): boolean {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return false;
  if (window.innerWidth < MIN_LIVE_WIDTH) return false;
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

/**
 * The landing page's one bold element. Shows a static render first (fast, and the
 * fallback for reduced motion, missing WebGL and phones), then swaps in the live scene,
 * which pauses whenever it's off-screen or the tab is hidden.
 */
export function HeroVisual() {
  const box = useRef<HTMLDivElement>(null);
  const [live, setLive] = useState(false);
  const [visible, setVisible] = useState(true);
  const [tabVisible, setTabVisible] = useState(true);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).has("static-hero")) return;
    const start = () => setLive(canRunScene());
    const idle = window.requestIdleCallback?.(start, { timeout: 1500 });
    const timer = idle === undefined ? window.setTimeout(start, 300) : undefined;
    return () => {
      if (idle !== undefined) window.cancelIdleCallback(idle);
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, []);

  useEffect(() => {
    if (!live || !box.current) return;
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), {
      threshold: 0.05,
    });
    observer.observe(box.current);
    const onVisibility = () => setTabVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [live]);

  const active = visible && tabVisible;
  return (
    <div
      ref={box}
      className="hero-fade relative h-full w-full"
      data-hero-mode={live ? "live" : "static"}
      data-hero-active={live && active ? "true" : "false"}
    >
      {live ? (
        <HeroScene active={active} />
      ) : (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element -- static render, sized by CSS */}
          <img
            src="/brand/hero-static-dark.png"
            alt=""
            className="absolute inset-0 h-full w-full object-cover object-[64%_100%] lg:object-contain lg:object-[100%_100%] light:hidden"
            fetchPriority="high"
          />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/brand/hero-static-light.png"
            alt=""
            className="absolute inset-0 hidden h-full w-full object-cover object-[64%_100%] lg:object-contain lg:object-[100%_100%] light:block"
          />
        </>
      )}
    </div>
  );
}
