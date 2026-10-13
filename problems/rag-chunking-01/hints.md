# Hints

## Hint 1

Print the chunks for one page, for example `chunk_document("returns.md", text)`, and look at
the `section` and the first few words of each chunk. Do they line up with the headings?

## Hint 2

The chunker windows over the whole page at once. Splitting the page into sections first,
then windowing inside each section, makes every rule in the statement easier to meet. Check
the loop bounds too: does the last window of a page survive?

## Hint 3

Recall still low after fixing the chunks? Read `build_prompt` in `pipeline.py` and check how
many of the retrieved chunks make it into the prompt.
