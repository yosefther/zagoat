"use client";

import type { OnMount } from "@monaco-editor/react";
import { useEffect, useId, useRef, useState } from "react";

import { CodeEditor } from "@/components/editor/CodeEditor";
import { FileTabs } from "@/components/editor/FileTabs";
import { config } from "@/config";
import { request } from "@/lib/api";
import { Autosaver, type Files, type SaveStatus } from "@/lib/autosave";
import type { ProblemDetail } from "@/lib/types";

const STATUS_TEXT: Record<SaveStatus, string> = {
  saved: "All changes saved",
  unsaved: "Unsaved changes",
  saving: "Saving…",
  error: "Couldn't save. Retrying…",
};

type Props = {
  problem: ProblemDetail;
  /** Called with the latest files whenever they change (for Run and Submit). */
  onFilesChange?: (files: Files) => void;
  readOnly?: boolean;
};

export function SolveArea({ problem, onFilesChange, readOnly = false }: Props) {
  const starter = problem.starter_files ?? {};
  const fileNames = Object.keys(starter);
  const panelId = useId();
  const [files, setFiles] = useState<Files>(() => ({ ...starter, ...problem.draft_files }));
  const [active, setActive] = useState(fileNames[0] ?? "");
  const [status, setStatus] = useState<SaveStatus>("saved");
  const saver = useRef<Autosaver | null>(null);
  const editor = useRef<Parameters<OnMount>[0] | null>(null);

  useEffect(() => {
    const autosaver = new Autosaver(
      (next) =>
        request(`/problems/${encodeURIComponent(problem.id)}/draft`, {
          method: "PUT",
          body: { files: next },
        }),
      setStatus,
      config.autosaveDelayMs,
      config.autosaveRetryMs,
    );
    saver.current = autosaver;
    const warn = (event: BeforeUnloadEvent) => {
      if (autosaver.hasUnsavedChanges()) event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => {
      window.removeEventListener("beforeunload", warn);
      void autosaver.flush().finally(() => autosaver.dispose());
    };
  }, [problem.id]);

  useEffect(() => {
    onFilesChange?.(files);
  }, [files, onFilesChange]);

  function change(name: string, content: string) {
    if (readOnly || files[name] === content) return;
    const next = { ...files, [name]: content };
    setFiles(next);
    saver.current?.update(next);
  }

  function resetActive() {
    const ok = window.confirm(`Reset ${active} to the starter code? Your changes to it are lost.`);
    const model = editor.current?.getModel();
    if (!ok || !model) return;
    // An edit (not setValue) so Ctrl+Z can undo the reset; onChange then saves it.
    model.pushEditOperations(
      [],
      [{ range: model.getFullModelRange(), text: starter[active] ?? "" }],
      () => null,
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center justify-between gap-4 border-b border-border bg-surface pr-3">
        <FileTabs files={fileNames} active={active} onSelect={setActive} panelId={panelId} />
        <div className="flex shrink-0 items-center gap-3 text-xs text-muted">
          {readOnly ? (
            <span>Read only</span>
          ) : (
            <>
              <span role="status" aria-live="polite" className={status === "error" ? "text-danger" : ""}>
                {STATUS_TEXT[status]}
              </span>
              <button type="button" onClick={resetActive} className="rounded px-2 py-1 hover:bg-code">
                Reset file
              </button>
            </>
          )}
        </div>
      </div>
      <div
        id={panelId}
        role="tabpanel"
        aria-labelledby={`tab-${active}`}
        className="min-h-0 flex-1 bg-surface"
      >
        <CodeEditor
          path={`${problem.id}/${active}`}
          value={files[active] ?? ""}
          readOnly={readOnly}
          onChange={(value) => change(active, value)}
          onMount={(instance) => {
            editor.current = instance;
          }}
          label={`Code editor for ${active}`}
        />
      </div>
      <p className="border-t border-border bg-surface px-3 py-1 text-xs text-muted">
        Tab inserts spaces. Press Ctrl+M (Ctrl+Shift+M on Mac) to make Tab move focus out of the
        editor.
      </p>
    </div>
  );
}
