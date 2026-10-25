import pytest
from app.application.services.chunking import (
    CodeAwareChunker,
    SentenceChunker,
    TokenChunker,
)


class TestSentenceChunker:
    def test_groups_sentences_up_to_the_limit(self) -> None:
        text = "One is short. Two is short too. Three keeps going and going. Four ends it."
        chunks = SentenceChunker(max_chars=40).chunk(text)
        assert all(len(c) <= 40 for c in chunks)
        assert " ".join(chunks).replace("  ", " ") == text

    def test_oversized_sentence_is_kept_whole(self) -> None:
        long = "x" * 100 + "."
        assert SentenceChunker(max_chars=20).chunk(long) == [long]

    def test_empty_text_gives_no_chunks(self) -> None:
        assert SentenceChunker(max_chars=40).chunk("   ") == []


class TestTokenChunker:
    def test_windows_overlap(self) -> None:
        words = " ".join(f"w{i}" for i in range(10))
        chunks = TokenChunker(max_tokens=4, overlap=1).chunk(words)
        assert chunks[0] == "w0 w1 w2 w3"
        assert chunks[1].startswith("w3")  # one token of overlap
        assert chunks[-1].endswith("w9")

    def test_rejects_bad_parameters(self) -> None:
        with pytest.raises(ValueError):
            TokenChunker(max_tokens=3, overlap=3)


JAVA = """package demo;

@Service
public class UserService {
  private final UserRepository repository;

  public UserService(UserRepository repository) {
    this.repository = repository;
  }

  public List<User> findAll() {
    return repository.findAll();
  }
}
"""


class TestCodeAwareChunker:
    def test_splits_class_and_methods(self) -> None:
        chunks = CodeAwareChunker().chunk(JAVA)
        assert any("public List<User> findAll()" in c for c in chunks)
        assert any("public UserService(UserRepository repository)" in c for c in chunks)

    def test_every_method_chunk_carries_the_class_header(self) -> None:
        chunks = CodeAwareChunker().chunk(JAVA)
        method_chunks = [c for c in chunks if "findAll" in c]
        assert method_chunks and all("class UserService" in c for c in method_chunks)

    def test_braces_stay_balanced_in_each_chunk(self) -> None:
        for c in CodeAwareChunker().chunk(JAVA):
            assert c.count("{") == c.count("}")

    def test_falls_back_to_whole_text_when_no_class_found(self) -> None:
        assert CodeAwareChunker().chunk("just some prose") == ["just some prose"]
