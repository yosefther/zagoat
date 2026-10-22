"use client";

import { useWorkspace } from "./WorkspaceContext";
import { ResultsPanel } from "@/components/results/ResultsPanel";
import { Tabs, panelId, tabId } from "@/components/Tabs";

const TABS_ID = "console";

/** Bottom pane: Sample tests (Run output) and Results (Submit). */
export function ConsolePanel() {
  const { consoleTab, setConsoleTab, run, submit, busy } = useWorkspace();
  const showing = consoleTab === "sample" ? run : submit;
  const empty =
    consoleTab === "sample"
      ? "Run the sample tests with Run tests (Ctrl+Enter). Their output appears here."
      : "Submit runs the hidden tests and metrics (Ctrl+Shift+Enter). Results appear here.";

  return (
    <div className="flex h-full min-h-0 flex-col bg-panel">
      <div className="border-b border-line">
        <Tabs
          tabs={[
            { id: "sample", label: busy === "run" ? "Sample tests (running)" : "Sample tests" },
            { id: "results", label: busy === "submit" ? "Results (grading)" : "Results" },
          ]}
          active={consoleTab}
          onSelect={(id) => setConsoleTab(id as "sample" | "results")}
          idPrefix={TABS_ID}
          label="Console"
        />
      </div>
      <div
        id={panelId(TABS_ID)}
        role="tabpanel"
        aria-labelledby={tabId(TABS_ID, consoleTab)}
        className="flex min-h-0 flex-1 flex-col"
      >
        <ResultsPanel job={showing.job} error={showing.error} emptyText={empty} />
      </div>
    </div>
  );
}
