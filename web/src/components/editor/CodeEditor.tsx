"use client";

import Editor, { loader, type BeforeMount, type OnMount } from "@monaco-editor/react";

import { config } from "@/config";
import { useResolvedTheme } from "@/lib/useResolvedTheme";

loader.config({ paths: { vs: config.monacoBaseUrl } });

// Editor colours from the design tokens (docs/design.md).
const defineThemes: BeforeMount = (monaco) => {
  monaco.editor.defineTheme("zagoat-light", {
    base: "vs",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#ffffff",
      "editorLineNumber.foreground": "#8b88ae",
      "editor.selectionBackground": "#dddbea",
      "editorCursor.foreground": "#1e1b4b",
    },
  });
  monaco.editor.defineTheme("zagoat-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#1c1a40",
      "editorLineNumber.foreground": "#6e6a9c",
      "editor.selectionBackground": "#34315e",
      "editorCursor.foreground": "#a3e635",
    },
  });
};

type Props = {
  path: string;
  value: string;
  readOnly?: boolean;
  onChange?: (value: string) => void;
  onMount?: OnMount;
  label: string;
};

/**
 * Monaco for one file. Each `path` keeps its own model, so undo history is per file.
 *
 * The editor is uncontrolled: `value` only seeds a new model. Feeding every keystroke back in
 * as a prop races with typing and drops characters, so programmatic changes go through the
 * editor instance from `onMount` instead.
 */
export function CodeEditor({ path, value, readOnly = false, onChange, onMount, label }: Props) {
  const theme = useResolvedTheme();
  return (
    <Editor
      path={path}
      defaultValue={value}
      defaultLanguage={path.endsWith(".py") ? "python" : undefined}
      theme={theme === "dark" ? "zagoat-dark" : "zagoat-light"}
      beforeMount={defineThemes}
      onMount={onMount}
      onChange={(next) => onChange?.(next ?? "")}
      loading={<p className="p-4 text-sm text-muted">Loading the editor…</p>}
      options={{
        readOnly,
        ariaLabel: label,
        fontFamily: "var(--font-plex-mono), ui-monospace, monospace",
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        tabSize: 4,
        insertSpaces: true,
        automaticLayout: true,
        renderWhitespace: "boundary",
        accessibilitySupport: "auto",
      }}
    />
  );
}
