"""
Tests for the transcript module.
"""

from __future__ import annotations

from typing import Any

import pytest

from direktor.core.transcript import aggregate_chunks


def test_aggregate_chunks_groups_by_duration() -> None:
    """aggregate_chunks should group chunks until the target duration is exceeded."""
    chunks: list[dict[str, Any]] = [
        {"text": "Hello world", "timestamp": [0.0, 5.0]},
        {"text": "This is a test", "timestamp": [5.0, 12.0]},
        {"text": "Another segment", "timestamp": [12.0, 18.0]},
        {"text": "Final segment", "timestamp": [18.0, 25.0]},
    ]
    result = aggregate_chunks(chunks, target_duration=10)
    assert len(result) >= 2
    assert result[0]["text"]
    assert result[0]["timestamp"][0] == pytest.approx(0.0)


def test_aggregate_chunks_empty_input() -> None:
    """aggregate_chunks should return an empty list for empty input."""
    assert aggregate_chunks([]) == []


def test_aggregate_chunks_single_chunk() -> None:
    """aggregate_chunks should preserve a single chunk."""
    chunks = [{"text": "Only one", "timestamp": [0.0, 3.0]}]
    result = aggregate_chunks(chunks, target_duration=10)
    assert len(result) == 1
    assert result[0]["text"] == "Only one"
