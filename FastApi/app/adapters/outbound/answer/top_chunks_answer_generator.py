"""Backwards-compatible name for the retrieval-only generator."""

from app.adapters.outbound.answer.snippet_answer_generator import SnippetAnswerGenerator

TopChunksAnswerGenerator = SnippetAnswerGenerator
