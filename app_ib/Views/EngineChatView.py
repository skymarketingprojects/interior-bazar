"""Chat REST views (sync DRF, auth required). Messages are SENT here and RECEIVED
over the single per-user SSE connection (/api/v1/engine/stream/).

Canonical responder stack (task 20): @exceptionHandler(responseFunc=ServerResponse,
errorMessage=...) wraps each view — the decorator maps controller NotFound_/
PermissionError_/Conflict_ to 410/403/409 and any other exception to a clean envelope;
views return ServerResponse(...) directly (no local _ok/_err wrappers, no per-view try/except)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Controllers.Engine.ChatController import CHAT_CONTROLLER


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationListCreateView(request):
    if request.method == "POST":
        biz = request.data.get("businessId")
        if not biz:
            return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                                  message=RESPONSE_MESSAGES.business_id_required, data={})
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_started,
                              data=CHAT_CONTROLLER.start_conversation(request.user, biz, request.data.get("leadId")))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=CHAT_CONTROLLER.list_conversations(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationAcceptView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_accepted,
                          data=CHAT_CONTROLLER.accept(request.user, convId))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationDeclineView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_declined,
                          data=CHAT_CONTROLLER.decline(request.user, convId, request.data.get("reason", "")))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationCloseView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_closed,
                          data=CHAT_CONTROLLER.close(request.user, convId))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationMarkUnreadView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_marked_unread,
                          data=CHAT_CONTROLLER.mark_unread(request.user, convId))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationReportView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_reported,
                          data=CHAT_CONTROLLER.report(request.user, convId, request.data.get("reason", "")))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationDeleteView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_deleted,
                          data=CHAT_CONTROLLER.delete(request.user, convId))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationLabelsView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.conversation_labels_updated,
                          data=CHAT_CONTROLLER.set_labels(request.user, convId, request.data.get("labels", [])))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ConversationEventsView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=CHAT_CONTROLLER.conversation_events(request.user, convId))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MessagesView(request, convId):
    if request.method == "POST":
        body = request.data.get("body", "")
        attachments = request.data.get("attachments", [])
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.message_sent,
                              data=CHAT_CONTROLLER.send_message(request.user, convId, body, attachments))
    before = request.GET.get("before_id")
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=CHAT_CONTROLLER.history(request.user, convId, int(before) if before else None))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MessagesReadView(request, convId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.messages_marked_read,
                          data=CHAT_CONTROLLER.mark_read(request.user, convId))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ChatPollView(request):
    """Polling endpoint: new incoming messages since `?since=<messageId>` across
    all of the user's conversations. Polling replacement for the SSE `chat` event;
    the SSE stream (/engine/stream/) is kept in place for future scale."""
    since = request.GET.get("since")
    try:
        since_id = int(since) if since else 0
    except (TypeError, ValueError):
        since_id = 0
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=CHAT_CONTROLLER.poll_messages(request.user, since_id))
