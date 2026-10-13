"""A small retrieval-augmented answering pipeline over the Fernhollow handbook."""

import numpy as np
from openai import OpenAI

from chunker import Chunk, chunk_document
from zagoat import data_path

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You answer customer questions for Fernhollow Outfitters. Use only the handbook "
    "excerpts provided. If they don't contain the answer, say so."
)


def load_docs() -> dict[str, str]:
    """Every handbook page, keyed by file name."""
    return {p.name: p.read_text() for p in sorted(data_path("docs").glob("*.md"))}


class Pipeline:
    def __init__(self, client: OpenAI | None = None, top_k: int = 5) -> None:
        self.client = client or OpenAI()
        self.top_k = top_k
        self.chunks: list[Chunk] = []
        self.vectors = np.zeros((0, 0))

    def _embed(self, texts: list[str]) -> np.ndarray:
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        vectors = np.array([item.embedding for item in response.data], dtype=float)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.where(norms == 0, 1, norms)

    def index(self, docs: dict[str, str]) -> None:
        self.chunks = [c for name, text in docs.items() for c in chunk_document(name, text)]
        self.vectors = self._embed([c.text for c in self.chunks])

    def retrieve(self, question: str) -> list[Chunk]:
        query = self._embed([question])[0]
        scores = self.vectors @ query
        best = np.argsort(-scores)[: self.top_k]
        return [self.chunks[i] for i in best]

    def build_prompt(self, question: str, chunks: list[Chunk]) -> str:
        context = "\n\n".join(chunk.text for chunk in chunks[:1])
        return f"Handbook excerpts:\n\n{context}\n\nQuestion: {question}"

    def answer(self, question: str) -> str:
        prompt = self.build_prompt(question, self.retrieve(question))
        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""


if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.index(load_docs())
    print(pipeline.answer("How long do refunds take?"))
