import pytest

from backend.rag.chunker import chunk_text


def test_chunk_text_splits_with_overlap():
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=150)
    assert len(chunks) == 3
    assert len(chunks[0]) == 1000
    assert len(chunks[-1]) == 800


def test_chunk_text_short_input_single_chunk():
    chunks = chunk_text("short text", chunk_size=1000, overlap=150)
    assert chunks == ["short text"]


def test_chunk_text_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=100, overlap=100)
