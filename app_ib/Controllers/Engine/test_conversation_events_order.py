# Ordering/dedupe check for ChatController.conversation_events (F229).
# Pure-python mirror of the sort+dedupe tail — no DB, no Django boot:
#   python app_ib/Controllers/Engine/test_conversation_events_order.py
from datetime import datetime


def build(created, first_reply, transition, last_message):
    """Same shape as ChatController.conversation_events' event assembly."""
    events = []

    def _add(dt, event):
        if dt:
            events.append((dt, {"event": event, "when": dt.strftime("%d %b, %I:%M %p")}))

    _add(created, "Connection started")
    _add(first_reply, "Seller replied")
    _add(transition, "Connection accepted")
    if last_message and all(dt != last_message for dt, _ in events):
        _add(last_message, "Last activity")
    return [p["event"] for _, p in sorted(events, key=lambda e: e[0])]


def demo():
    t = lambda h: datetime(2026, 7, 20, h, 0)

    # Accepted BEFORE the last message arrived — narrative order would put
    # "Last activity" after "accepted" regardless of the clock.
    assert build(t(9), t(10), t(11), t(12)) == [
        "Connection started", "Seller replied", "Connection accepted", "Last activity"
    ]

    # Same events, transition recorded last (updatedAt bumped after the message).
    assert build(t(9), t(10), t(12), t(11)) == [
        "Connection started", "Seller replied", "Last activity", "Connection accepted"
    ]

    # The only message IS the seller's first reply → no duplicate row.
    assert build(t(9), t(10), None, t(10)) == ["Connection started", "Seller replied"]

    # Nothing but creation.
    assert build(t(9), None, None, None) == ["Connection started"]

    print("ok")


if __name__ == "__main__":
    demo()
