/** Marks placeholder legal text that must be reviewed before launch (brief, section 12). */
export function DraftNotice() {
  return (
    <p role="note" className="border-l-2 border-warning bg-raised p-4 text-sm">
      <strong className="text-warning">Draft for review.</strong> This placeholder text is not
      legal advice and must be reviewed and replaced before zagoat launches.
    </p>
  );
}
