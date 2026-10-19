"use client";

import { useEffect, useRef, useState } from "react";

const SHORTCUTS = [
  ["Ctrl/Cmd + Enter", "Run tests"],
  ["Ctrl/Cmd + Shift + Enter", "Submit solution"],
  ["Ctrl + M (Ctrl + Shift + M on Mac)", "Let Tab move focus out of the editor"],
];

/** The "?" menu listing keyboard shortcuts. */
export function ShortcutsHelp() {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !box.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div ref={box} className="relative">
      <button
        type="button"
        className="btn-quiet px-2.5 font-mono"
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label="Keyboard shortcuts"
        title="Keyboard shortcuts"
        onClick={() => setOpen(!open)}
      >
        ?
      </button>
      {open && (
        <div
          role="dialog"
          aria-label="Keyboard shortcuts"
          className="absolute right-0 z-40 mt-2 w-80 rounded-md bg-raised p-4 text-sm shadow-raised"
        >
          <h2 className="mb-2 text-base font-bold">Keyboard shortcuts</h2>
          <dl className="flex flex-col gap-2">
            {SHORTCUTS.map(([keys, action]) => (
              <div key={keys} className="flex flex-col">
                <dt className="font-mono text-xs text-brand-strong">{keys}</dt>
                <dd className="text-muted">{action}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
