import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { SAMPLE_TASKS } from "./samples";

const PROBLEMS = path.resolve(import.meta.dirname, "../../../problems");

function field(yaml: string, key: string): string {
  const match = yaml.match(new RegExp(`^${key}: (.+)$`, "m"));
  return match ? match[1].trim() : "";
}

describe("landing page samples", () => {
  it.each(SAMPLE_TASKS)("$id matches its problem.yaml", (task) => {
    const yaml = readFileSync(path.join(PROBLEMS, task.id, "problem.yaml"), "utf8");
    expect(field(yaml, "title")).toBe(task.title);
    expect(field(yaml, "difficulty")).toBe(task.difficulty);
    expect(Number(field(yaml, "est_minutes"))).toBe(task.minutes);
  });
});
