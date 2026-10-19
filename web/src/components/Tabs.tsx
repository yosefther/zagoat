"use client";

import { useRef, type KeyboardEvent } from "react";

export type Tab = { id: string; label: string };

type Props = {
  tabs: Tab[];
  active: string;
  onSelect: (id: string) => void;
  /** Prefix for the tab and panel ids, unique on the page. */
  idPrefix: string;
  label: string;
  mono?: boolean;
};

export function tabId(prefix: string, id: string) {
  return `${prefix}-tab-${id.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
}

export function panelId(prefix: string) {
  return `${prefix}-panel`;
}

/** Accessible tabs: arrow keys, Home and End move between them. */
export function Tabs({ tabs, active, onSelect, idPrefix, label, mono = false }: Props) {
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const moves: Record<string, number> = {
      ArrowRight: (index + 1) % tabs.length,
      ArrowLeft: (index - 1 + tabs.length) % tabs.length,
      Home: 0,
      End: tabs.length - 1,
    };
    const next = moves[event.key];
    if (next === undefined) return;
    event.preventDefault();
    onSelect(tabs[next].id);
    refs.current[tabs[next].id]?.focus();
  }

  return (
    <div role="tablist" aria-label={label} className="flex min-w-0 overflow-x-auto">
      {tabs.map((tab, index) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            ref={(element) => {
              refs.current[tab.id] = element;
            }}
            type="button"
            role="tab"
            id={tabId(idPrefix, tab.id)}
            aria-selected={selected}
            aria-controls={panelId(idPrefix)}
            tabIndex={selected ? 0 : -1}
            onClick={() => onSelect(tab.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={`shrink-0 border-b-2 px-3 py-2 text-sm ${mono ? "font-mono text-xs" : ""} ${
              selected
                ? "border-brand font-medium text-ink"
                : "border-transparent text-muted hover:text-ink"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
