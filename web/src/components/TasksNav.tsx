import Link from "next/link";

/** The switch between the two ways to browse: by path, or the full table. */
export function TasksNav({ current }: { current: "paths" | "all" }) {
  const item = (view: "paths" | "all", href: string, label: string) => (
    <Link
      href={href}
      aria-current={current === view ? "page" : undefined}
      className={`border-b-2 px-1 pb-2 font-medium no-underline ${
        current === view ? "border-brand text-ink" : "border-transparent text-muted hover:text-ink"
      }`}
    >
      {label}
    </Link>
  );
  return (
    <nav aria-label="Browse tasks" className="flex gap-6 border-b border-line">
      {item("paths", "/tasks", "Paths")}
      {item("all", "/tasks/all", "All tasks")}
    </nav>
  );
}
