import json

import pytest

from pipeline import Pipeline, load_docs
from zagoat import data_path


@pytest.fixture(scope="session")
def docs():
    return load_docs()


@pytest.fixture(scope="session")
def questions():
    return [json.loads(line) for line in data_path("questions.jsonl").read_text().splitlines()]


@pytest.fixture(scope="session")
def pipeline(docs):
    pipeline = Pipeline()
    pipeline.index(docs)
    return pipeline
