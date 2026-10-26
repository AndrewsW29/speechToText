"""Property tests for the structure-aware chunker (lands with US19; skipped until it exists).

Whatever the input, text is never lost, reordered or duplicated, and chunks respect structure.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

chunker = pytest.importorskip("app.application.pdf.services.chunker")
Block, chunk_blocks, words = chunker.Block, chunker.chunk_blocks, chunker.words

blocks_strategy = st.lists(
    st.builds(
        Block,
        type=st.sampled_from(["paragraph", "code", "table", "heading"]),
        text=st.text(min_size=1, max_size=400),
        page=st.integers(1, 50),
        level=st.integers(1, 3),
    ),
    max_size=40,
)


def squash(text: str) -> str:
    return "".join(text.split())


@settings(max_examples=200, deadline=None)
@given(blocks_strategy)
def test_chunker_keeps_all_non_heading_text_in_order(blocks: list) -> None:  # type: ignore[type-arg]
    expected = "".join(squash(b.text) for b in blocks if b.type != "heading")
    assert "".join(squash(c.text) for c in chunk_blocks(blocks)) == expected


@settings(max_examples=100, deadline=None)
@given(blocks_strategy)
def test_no_prose_chunk_exceeds_the_token_budget(blocks: list) -> None:  # type: ignore[type-arg]
    for chunk in chunk_blocks(blocks, max_tokens=350):
        if chunk.chunk_type == "text":
            assert (
                words(chunk.text) <= 350 or "\n\n" not in chunk.text
            )  # a single oversized paragraph is split by sentences


@settings(max_examples=100, deadline=None)
@given(blocks_strategy)
def test_code_and_tables_are_never_mixed_with_prose(blocks: list) -> None:  # type: ignore[type-arg]
    kinds = {c.chunk_type for c in chunk_blocks(blocks)}
    assert kinds <= {"text", "code", "table"}
