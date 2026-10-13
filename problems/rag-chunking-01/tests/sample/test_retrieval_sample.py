import json

from pipeline import Pipeline, load_docs
from zagoat import data_path, record_metric


def test_recall_on_a_few_questions():
    questions = [json.loads(line) for line in data_path("questions.jsonl").read_text().splitlines()]
    sample = questions[:8]
    pipeline = Pipeline()
    pipeline.index(load_docs())
    hits = sum(q["section"] in {c.section for c in pipeline.retrieve(q["question"])} for q in sample)
    recall = hits / len(sample)
    record_metric("recall_at_5_sample", recall)
    print(f"recall@5 on {len(sample)} sample questions: {recall:.2f}")
    assert recall >= 0.8, f"recall@5 is {recall:.2f} on the sample questions; aim for 0.80 or more"
