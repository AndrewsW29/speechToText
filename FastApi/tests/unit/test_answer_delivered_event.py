from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.application.events import AnswerDelivered, EventBus
from app.application.use_cases.ask_question import AskQuestion

from tests.fakes import FakeTranscriber


def test_bus_delivers_to_subscribers_and_isolates_failures() -> None:
    bus, seen = EventBus(), []
    bus.subscribe(AnswerDelivered, lambda e: (_ for _ in ()).throw(RuntimeError("boom")))
    bus.subscribe(AnswerDelivered, seen.append)
    bus.publish(AnswerDelivered("q1", None, ("s",), 0.5))
    assert [e.query_id for e in seen] == ["q1"]


def test_ask_question_publishes_answer_delivered() -> None:
    bus, seen = EventBus(), []
    bus.subscribe(AnswerDelivered, seen.append)
    result = AskQuestion(FakeTranscriber("hi"), FixedAnswerGenerator(), events=bus).execute(
        b"audio"
    )
    assert seen[0].query_id == result.query.id and seen[0].source_ids
