import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Renders task Markdown (statements, hints, walkthroughs). Raw HTML is not allowed. */
export function Markdown({ children, className = "" }: { children: string; className?: string }) {
  return (
    <div className={`markdown ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
