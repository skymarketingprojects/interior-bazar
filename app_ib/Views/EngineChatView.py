"""Chat REST views (sync DRF, auth required). Messages are SENT here and RECEIVED
over the single per-user SSE connection (/api/v1/engine/stream/)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Engine.ChatController import CHAT_CONTROLLER
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_, Conflict_


def _ok(data, msg="ok"):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=msg, data=data)


def _err(e):
    if isinstance(e, NotFound_):
        return ServerResponse(response=False, code=RESPONSE_CODES.not_exist, message=str(e), data={})
    if isinstance(e, PermissionError_):
        return ServerResponse(response=False, code=RESPONSE_CODES.forbidden, message=str(e), data={})
    if isinstance(e, Conflict_):
        return ServerResponse(response=False, code=RESPONSE_CODES.conflict, message=str(e), data={})
    return ServerResponse(response=False, code=RESPONSE_CODES.error, message=str(e), data={})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def ConversationListCreateView(request):
    if request.method == "POST":
        biz = request.data.get("businessId")
        if not biz:
            return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                                  message="businessId required", data={})
        try:
            return _ok(CHAT_CONTROLLER.start_conversation(request.user, biz, request.data.get("leadId")),
                       "Conversation started")
        except Exception as e:
            return _err(e)
    return _ok(CHAT_CONTROLLER.list_conversations(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ConversationAcceptView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.accept(request.user, convId), "Accepted")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ConversationDeclineView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.decline(request.user, convId, request.data.get("reason", "")), "Declined")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ConversationCloseView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.close(request.user, convId), "Closed")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ConversationMarkUnreadView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.mark_unread(request.user, convId), "Marked unread")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ConversationReportView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.report(request.user, convId, request.data.get("reason", "")), "Reported")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ConversationDeleteView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.delete(request.user, convId), "Deleted")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ConversationLabelsView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.set_labels(request.user, convId, request.data.get("labels", [])), "Labels updated")
    except Exception as e:
        return _err(e)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def MessagesView(request, convId):
    try:
        if request.method == "POST":
            body = request.data.get("body", "")
            attachments = request.data.get("attachments", [])
            return _ok(CHAT_CONTROLLER.send_message(request.user, convId, body, attachments), "Message sent")
        before = request.GET.get("before_id")
        return _ok(CHAT_CONTROLLER.history(request.user, convId, int(before) if before else None))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def MessagesReadView(request, convId):
    try:
        return _ok(CHAT_CONTROLLER.mark_read(request.user, convId), "Marked read")
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ChatPollView(request):
    """Polling endpoint: new incoming messages since `?since=<messageId>` across
    all of the user's conversations. Polling replacement for the SSE `chat` event;
    the SSE stream (/engine/stream/) is kept in place for future scale."""
    since = request.GET.get("since")
    try:
        since_id = int(since) if since else 0
    except (TypeError, ValueError):
        since_id = 0
    try:
        return _ok(CHAT_CONTROLLER.poll_messages(request.user, since_id))
    except Exception as e:
        return _err(e)
