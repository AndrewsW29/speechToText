import pytest

from ml.training.common.pii import scrub


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("mail me at jane.doe@example.com please", "email"),
        ("my key is AKIAIOSFODNN7EXAMPLE ok", "aws_key"),
        ("token ghp_abcdefghijklmnopqrstuvwxyz0123456789 here", "github_token"),
        ("use sk-abcdefghijklmnopqrstuvwxyz123456 for it", "api_key"),
        ("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc123def", "jwt"),
        ("my password is hunter two", "spoken_secret"),
        ("the api key is a b c one two three", "spoken_secret"),
        ("server at 192.168.10.25 is down", "ip_address"),
    ],
)
def test_sensitive_values_are_redacted(text: str, kind: str) -> None:
    clean, findings = scrub(text)
    assert kind in {f.kind for f in findings}
    assert "[REDACTED:" in clean
    for secret in (
        "jane.doe@example.com",
        "AKIAIOSFODNN7EXAMPLE",
        "hunter",
        "192.168.10.25",
        "abc123def",
    ):
        assert secret not in clean


def test_ordinary_developer_text_is_untouched() -> None:
    text = "how do I create a @RestController and a service with JPA"
    assert scrub(text) == (text, [])


def test_scrub_is_idempotent() -> None:
    once, _ = scrub("email a@b.co and password is swordfish")
    assert scrub(once)[0] == once
