import json

import httpx

from ml.training.common.paraphrase import OllamaParaphraser, review_sample, synthetic_share


def _client(reply: str) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["stream"] is False and "make a service" in body["prompt"]
        return httpx.Response(200, json={"response": reply})

    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama")


def test_paraphraser_parses_numbered_lines_and_drops_duplicates() -> None:
    reply = "1. how can I build a service\n2) show me how to write a service\n- how can I build a service\n\nshort"
    out = OllamaParaphraser(_client(reply), model="llama3").paraphrase("make a service", n=5)
    assert out == ["how can I build a service", "show me how to write a service"]


def test_paraphraser_survives_server_errors() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(500)), base_url="http://o"
    )
    assert OllamaParaphraser(client, model="m").paraphrase("make a service", n=3) == []


def test_review_sample_fraction_is_deterministic_and_labelstudio_shaped() -> None:
    rows = [
        {"id": f"p{i}", "tokens": ["a", "b"], "intent": "X", "source": "llm_paraphrase"}
        for i in range(50)
    ]
    a = review_sample(rows, fraction=0.2, seed=7)
    assert len(a) == 10 and a == review_sample(rows, fraction=0.2, seed=7)
    assert a[0]["data"]["text"] == "a b" and a[0]["meta"]["id"].startswith("p")


def test_synthetic_share_per_intent() -> None:
    rows = (
        [{"intent": "A", "source": "seed"}] * 6
        + [{"intent": "A", "source": "template"}] * 2
        + [{"intent": "A", "source": "llm_paraphrase"}] * 2
        + [{"intent": "B", "source": "seed"}] * 4
    )
    assert synthetic_share(rows) == {"A": 0.4, "B": 0.0}
