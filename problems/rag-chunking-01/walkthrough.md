# Walkthrough

This shows the full solution. Try the hints first if you'd like to solve it yourself.

## 1. Find the symptoms

Printing the chunks for `returns.md` shows three problems at once:

- Windows of 40 words run across headings, so one chunk mixes the end of one section with
  the start of the next.
- The `section` label comes from whichever heading appears inside the window, so text before
  that heading gets the wrong label.
- `range(0, len(words) - max_words, max_words)` stops early, so the last part of every page,
  often a whole section, is never indexed.

Retrieval scores on chunk text, so a question about deposits lands on a chunk labelled
"late returns" and recall@5 sits around 0.4.

## 2. Chunk inside sections

Split the page into `(heading, body)` pairs first, then window inside each body:

```python
def split_sections(markdown):
    sections = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
    return [(heading, "\n".join(lines).strip()) for heading, lines in sections]


def chunk_document(doc, markdown, max_words=40):
    chunks = []
    for heading, body in split_sections(markdown):
        section = f"{doc}#{slugify(heading)}"
        words = body.split()
        for start in range(0, len(words), max_words):
            window = " ".join(words[start : start + max_words])
            chunks.append(Chunk(doc, section, f"## {heading}\n{window}"))
    return chunks
```

Putting the heading in every chunk matters twice: it keeps the citation right, and it adds
the section's key words ("Deposits", "Late returns") to the text that gets embedded.

## 3. Send all retrieved excerpts

`build_prompt` joins `chunks[:1]`, so the model only ever sees the top hit. Join all of
them:

```python
context = "\n\n".join(chunk.text for chunk in chunks)
```

With both fixes recall@5 is about 0.96, and the model gets every excerpt it needs.

## In an interview

Explain how you'd catch this earlier: log what was retrieved and what was sent, keep a small
labelled question set like `questions.jsonl`, and track recall@k in CI whenever chunking or
embedding settings change.
