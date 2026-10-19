"use client";

import Editor, { loader, useMonaco, type BeforeMount, type OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { useEffect, useRef } from "react";

import { config } from "@/config";
import { useResolvedTheme } from "@/lib/useResolvedTheme";

loader.config({ paths: { vs: config.monacoBaseUrl } });

const THEME = "zagoat";

/** Monaco only accepts #rrggbb; the CSS minifier may shorten tokens to #rgb. */
export function toHex6(value: string): string {
  const hex = value.trim().replace("#", "");
  if (/^[0-9a-f]{3}$/i.test(hex)) {
    return `#${[...hex].map((digit) => digit + digit).join("")}`.toLowerCase();
  }
  return `#${hex}`.toLowerCase();
}

/** The editor theme, built from the design tokens currently on <html>. */
function themeFromTokens(): editor.IStandaloneThemeData {
  const css = getComputedStyle(document.documentElement);
  const token = (name: string) => toHex6(css.getPropertyValue(name));
  const bare = (name: string) => token(name).replace("#", "");
  const light = document.documentElement.getAttribute("data-theme") === "light";
  return {
    base: light ? "vs" : "vs-dark",
    inherit: true,
    rules: [
      { token: "", foreground: bare("--ink") },
      { token: "keyword", foreground: bare("--code-keyword") },
      { token: "string", foreground: bare("--code-string") },
      { token: "number", foreground: bare("--code-number") },
      { token: "comment", foreground: bare("--code-comment"), fontStyle: "italic" },
      { token: "type", foreground: bare("--code-function") },
      { token: "delimiter", foreground: bare("--muted") },
    ],
    colors: {
      "editor.background": token("--panel"),
      "editor.foreground": token("--ink"),
      "editorLineNumber.foreground": token("--field"),
      "editorLineNumber.activeForeground": token("--ink"),
      "editor.lineHighlightBackground": token("--raised"),
      "editor.lineHighlightBorder": token("--raised"),
      "editor.selectionBackground": token("--code-selection"),
      "editorCursor.foreground": token("--brand-strong"),
      "editorIndentGuide.background1": token("--line"),
      "editorWhitespace.foreground": token("--line"),
      "editorWidget.background": token("--raised"),
      "editorWidget.border": token("--line"),
      "editorSuggestWidget.background": token("--raised"),
      "editorSuggestWidget.selectedBackground": token("--code-selection"),
      "scrollbarSlider.background": `${token("--field")}55`,
      "scrollbarSlider.hoverBackground": `${token("--field")}88`,
      focusBorder: token("--focus"),
    },
  };
}

const defineTheme: BeforeMount = (monaco) => {
  monaco.editor.defineTheme(THEME, themeFromTokens());
};

type Props = {
  path: string;
  value: string;
  readOnly?: boolean;
  onChange?: (value: string) => void;
  onMount?: OnMount;
  /** Ctrl/Cmd+Enter and Ctrl/Cmd+Shift+Enter, which Monaco would otherwise capture. */
  onRun?: () => void;
  onSubmit?: () => void;
  label: string;
};

/**
 * Monaco for one file. Each `path` keeps its own model, so undo history is per file.
 *
 * The editor is uncontrolled: `value` only seeds a new model. Feeding every keystroke back in
 * as a prop races with typing and drops characters, so programmatic changes go through the
 * editor instance from `onMount` instead.
 */
export function CodeEditor({
  path,
  value,
  readOnly = false,
  onChange,
  onMount,
  onRun,
  onSubmit,
  label,
}: Props) {
  const theme = useResolvedTheme();
  const monaco = useMonaco();
  const handlers = useRef({ onRun, onSubmit });

  useEffect(() => {
    handlers.current = { onRun, onSubmit };
  }, [onRun, onSubmit]);

  // Rebuild the theme from the tokens whenever the app theme changes.
  useEffect(() => {
    if (!monaco) return;
    monaco.editor.defineTheme(THEME, themeFromTokens());
    monaco.editor.setTheme(THEME);
  }, [monaco, theme]);

  const mount: OnMount = (instance, api) => {
    instance.addCommand(api.KeyMod.CtrlCmd | api.KeyCode.Enter, () => handlers.current.onRun?.());
    instance.addCommand(api.KeyMod.CtrlCmd | api.KeyMod.Shift | api.KeyCode.Enter, () =>
      handlers.current.onSubmit?.(),
    );
    onMount?.(instance, api);
  };

  return (
    <Editor
      path={path}
      defaultValue={value}
      defaultLanguage={path.endsWith(".py") ? "python" : undefined}
      theme={THEME}
      beforeMount={defineTheme}
      onMount={mount}
      onChange={(next) => onChange?.(next ?? "")}
      loading={<p className="p-4 text-sm text-muted">Loading the editor…</p>}
      options={{
        readOnly,
        ariaLabel: label,
        fontFamily: "var(--font-jetbrains), ui-monospace, monospace",
        fontSize: 14,
        lineHeight: 22,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        tabSize: 4,
        insertSpaces: true,
        automaticLayout: true,
        renderWhitespace: "selection",
        fontLigatures: false,
        accessibilitySupport: "auto",
        padding: { top: 12 },
      }}
    />
  );
}
