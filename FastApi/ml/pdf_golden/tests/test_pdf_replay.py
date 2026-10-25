from ml.pdf_golden import replay


def trace(
    chunks=("c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"),
    page=3,
    quote="the limit is 5",
):
    return {
        "chunks": {"book/a.pdf": list(chunks)},
        "citations": {"book/a.pdf::q0": [{"page": page, "quote": quote, "chunk_id": chunks[0]}]},
    }


def test_identical_traces_are_safe_to_flip() -> None:
    report = replay.compare_traces(trace(), trace())
    assert report.safe and not report.citation_changes and report.chunk_churn == 0


def test_changed_citation_page_blocks_the_flip() -> None:
    report = replay.compare_traces(trace(), trace(page=4))
    assert not report.safe
    assert report.citation_changes[0].key == "book/a.pdf::q0"


def test_lost_citation_blocks_the_flip() -> None:
    new = trace()
    new["citations"]["book/a.pdf::q0"] = []
    assert not replay.compare_traces(trace(), new).safe


def test_chunk_id_churn_over_the_budget_blocks_the_flip() -> None:
    new = trace(chunks=("x1", "x2", "x3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"))
    report = replay.compare_traces(trace(), new, max_chunk_churn=0.1)
    assert report.chunk_churn == 0.3 and not report.safe
    assert replay.compare_traces(trace(), new, max_chunk_churn=0.5).safe


def test_traces_roundtrip_through_json(tmp_path) -> None:
    path = tmp_path / "t.json"
    replay.save_trace(trace(), path)
    assert replay.load_trace(path) == trace()
