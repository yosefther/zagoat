from rag_helpers import normalize

from zagoat import llm_calls, record_metric


def test_retrieval_recall_at_5(pipeline, questions):
    """Retrieval recall@5 on the full question set"""
    hits = sum(
        q["section"] in {c.section for c in pipeline.retrieve(q["question"])} for q in questions
    )
    record_metric("recall_at_5", hits / len(questions))


def last_prompt():
    chats = [call for call in llm_calls() if call["endpoint"] == "chat.completions"]
    assert chats, "answer() should call the chat completions API"
    return normalize(chats[-1]["request"]["messages"][-1]["content"])


def test_prompt_includes_every_retrieved_excerpt(pipeline, questions):
    """The prompt sent to the model includes every retrieved excerpt"""
    for q in questions[::4]:
        retrieved = pipeline.retrieve(q["question"])
        pipeline.answer(q["question"])
        prompt = last_prompt()
        missing = [c for c in retrieved if normalize(c.text) not in prompt]
        assert not missing, "Some retrieved excerpts never reach the model's prompt"


def test_prompt_carries_the_evidence(pipeline, questions):
    """When the right section is retrieved, its evidence reaches the model"""
    checked = 0
    for q in questions:
        if q["section"] not in {c.section for c in pipeline.retrieve(q["question"])}:
            continue
        pipeline.answer(q["question"])
        assert normalize(q["evidence"]) in last_prompt(), (
            "The model never sees the passage that answers the question"
        )
        checked += 1
    assert checked, "No question retrieved its own section"
