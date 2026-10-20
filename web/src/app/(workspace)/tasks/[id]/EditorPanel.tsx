"use client";

import type { OnMount } from "@monaco-editor/react";
import { useEffect, useRef, useState } from "react";

import { useWorkspace } from "./WorkspaceContext";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { Tabs, panelId, tabId } from "@/components/Tabs";
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
const TABS_ID = "files";

/** File tabs and the editor, with debounced autosave of the draft. */
export function EditorPanel({ problem, readOnly }: { problem: ProblemDetail; readOnly: boolean }) {
  const { onFilesChange, start } = useWorkspace();
  const starter = problem.starter_files ?? {};
  const fileNames = Object.keys(starter);
  const [files, setFiles] = useState<Files>(() => ({ ...starter, ...problem.draft_files }));
  const [active, setActive] = useState(fileNames[0] ?? "");
  const [status, setStatus] = useState<SaveStatus>("saved");
  const saver = useRef<Autosaver | null>(null);
  const editor = useRef<Parameters<OnMount>[0] | null>(null);

  useEffect(() => {
    if (readOnly) return;
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
  }, [problem.id, readOnly]);

  useEffect(() => {
    onFilesChange(files);
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
    <div className="flex h-full min-h-0 flex-col bg-panel">
      <div className="flex items-center justify-between gap-4 border-b border-line pr-2">
        <Tabs
          tabs={fileNames.map((name) => ({ id: name, label: name }))}
          active={active}
          onSelect={setActive}
          idPrefix={TABS_ID}
          label="Files"
          mono
        />
        <div className="flex shrink-0 items-center gap-1 text-xs text-muted">
          {readOnly ? (
            <span className="px-2">Read only</span>
          ) : (
            <>
              <span
                role="status"
                aria-live="polite"
                className={`px-2 ${status === "error" ? "text-danger" : ""}`}
              >
                {STATUS_TEXT[status]}
              </span>
              <button type="button" onClick={resetActive} className="btn-quiet px-2 py-1 text-xs">
                Reset file
              </button>
            </>
          )}
        </div>
      </div>
      <div
        id={panelId(TABS_ID)}
        role="tabpanel"
        aria-labelledby={tabId(TABS_ID, active)}
        className="min-h-0 flex-1"
      >
        <CodeEditor
          path={`${problem.id}/${active}`}
          value={files[active] ?? ""}
          readOnly={readOnly}
          onChange={(value) => change(active, value)}
          onMount={(instance) => {
            editor.current = instance;
          }}
          onRun={() => start("run")}
          onSubmit={() => start("submit")}
          label={`Code editor for ${active}`}
        />
      </div>
    </div>
  );
}
