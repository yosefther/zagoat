"""Helpers shared by the hidden tests."""


def normalize(text: str) -> str:
    return " ".join(text.split())


def sections(markdown: str) -> dict[str, str]:
    """Heading -> body, for every '## ' section."""
    result: dict[str, list[str]] = {}
    current = None
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        elif current is not None:
            result[current].append(line)
    return {heading: normalize("\n".join(lines)) for heading, lines in result.items()}
