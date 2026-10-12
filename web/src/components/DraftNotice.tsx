/** Marks placeholder legal text that must be reviewed before launch (brief, section 12). */
export function DraftNotice() {
  return (
    <p role="note" className="rounded-lg border border-danger p-4 text-sm text-danger">
      Draft for review. This placeholder text is not legal advice and must be reviewed and
      replaced before zagoat launches.
    </p>
  );
}
