import re

import pytest
from rag_helpers import normalize, sections

from chunker import chunk_document

EDGE_PAGE = """# Edge cases

Intro text before the first section is not part of any section.

## Q&A: Short answers

one two three four

## Exactly full

a b c d e f

## Notes, part 2

final words here
"""


def slug(heading):
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def body_of(chunk):
    first_line, _, rest = chunk.text.partition("\n")
    return first_line, normalize(rest)


@pytest.mark.parametrize("max_words", [6, 25, 40])
def test_every_section_is_indexed(docs, max_words):
    """Every section of every page gets at least one chunk"""
    for name, text in {**docs, "edge.md": EDGE_PAGE}.items():
        found = {c.section for c in chunk_document(name, text, max_words=max_words)}
        for heading in sections(text):
            assert f"{name}#{slug(heading)}" in found, f"No chunk for a section in {name}"


@pytest.mark.parametrize("max_words", [6, 25, 40])
def test_chunks_start_with_their_heading(docs, max_words):
    """Each chunk starts with its own section heading"""
    for name, text in {**docs, "edge.md": EDGE_PAGE}.items():
        headings = {f"{name}#{slug(h)}": h for h in sections(text)}
        for chunk in chunk_document(name, text, max_words=max_words):
            first_line, _ = body_of(chunk)
            assert chunk.section in headings, f"Unknown section id {chunk.section!r}"
            assert first_line.strip() == f"## {headings[chunk.section]}", (
                "A chunk's first line should be its section heading"
            )


@pytest.mark.parametrize("max_words", [6, 25, 40])
def test_no_text_is_dropped_or_mixed(docs, max_words):
    """Each section's chunks hold exactly that section's text, in order"""
    for name, text in {**docs, "edge.md": EDGE_PAGE}.items():
        chunks = chunk_document(name, text, max_words=max_words)
        for heading, body in sections(text).items():
            section_id = f"{name}#{slug(heading)}"
            joined = " ".join(body_of(c)[1] for c in chunks if c.section == section_id)
            assert joined == body, (
                "Joining a section's chunks should give back the section's text exactly, "
                "with nothing dropped, repeated or borrowed from another section"
            )


@pytest.mark.parametrize("max_words", [6, 25, 40])
def test_chunks_respect_the_word_limit(docs, max_words):
    """No chunk has more than max_words body words"""
    for name, text in {**docs, "edge.md": EDGE_PAGE}.items():
        for chunk in chunk_document(name, text, max_words=max_words):
            assert len(body_of(chunk)[1].split()) <= max_words, "A chunk is over the word limit"


def test_a_section_that_fills_one_chunk_exactly():
    """A section with exactly max_words words becomes one chunk"""
    chunks = [c for c in chunk_document("edge.md", EDGE_PAGE, max_words=6)
              if c.section == "edge.md#exactly-full"]
    assert len(chunks) == 1, "A section of exactly max_words words should be one chunk"
