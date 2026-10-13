"""Sample tests. Run them as often as you like; Submit runs a larger hidden set."""

from chunker import chunk_document

PAGE = """# Sample page

## First topic

alpha beta gamma delta epsilon

## Second topic

zeta eta theta
"""


def test_each_chunk_starts_with_its_heading():
    for chunk in chunk_document("sample.md", PAGE, max_words=10):
        heading = "First topic" if chunk.section.endswith("first-topic") else "Second topic"
        assert chunk.text.startswith(f"## {heading}"), f"Chunk should start with its heading: {chunk.text!r}"


def test_sections_get_their_own_chunks():
    chunks = chunk_document("sample.md", PAGE, max_words=10)
    assert [c.section for c in chunks] == ["sample.md#first-topic", "sample.md#second-topic"]
    assert "zeta" not in chunks[0].text, "The first chunk spills into the second section"


def test_long_sections_are_split_without_dropping_words():
    chunks = chunk_document("sample.md", PAGE, max_words=2)
    first = [c for c in chunks if c.section == "sample.md#first-topic"]
    bodies = [c.text.split("\n", 1)[1].split() for c in first]
    assert bodies == [["alpha", "beta"], ["gamma", "delta"], ["epsilon"]]
