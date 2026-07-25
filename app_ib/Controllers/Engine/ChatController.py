"""
ChatController — conversations + messages between a client and a business owner.

Real-time delivery rides the single per-user SSE connection: a sent message is
published to the recipient's `engine:chat:{uid}` channel (which their unified
/stream/ is already subscribed to). Clients SEND via REST, RECEIVE via SSE.
"""
from django.utils import timezone
from django.db.models import Q

from app_ib.Utils.EngineConfig import CONVERSATION_STATUS, NOTIFICATION_TYPE
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_, Conflict_


class _ChatController:

    # ---------------- lifecycle ----------------
    def start_conversation(self, client_user, business_id, lead_id=None):
        from app_ib.models import Conversation, Business, LeadQuery
        business = Business.objects.filter(id=business_id).first()
        if not business:
            raise NotFound_("business not found")
        lead = LeadQuery.objects.filter(id=lead_id).first() if lead_id else None
        # reuse an existing open conversation between this client and business
        existing = Conversation.objects.filter(
            clientUser=client_user, business=business,
            status__in=[CONVERSATION_STATUS.REQUESTED, CONVERSATION_STATUS.ACCEPTED]).first()
        if existing:
            return self._conv_dict(existing)
        conv = Conversation.objects.create(
            lead=lead, business=business, clientUser=client_user,
            businessUser=business.user, status=CONVERSATION_STATUS.REQUESTED)
        # let the business owner know via their unified stream
        self._notify_user(conv.businessUser_id, NOTIFICATION_TYPE.CHAT,
                          "New chat request", dedupe_key=f"conv:{conv.id}")
        return self._conv_dict(conv)

    def accept(self, user, conv_id):
        conv = self._get(conv_id)
        if conv.businessUser_id != user.id:
            raise PermissionError_("only the business owner can accept")
        conv.status = CONVERSATION_STATUS.ACCEPTED
        conv.save(update_fields=["status", "updatedAt"])
        return self._conv_dict(conv)

    def decline(self, user, conv_id, reason=""):
        conv = self._get(conv_id)
        if conv.businessUser_id != user.id:
            raise PermissionError_("only the business owner can decline")
        conv.status = CONVERSATION_STATUS.DECLINED
        conv.declineReason = reason[:255]
        conv.save(update_fields=["status", "declineReason", "updatedAt"])
        return self._conv_dict(conv)

    def close(self, user, conv_id):
        # Either participant (buyer or seller) can close an enquiry.
        conv = self._get(conv_id)
        if user.id not in (conv.clientUser_id, conv.businessUser_id):
            raise PermissionError_("only a participant can close this conversation")
        conv.status = CONVERSATION_STATUS.CLOSED
        conv.save(update_fields=["status", "updatedAt"])
        return self._conv_dict(conv)

    def mark_unread(self, user, conv_id):
        # Flip the latest incoming (other-party) message back to unread so the
        # thread shows an unread marker again (task 53 "Mark as unread").
        from app_ib.models import Message
        conv = self._get(conv_id)
        if not conv.is_participant(user.id):
            raise PermissionError_("not a participant")
        last_in = Message.objects.filter(conversation=conv).exclude(sender_id=user.id).order_by("-id").first()
        if last_in and last_in.isRead:
            last_in.isRead = False
            last_in.save(update_fields=["isRead"])
        return {"markedUnread": bool(last_in)}

    def report(self, user, conv_id, reason=""):
        # Persist a report against the enquiry as a Feedback row (no dedicated
        # model needed). Any participant may report their own conversation.
        from app_ib.models import Feedback
        conv = self._get(conv_id)
        if not conv.is_participant(user.id):
            raise PermissionError_("not a participant")
        profile = getattr(user, "user_profile", None)
        contact = (profile.email or profile.phone) if profile else ""
        biz = conv.business.businessName if conv.business_id and conv.business else "business"
        Feedback.objects.create(
            user=user, contact=contact or "",
            feedback=f"[Report] Enquiry #{conv.id} with {biz}: {reason or 'No reason given'}",
            status="report",
        )
        return {"reported": True}

    # Known label ids (mirror the frontend content labels — task 54).
    _KNOWN_LABELS = {"l_vip", "l_hot", "l_site"}

    def set_labels(self, user, conv_id, label_ids):
        conv = self._get(conv_id)
        if not conv.is_participant(user.id):
            raise PermissionError_("not a participant")
        ids = [x for x in (label_ids or []) if x in self._KNOWN_LABELS]
        # dedupe, preserve order
        seen, clean = set(), []
        for x in ids:
            if x not in seen:
                seen.add(x); clean.append(x)
        conv.labels = clean
        conv.save(update_fields=["labels", "updatedAt"])
        return self._conv_dict(conv)

    def delete(self, user, conv_id):
        # Per-participant soft delete — hides the thread from this user's list only.
        conv = self._get(conv_id)
        if user.id == conv.clientUser_id:
            conv.clientDeleted = True
            conv.save(update_fields=["clientDeleted", "updatedAt"])
        elif user.id == conv.businessUser_id:
            conv.businessDeleted = True
            conv.save(update_fields=["businessDeleted", "updatedAt"])
        else:
            raise PermissionError_("only a participant can delete this conversation")
        return {"deleted": True}

    # ---------------- messaging ----------------
    @staticmethod
    def _clean_attachments(attachments):
        # Keep only well-formed {name,url,size} entries (task 56). Cap at 10.
        out = []
        for a in (attachments or [])[:10]:
            if isinstance(a, dict) and a.get("url"):
                out.append({"name": str(a.get("name") or "file")[:255],
                            "url": str(a["url"])[:2000],
                            "size": str(a.get("size") or "")[:32]})
        return out

    def send_message(self, user, conv_id, body, attachments=None):
        from app_ib.models import Message
        from app_ib.Utils.sse_streamer import publish_chat
        conv = self._get(conv_id)
        if not conv.is_participant(user.id):
            raise PermissionError_("not a participant")
        if conv.status not in (CONVERSATION_STATUS.ACCEPTED, CONVERSATION_STATUS.REQUESTED):
            raise Conflict_(f"conversation is {conv.status}")
        attachments = self._clean_attachments(attachments)
        if not (body or "").strip() and not attachments:
            raise Conflict_("empty message")
        msg = Message.objects.create(conversation=conv, sender=user,
                                     body=(body or "").strip(), attachments=attachments)
        conv.lastMessageAt = msg.createdAt
        update_fields = ["lastMessageAt", "updatedAt"]
        # item 6: track first business-side response time
        if (conv.firstResponseSeconds is None and conv.businessUser_id == user.id
                and conv.createdAt):
            elapsed = (msg.createdAt - conv.createdAt).total_seconds()
            conv.firstResponseSeconds = max(0, int(elapsed))
            update_fields.append("firstResponseSeconds")
        conv.save(update_fields=update_fields)
        payload = {"conversationId": conv.id, "messageId": msg.id, "senderId": user.id,
                   "body": msg.body, "createdAt": msg.createdAt.isoformat(),
                   "senderName": self._display_name(user), "attachments": msg.attachments}
        # deliver to the OTHER party over their single per-user SSE connection
        publish_chat(conv.other_party(user.id), payload)
        # also raise an unread notification (deduped per conversation)
        preview = msg.body[:80] or "Sent an attachment"
        self._notify_user(conv.other_party(user.id), NOTIFICATION_TYPE.CHAT,
                          "New message", body=preview, dedupe_key=f"conv:{conv.id}")
        return {"messageId": msg.id, "createdAt": msg.createdAt.isoformat(),
                "senderName": self._display_name(user), "attachments": msg.attachments}

    def history(self, user, conv_id, before_id=None, limit=30):
        from app_ib.models import Message
        conv = self._get(conv_id)
        if not conv.is_participant(user.id):
            raise PermissionError_("not a participant")
        qs = Message.objects.filter(conversation=conv) \
            .select_related("sender", "sender__user_profile")
        if before_id:
            qs = qs.filter(id__lt=before_id)
        rows = list(qs.order_by("-id")[:limit])
        rows.reverse()
        return [{"messageId": m.id, "senderId": m.sender_id, "body": m.body,
                 "isRead": m.isRead, "createdAt": m.createdAt.isoformat(),
                 "senderName": self._display_name(m.sender),
                 "attachments": m.attachments if isinstance(m.attachments, list) else []} for m in rows]

    def poll_messages(self, user, since_id=0, limit=100):
        """Polling replacement for the SSE `chat` event: new INCOMING messages
        (sent by the other party) across all of the user's conversations.

        `since_id` is the highest messageId the client already has; pass 0 on the
        first poll to seed the last `limit` incoming messages (the client dedupes
        by id). Returns the SAME flat payload the SSE stream published, so the
        frontend adapter/Redux path is unchanged. SSE delivery is left in place."""
        from app_ib.models import Conversation, Message
        conv_ids = list(Conversation.objects.filter(Q(clientUser=user) | Q(businessUser=user))
                        .values_list("id", flat=True))
        qs = (Message.objects.filter(conversation_id__in=conv_ids)
              .exclude(sender_id=user.id)
              .select_related("sender", "sender__user_profile"))
        if since_id:
            rows = list(qs.filter(id__gt=since_id).order_by("id")[:limit])
        else:
            # first poll — seed the most recent incoming messages, oldest-first
            rows = list(qs.order_by("-id")[:min(limit, 30)])
            rows.reverse()
        return [{"conversationId": m.conversation_id, "messageId": m.id,
                 "senderId": m.sender_id, "body": m.body,
                 "createdAt": m.createdAt.isoformat(),
                 "senderName": self._display_name(m.sender),
                 "attachments": m.attachments if isinstance(m.attachments, list) else []} for m in rows]

    def conversation_events(self, user, conv_id):
        """Synthesize a real activity feed for a conversation from its actual data
        (task 57a): started → first seller reply → status transition → last activity.
        No fabricated events — everything is derived from the conversation + messages."""
        from app_ib.models import Message

        def _fmt(dt):
            return dt.strftime("%d %b, %I:%M %p") if dt else ""

        conv = self._get(conv_id)
        if not conv.is_participant(user.id):
            raise PermissionError_("not a participant")
        # (timestamp, payload) — the feed is SORTED by timestamp at the end, never by
        # the order we happen to append in: a status transition (updatedAt) can predate
        # the last message, and the first reply can postdate an accept.
        events = []

        def _add(dt, event, icon):
            if dt:
                events.append((dt, {"event": event, "when": _fmt(dt), "icon": icon}))

        _add(conv.createdAt, "Connection started", "ti-link")
        # First seller (business-side) reply — the moment they engaged.
        first_reply = (Message.objects.filter(conversation=conv, sender_id=conv.businessUser_id)
                       .order_by("id").first())
        if first_reply:
            _add(first_reply.createdAt, "Seller replied", "ti-message-2")
        # Status transition (accepted/declined/closed) — updatedAt is the transition time.
        status_labels = {
            CONVERSATION_STATUS.ACCEPTED: ("Connection accepted", "ti-check"),
            CONVERSATION_STATUS.DECLINED: ("Connection declined", "ti-x"),
            CONVERSATION_STATUS.CLOSED: ("Connection closed", "ti-flag-check"),
        }
        if conv.status in status_labels:
            label, icon = status_labels[conv.status]
            _add(conv.updatedAt, label, icon)
        # Last message activity — only if distinct from the events above, otherwise it
        # renders as a duplicate row at the same timestamp (e.g. the only message IS
        # the seller's first reply).
        if conv.lastMessageAt and all(dt != conv.lastMessageAt for dt, _ in events):
            _add(conv.lastMessageAt, "Last activity", "ti-clock")
        return {"events": [payload for _, payload in sorted(events, key=lambda e: e[0])]}

    def mark_read(self, user, conv_id):
        from app_ib.models import Message
        conv = self._get(conv_id)
        if not conv.is_participant(user.id):
            raise PermissionError_("not a participant")
        # mark the OTHER party's messages as read
        updated = Message.objects.filter(conversation=conv, isRead=False) \
            .exclude(sender_id=user.id).update(isRead=True)
        return {"markedRead": updated}

    def list_conversations(self, user):
        from app_ib.models import Conversation, Message
        # Exclude threads this user has soft-deleted (task 53).
        convs = Conversation.objects.filter(Q(clientUser=user) | Q(businessUser=user)) \
            .exclude(Q(clientUser=user, clientDeleted=True) | Q(businessUser=user, businessDeleted=True)) \
            .select_related("business", "clientUser", "clientUser__user_profile", "lead") \
            .order_by("-lastMessageAt", "-createdAt")[:100]
        out = []
        for c in convs:
            last = Message.objects.filter(conversation=c).order_by("-id").first()
            unread = Message.objects.filter(conversation=c, isRead=False).exclude(sender_id=user.id).count()
            out.append({**self._conv_dict(c),
                        "lastMessage": last.body if last else "",
                        "unreadCount": unread})
        return out

    # ---------------- helpers ----------------
    def _get(self, conv_id):
        from app_ib.models import Conversation
        conv = Conversation.objects.filter(id=conv_id).first()
        if not conv:
            raise NotFound_("conversation not found")
        return conv

    def _conv_dict(self, c):
        # Additive display fields (businessName/clientName/lead*) feed the v3
        # dashboards so they never need extra round-trips per conversation.
        biz = c.business if c.business_id else None
        lead = c.lead if c.lead_id else None
        return {"conversationId": c.id, "status": c.status, "businessId": c.business_id,
                "clientUserId": c.clientUser_id, "businessUserId": c.businessUser_id,
                "leadId": c.lead_id,
                "lastMessageAt": c.lastMessageAt.isoformat() if c.lastMessageAt else None,
                "createdAt": c.createdAt.isoformat() if c.createdAt else None,
                "businessName": biz.businessName if biz else "",
                "businessImageUrl": (biz.coverImageUrl or "") if biz else "",
                "businessPhone": (biz.whatsapp or "") if biz else "",
                "clientName": self._display_name(c.clientUser if c.clientUser_id else None),
                "leadInterested": (lead.interested or "") if lead else "",
                "leadCity": (lead.city or "") if lead else "",
                "leadQuery": (lead.query or "") if lead else "",
                # Real lead provenance so the seller brief shows the true form type /
                # source instead of a hardcoded "Contact / Shop" (task 212).
                "leadFormType": (lead.formType or "") if lead else "",
                "leadSourceChannel": (lead.sourceChannel or "") if lead else "",
                "leadOriginType": (lead.originType or "") if lead else "",
                "labels": c.labels if isinstance(c.labels, list) else [],
                "sellerVerified": bool(biz.isVerified) if biz else False,
                # Contact reveal gated: only expose the seller's email once the
                # enquiry is active/accepted (task 57b, matches the prototype).
                "sellerEmail": self._seller_email(biz)
                               if c.status == CONVERSATION_STATUS.ACCEPTED else ""}

    @staticmethod
    def _seller_email(biz):
        if not biz or not biz.user_id:
            return ""
        profile = getattr(biz.user, "user_profile", None)
        return (profile.email or "") if profile else ""

    def _display_name(self, user):
        """Profile name, else the email local-part — never the raw email."""
        if not user:
            return "User"
        profile = getattr(user, "user_profile", None)
        name = (profile.name or "").strip() if profile else ""
        if not name:
            name = (user.username or "").split("@")[0]
        return name or "User"

    def _notify_user(self, user_id, ntype, title, body="", dedupe_key=""):
        from app_ib.models import CustomUser
        from app_ib.algorithms.state import notify
        u = CustomUser.objects.filter(id=user_id).first()
        if u:
            notify(u, ntype, title, body=body, dedupe_key=dedupe_key)


CHAT_CONTROLLER = _ChatController()
