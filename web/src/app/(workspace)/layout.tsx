/** The task workspace has its own top bar instead of the site header and footer. */
export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return <div className="flex min-h-full flex-1 flex-col">{children}</div>;
}
