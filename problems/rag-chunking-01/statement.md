Fernhollow Outfitters, a (fictional) outdoor gear shop, runs a support bot that answers
customer questions from its handbook. Since the last release, the bot keeps citing the wrong
policy: ask about deposits and it quotes late fees; ask about the warranty and it says it
can't find anything.

The pipeline lives in two files:

- `chunker.py` splits each handbook page into chunks.
- `pipeline.py` embeds the chunks, retrieves the top 5 for a question and asks the model.

Your job is to find out why retrieval misses and fix it.

## What the chunker must do

`chunk_document(doc, markdown, max_words=40)` returns a list of `Chunk(doc, section, text)`:

- Every `## ` heading starts a section. Text before the first `## ` heading is ignored.
- A chunk belongs to exactly one section. `section` is `"<doc>#<slug>"`, using the
  `slugify` helper on the heading, for example `"returns.md#refund-timing"`.
- `text` starts with the heading line (`## Refund timing`), then a newline, then up to
  `max_words` words of that section's body. The heading doesn't count toward the limit.
- Long sections are split into consecutive chunks. No words are dropped, repeated or mixed
  in from another section.

Also check what the model actually receives: every retrieved excerpt should reach the
prompt.

## Data

- `data/docs/*.md`: the handbook pages.
- `data/questions.jsonl`: customer questions, each with the section that answers it.

Read data files with `zagoat.data_path("docs")`. The OpenAI client is already configured to
talk to a mock model: embeddings are deterministic, and chat answers are canned, so grading
looks at retrieval and at the prompt, not at the wording of answers.

## How you're graded

**Run tests** runs the sample tests and shows their output. **Submit solution** runs hidden
tests on the chunking rules above and on the prompt, and measures retrieval recall@5 on the
full question set. You pass when every test passes and recall@5 is at least **0.80**.
