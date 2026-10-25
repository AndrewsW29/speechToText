from app.adapters.outbound.pdf.redis_events import RedisEvents

from tests.fakes.redis import FakeRedis


def test_events_get_increasing_sequence_numbers_and_replay_from_any_point() -> None:
    redis = FakeRedis()
    events = RedisEvents(redis)  # type: ignore[arg-type]
    events.publish("d_1", "scanning")
    events.publish("d_1", "reading", pages_done=0, pages_total=120)
    events.publish("d_1", "ready", chunks=40)
    all_events = events.read("d_1")
    assert [e["seq"] for e in all_events] == [1, 2, 3]
    assert [e["stage"] for e in all_events] == ["scanning", "reading", "ready"]
    assert all_events[1]["pages_total"] == 120 and all_events[2]["chunks"] == 40
    assert [e["seq"] for e in events.read("d_1", after=2)] == [3]
    assert events.read("d_1", after=3) == []


def test_documents_do_not_see_each_others_events_and_streams_expire() -> None:
    redis = FakeRedis()
    events = RedisEvents(redis, ttl_seconds=60)  # type: ignore[arg-type]
    events.publish("d_1", "scanning")
    events.publish("d_2", "ready")
    assert [e["stage"] for e in events.read("d_1")] == ["scanning"]
    assert events.read("d_missing") == [] and set(redis.expiries.values()) == {60}


def test_publishing_never_raises_into_the_pipeline_when_redis_is_down() -> None:
    class Down:
        def rpush(self, *_: object) -> int:
            raise ConnectionError("redis down")

    RedisEvents(Down()).publish("d_1", "scanning")  # type: ignore[arg-type]
