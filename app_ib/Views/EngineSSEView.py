"""SSE streaming endpoints: live activity feed + per-user notifications.

Use `?once=1` for a snapshot-and-close response (first paint / tests); omit it
for a live stream. `isSynthetic` is never included in feed output.
"""
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from app_ib.Utils.sse_streamer import (
    sse_stream, sse_multiplex, user_channels, FEED_CHANNEL, NOTIF_CHANNEL_PREFIX,
    EventStreamRenderer,
)


def _streaming(generator):
    resp = StreamingHttpResponse(generator, content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([EventStreamRenderer])
def LiveFeedSSEView(request):
    from app_ib.models import FeedEvent
    once = request.GET.get("once") in ("1", "true")
    rows = FeedEvent.objects.order_by("-timestamp")[:6]
    snapshot = [{
        "id": e.id, "eventType": e.eventType, "template": e.template,
        "city": e.city, "timestamp": e.timestamp.isoformat(),
    } for e in reversed(list(rows))]   # NOTE: isSynthetic intentionally omitted
    return _streaming(sse_stream(snapshot, FEED_CHANNEL, "feed", once=once))


@api_view(["GET"])
@permission_classes([AllowAny])
def LiveFeedInitView(request):
    """Non-streaming first paint: latest 6 feed events."""
    from app_ib.models import FeedEvent
    from app_ib.Utils.ServerResponse import ServerResponse
    from app_ib.Utils.ResponseCodes import RESPONSE_CODES
    from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
    rows = FeedEvent.objects.order_by("-timestamp")[:6]
    data = [{"id": e.id, "eventType": e.eventType, "template": e.template,
             "city": e.city, "timestamp": e.timestamp.isoformat()} for e in rows]
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=data)


@api_view(["GET"])
@permission_classes([AllowAny])
def LiveFeedBatchView(request):
    """Polling endpoint for the live ticker (/v3/trending): returns `limit`
    (default 20) feed events generated in ONE call, so the client can buffer the
    strip and re-poll rarely. Non-streaming companion to LiveFeedSSEView — the SSE
    stream is intentionally kept for when the platform scales."""
    from app_ib.algorithms.feed import generate_feed_batch
    from app_ib.Utils.ServerResponse import ServerResponse
    from app_ib.Utils.ResponseCodes import RESPONSE_CODES
    from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
    try:
        limit = int(request.GET.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    data = generate_feed_batch(limit)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([EventStreamRenderer])
def UserStreamView(request):
    """THE single per-user SSE connection. One EventSource carries notifications,
    chat messages, and live-feed events (dispatched client-side by `event:` type).
    The frontend must open ONLY this stream when authenticated."""
    from app_ib.models import Notification, FeedEvent, Message, Conversation
    from django.db.models import Q
    once = request.GET.get("once") in ("1", "true")
    uid = request.user.id

    snapshot = []
    # notifications
    for n in Notification.objects.filter(user=request.user).order_by("-timestamp")[:50]:
        snapshot.append(("notification", {
            "id": n.id, "type": n.type, "title": n.title, "body": n.body,
            "groupCount": n.groupCount, "timestamp": n.timestamp.isoformat()}))
    # unread chat messages addressed to this user
    conv_ids = list(Conversation.objects.filter(Q(clientUser=request.user) | Q(businessUser=request.user))
                    .values_list("id", flat=True))
    for m in (Message.objects.filter(conversation_id__in=conv_ids, isRead=False)
              .exclude(sender_id=uid).order_by("-id")[:30]):
        snapshot.append(("chat", {"conversationId": m.conversation_id, "messageId": m.id,
                                  "senderId": m.sender_id, "body": m.body,
                                  "createdAt": m.createdAt.isoformat()}))
    # recent feed
    for e in reversed(list(FeedEvent.objects.order_by("-timestamp")[:6])):
        snapshot.append(("feed", {"id": e.id, "eventType": e.eventType, "template": e.template,
                                  "city": e.city, "timestamp": e.timestamp.isoformat()}))

    return _streaming(sse_multiplex(snapshot, user_channels(uid), once=once))
