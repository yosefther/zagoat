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


def chunk_document(doc: str, markdown: str, max_words: int = 40) -> list[Chunk]:
    """Split one markdown page into chunks of at most `max_words` body words.

    Each chunk belongs to exactly one `## ` section and starts with that section's heading.
    """
    words = markdown.split()
    chunks = []
    section = slugify(doc)
    heading = ""
    for start in range(0, len(words) - max_words, max_words):
        window = words[start : start + max_words]
        if "##" in window:
            i = window.index("##")
            heading_words = []
            for word in window[i + 1 :]:
                heading_words.append(word)
                if word[:1].isupper() is False:
                    break
            heading = " ".join(heading_words)
            section = f"{doc}#{slugify(heading)}"
        chunks.append(Chunk(doc=doc, section=section, text=" ".join(window)))
    return chunks
