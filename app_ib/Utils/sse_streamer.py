"""
sse_streamer — Server-Sent Events over plain Django streaming responses, fanned
out across processes via Redis pub/sub (no Django Channels / WebSockets).

Channels:
  engine:feed                 -> live activity ticker
  engine:notif:{user_id}      -> per-user notifications

Publishers (publish_feed / publish_notification) are best-effort: a Redis outage
never breaks the originating write. The `once=True` mode yields the current
snapshot and closes (used by tests / first-paint); live mode subscribes and
streams with heartbeats until max_seconds.
"""
import json
import logging
import time

from rest_framework.renderers import BaseRenderer

logger = logging.getLogger(__name__)


class EventStreamRenderer(BaseRenderer):
    """DRF renderer that advertises text/event-stream so content negotiation
    accepts a browser EventSource's `Accept: text/event-stream` header (otherwise
    @api_view returns 406 Not Acceptable before the view body runs). The actual
    body is produced by StreamingHttpResponse, so render() is never used."""
    media_type = "text/event-stream"
    format = "txt"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Streaming responses bypass render(); this only fires for the rare
        # non-streaming branch (e.g. an auth-error ServerResponse), so emit JSON.
        if isinstance(data, (dict, list)):
            return json.dumps(data).encode(self.charset)
        if data is None:
            return b""
        return str(data).encode(self.charset)

FEED_CHANNEL = "engine:feed"
NOTIF_CHANNEL_PREFIX = "engine:notif:"
CHAT_CHANNEL_PREFIX = "engine:chat:"


def user_channels(user_id):
    """All Redis channels a single per-user SSE connection subscribes to."""
    return {
        f"{NOTIF_CHANNEL_PREFIX}{user_id}": "notification",
        f"{CHAT_CHANNEL_PREFIX}{user_id}": "chat",
        FEED_CHANNEL: "feed",
    }


def _redis():
    try:
        from django_redis import get_redis_connection
        return get_redis_connection("default")
    except Exception as e:  # LocMemCache / no redis
        logger.debug("redis pub/sub unavailable: %s", e)
        return None


def _sse_frame(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------- publishers ----------------------------
def publish_feed(payload):
    conn = _redis()
    if conn:
        try:
            conn.publish(FEED_CHANNEL, json.dumps(payload))
        except Exception as e:
            logger.warning("publish_feed failed: %s", e)


def publish_notification(user_id, payload):
    conn = _redis()
    if conn:
        try:
            conn.publish(f"{NOTIF_CHANNEL_PREFIX}{user_id}", json.dumps(payload))
        except Exception as e:
            logger.warning("publish_notification failed: %s", e)


def publish_chat(user_id, payload):
    conn = _redis()
    if conn:
        try:
            conn.publish(f"{CHAT_CHANNEL_PREFIX}{user_id}", json.dumps(payload))
        except Exception as e:
            logger.warning("publish_chat failed: %s", e)


# ---------------------------- multiplexed stream ----------------------------
def sse_multiplex(snapshot_frames, channel_event_map, once=False, max_seconds=25, heartbeat=15):
    """ONE connection, MANY channels. snapshot_frames = list of (event_name, data).
    channel_event_map = {redis_channel: event_name}. Each inbound message is emitted
    as its mapped event type so the client can dispatch on a single EventSource.
    """
    for event_name, data in snapshot_frames:
        yield _sse_frame(event_name, data)
    if once:
        yield ": end-of-snapshot\n\n"
        return
    conn = _redis()
    if not conn:
        yield ": no-stream-backend\n\n"
        return
    pubsub = conn.pubsub()
    pubsub.subscribe(*channel_event_map.keys())
    start = last_beat = time.monotonic()
    try:
        while time.monotonic() - start < max_seconds:
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("type") == "message":
                ch = msg["channel"]
                if isinstance(ch, bytes):
                    ch = ch.decode("utf-8")
                raw = msg["data"]
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                event_name = channel_event_map.get(ch, "message")
                yield _sse_frame(event_name, json.loads(raw))
            now = time.monotonic()
            if now - last_beat >= heartbeat:
                last_beat = now
                yield ": heartbeat\n\n"
    finally:
        try:
            pubsub.close()
        except Exception:
            pass


# ---------------------------- single-channel stream ----------------------------
def sse_stream(snapshot, channel, event_name, once=False, max_seconds=25, heartbeat=15):
    """Yield SSE frames: snapshot first, then live pub/sub messages (unless once)."""
    for item in snapshot:
        yield _sse_frame(event_name, item)

    if once:
        yield ": end-of-snapshot\n\n"
        return

    conn = _redis()
    if not conn:
        yield ": no-stream-backend\n\n"
        return
    pubsub = conn.pubsub()
    pubsub.subscribe(channel)
    start = time.monotonic()
    last_beat = start
    try:
        while time.monotonic() - start < max_seconds:
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("type") == "message":
                raw = msg["data"]
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                yield _sse_frame(event_name, json.loads(raw))
            now = time.monotonic()
            if now - last_beat >= heartbeat:
                last_beat = now
                yield ": heartbeat\n\n"
    finally:
        try:
            pubsub.close()
        except Exception:
            pass
