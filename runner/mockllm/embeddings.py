"""Deterministic embeddings for text that has no precomputed vector in the fixtures.

A hashed bag of words: every token adds ±weight to one of `dim` buckets, then the vector
is L2-normalized. Texts that share words land close together, which is enough for
retrieval tasks to behave like a real (if simple) embedding model. Stable across runs and
machines because it uses SHA-256, not Python's salted hash().
"""

import hashlib
import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS_TEXT = (
    "a an and are as at be by can do does for from has have how i if in is it its of on or "
    "our that the their this to was we what when where which who will with you your"
)
STOPWORDS = frozenset(_STOPWORDS_TEXT.split())


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


def _bucket(token: str, dim: int) -> tuple[int, float]:
    digest = hashlib.sha256(token.encode()).digest()
    index = int.from_bytes(digest[:4], "big") % dim
    sign = 1.0 if digest[4] & 1 else -1.0
    return index, sign


def hashed_embedding(text: str, dim: int) -> list[float]:
    vector = [0.0] * dim
    for token, count in Counter(tokens(text)).items():
        index, sign = _bucket(token, dim)
        vector[index] += sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [round(v / norm, 6) for v in vector]
