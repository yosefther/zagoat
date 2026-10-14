"use client";

import { useRef, type KeyboardEvent } from "react";

type Props = {
  files: string[];
  active: string;
  onSelect: (file: string) => void;
  panelId: string;
};

/** Tabs for multi-file tasks. Arrow keys, Home and End move between tabs. */
export function FileTabs({ files, active, onSelect, panelId }: Props) {
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const moves: Record<string, number> = {
      ArrowRight: (index + 1) % files.length,
      ArrowLeft: (index - 1 + files.length) % files.length,
      Home: 0,
      End: files.length - 1,
    };
    const next = moves[event.key];
    if (next === undefined) return;
    event.preventDefault();
    onSelect(files[next]);
    refs.current[files[next]]?.focus();
  }

  return (
    <div role="tablist" aria-label="Files" className="flex min-w-0 overflow-x-auto">
      {files.map((file, index) => {
        const selected = file === active;
        return (
          <button
            key={file}
            ref={(element) => {
              refs.current[file] = element;
            }}
            type="button"
            role="tab"
            id={`tab-${file}`}
            aria-selected={selected}
            aria-controls={panelId}
            tabIndex={selected ? 0 : -1}
            onClick={() => onSelect(file)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={`shrink-0 border-b-2 px-3 py-2 font-mono text-xs ${
              selected
                ? "border-accent-edge font-medium text-ink"
                : "border-transparent text-muted hover:text-ink"
            }`}
          >
            {file}
          </button>
        );
      })}
    </div>
  );
}
