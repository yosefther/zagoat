"""Split handbook pages into chunks for retrieval."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    doc: str  # file name, e.g. "returns.md"
    section: str  # section id, e.g. "returns.md#refund-timing"
    text: str  # starts with the section heading, e.g. "## Refund timing\n..."


def slugify(heading: str) -> str:
    """'Refund timing' -> 'refund-timing'."""
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def split_sections(markdown: str) -> list[tuple[str, str]]:
    """Return (heading, body) for every `## ` section. Text before the first one is ignored."""
    sections: list[tuple[str, list[str]]] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
    return [(heading, "\n".join(lines).strip()) for heading, lines in sections]


def chunk_document(doc: str, markdown: str, max_words: int = 40) -> list[Chunk]:
    """Split one markdown page into chunks of at most `max_words` body words.

    Each chunk belongs to exactly one `## ` section and starts with that section's heading.
    """
    chunks = []
    for heading, body in split_sections(markdown):
        section = f"{doc}#{slugify(heading)}"
        words = body.split()
        for start in range(0, len(words), max_words):
            window = " ".join(words[start : start + max_words])
            chunks.append(Chunk(doc=doc, section=section, text=f"## {heading}\n{window}"))
    return chunks
