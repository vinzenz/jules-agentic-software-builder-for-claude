from agentic_builder.common.events import EventEmitter


def test_event_emitter_basic():
    emitter = EventEmitter()
    received = []

    def handler(payload):
        received.append(payload)

    emitter.on("test_event", handler)
    emitter.emit("test_event", {"data": 123})

    assert len(received) == 1
    assert received[0]["data"] == 123


def test_event_emitter_multiple_handlers():
    emitter = EventEmitter()
    count = 0

    def h1(_):
        nonlocal count
        count += 1

    def h2(_):
        nonlocal count
        count += 2

    emitter.on("evt", h1)
    emitter.on("evt", h2)

    emitter.emit("evt", {})
    assert count == 3


def test_event_emitter_off():
    emitter = EventEmitter()
    calls = 0

    def h(_):
        nonlocal calls
        calls += 1

    emitter.on("evt", h)
    emitter.emit("evt", {})
    emitter.off("evt", h)
    emitter.emit("evt", {})

    assert calls == 1
