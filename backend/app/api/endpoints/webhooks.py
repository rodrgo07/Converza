from typing import Dict, Any, Optional
import logging
import hashlib
import hmac
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.session import get_db
from app.core.config import settings
from app.core.events import manager
from app.models import (
    WhatsAppAccount, Company, Customer, Conversation, Message,
    MessageDirection, MessageType, MessageStatus, Notification, ConversationEvent
)
from app.schemas import MessageOut, ConversationOut

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_meta_signature(request_body: bytes, signature_header: Optional[str], app_secret: Optional[str]) -> bool:
    if not app_secret or not signature_header:
        return False
    try:
        expected = "sha256=" + hmac.new(
            app_secret.encode("utf-8"),
            request_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)
    except Exception:
        return False


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    db: Session = Depends(get_db)
):
    if not hub_mode or not hub_verify_token:
        raise HTTPException(status_code=400, detail="Missing hub.mode or hub.verify_token parameters")

    if hub_mode == "subscribe":
        if hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            return Response(content=hub_challenge or "", media_type="text/plain")

        wa_acc = db.query(WhatsAppAccount).filter(WhatsAppAccount.webhook_verify_token == hub_verify_token).first()
        if wa_acc:
            return Response(content=hub_challenge or "", media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/whatsapp")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.body()

    signature_header = request.headers.get("X-Hub-Signature-256")
    if settings.WHATSAPP_APP_SECRET:
        if not verify_meta_signature(body, signature_header, settings.WHATSAPP_APP_SECRET):
            logger.warning("Webhook signature verification failed — rejected request.")
            return JSONResponse(status_code=403, content={"error": "Invalid signature"})

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "Invalid JSON body"}

    entry_list = payload.get("entry", [])
    if not entry_list or not isinstance(entry_list, list):
        return {"status": "ignored", "reason": "No entries in payload"}

    for entry in entry_list:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")

            wa_account = None
            if phone_number_id:
                wa_account = db.query(WhatsAppAccount).filter(
                    WhatsAppAccount.phone_number_id == phone_number_id,
                    WhatsAppAccount.is_connected == True
                ).first()

            if not wa_account:
                logger.warning(f"Webhook received for unknown phone_number_id={phone_number_id}. Skipping.")
                continue

            company_id = wa_account.company_id

            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            contact_profile_name = ""
            if contacts and isinstance(contacts, list):
                contact_profile_name = contacts[0].get("profile", {}).get("name", "")

            for msg_item in messages:
                wamid = msg_item.get("id")
                from_phone = msg_item.get("from")
                msg_type_str = msg_item.get("type", "text")
                timestamp_str = msg_item.get("timestamp")

                if not from_phone:
                    continue

                phone_formatted = f"+{from_phone}" if not from_phone.startswith("+") else from_phone

                content = ""
                media_url = None
                m_type = MessageType.TEXT

                if msg_type_str == "text":
                    content = msg_item.get("text", {}).get("body", "")
                    m_type = MessageType.TEXT
                elif msg_type_str in ["image", "audio", "video", "document"]:
                    media_data = msg_item.get(msg_type_str, {})
                    content = media_data.get("caption", f"[{msg_type_str.upper()} recebido]")
                    media_url = media_data.get("id")
                    m_type = MessageType(msg_type_str)
                else:
                    content = f"[{msg_type_str} message]"

                existing_msg = db.query(Message).filter(Message.external_id == wamid).first()
                if existing_msg:
                    logger.info(f"Mensagem já processada (idempotência): {wamid}")
                    continue

                now = datetime.now(timezone.utc)

                customer = db.query(Customer).filter(
                    Customer.company_id == company_id,
                    Customer.phone == phone_formatted
                ).first()

                if not customer:
                    customer_name = contact_profile_name or f"Lead ({phone_formatted[-4:]})"
                    customer = Customer(
                        company_id=company_id,
                        name=customer_name,
                        phone=phone_formatted,
                        last_interaction=now,
                        created_at=now
                    )
                    db.add(customer)
                    db.flush()

                conv = db.query(Conversation).filter(
                    Conversation.company_id == company_id,
                    Conversation.customer_id == customer.id
                ).first()

                if not conv:
                    conv = Conversation(
                        company_id=company_id,
                        customer_id=customer.id,
                        whatsapp_account_id=wa_account.id,
                        assigned_user_id=customer.assigned_user_id,
                        status="open",
                        queue="mine" if customer.assigned_user_id else "unassigned",
                        unread_count=1,
                        last_message_text=content,
                        last_message_time=now,
                        last_inbound_time=now,
                        version=1,
                        created_at=now
                    )
                    db.add(conv)
                    db.flush()
                else:
                    conv.unread_count = (conv.unread_count or 0) + 1
                    conv.last_message_text = content
                    conv.last_message_time = now
                    conv.last_inbound_time = now
                    conv.whatsapp_account_id = wa_account.id
                    conv.status = "open"
                    if not conv.assigned_user_id:
                        conv.queue = "unassigned"
                    conv.version = (conv.version or 1) + 1

                customer.last_interaction = now

                new_msg = Message(
                    conversation_id=conv.id,
                    sender_id=None,
                    sender_type="customer",
                    whatsapp_account_id=wa_account.id,
                    direction=MessageDirection.INBOUND,
                    message_type=m_type,
                    content=content,
                    media_url=media_url,
                    status=MessageStatus.DELIVERED,
                    external_id=wamid,
                    created_at=now
                )
                db.add(new_msg)

                target_user_id = customer.assigned_user_id or conv.assigned_user_id
                if target_user_id:
                    notif = Notification(
                        company_id=company_id,
                        user_id=target_user_id,
                        title=f"Nova mensagem de {customer.name}",
                        message=content[:100],
                        notification_type="message",
                        link="/inbox",
                        is_read=False
                    )
                    db.add(notif)

            statuses = value.get("statuses", [])
            for st in statuses:
                status_wamid = st.get("id")
                status_val = st.get("status")

                if not status_wamid or not status_val:
                    continue

                msg_to_update = db.query(Message).filter(Message.external_id == status_wamid).first()
                if msg_to_update:
                    status_map = {
                        "sending": MessageStatus.SENDING,
                        "sent": MessageStatus.SENT,
                        "delivered": MessageStatus.DELIVERED,
                        "read": MessageStatus.READ,
                        "failed": MessageStatus.FAILED,
                    }
                    new_status = status_map.get(status_val)
                    if new_status:
                        msg_to_update.status = new_status
                    if status_val == "failed":
                        errors = st.get("errors", [])
                        if errors:
                            msg_to_update.error_message = str(errors[0].get("message", "Unknown error"))

            db.commit()

            for msg_item in messages:
                wamid = msg_item.get("id")
                msg_obj = db.query(Message).filter(Message.external_id == wamid).first()
                if not msg_obj:
                    continue
                conv = db.query(Conversation).filter(Conversation.id == msg_obj.conversation_id).first()
                if not conv:
                    continue
                try:
                    await manager.broadcast_to_company(
                        company_id=conv.company_id,
                        event_type="NEW_MESSAGE",
                        data={
                            "message": MessageOut.model_validate(msg_obj).model_dump(mode="json"),
                            "conversation": ConversationOut.model_validate(conv).model_dump(mode="json")
                        }
                    )
                except Exception as b_err:
                    logger.warning(f"WebSocket broadcast error: {b_err}")

            for st in statuses:
                status_wamid = st.get("id")
                if not status_wamid:
                    continue
                msg_to_update = db.query(Message).filter(Message.external_id == status_wamid).first()
                if not msg_to_update:
                    continue
                try:
                    conv = db.query(Conversation).filter(Conversation.id == msg_to_update.conversation_id).first()
                    if conv:
                        await manager.broadcast_to_company(
                            company_id=conv.company_id,
                            event_type="MESSAGE_STATUS_UPDATE",
                            data={
                                "message_id": msg_to_update.id,
                                "external_id": msg_to_update.external_id,
                                "status": msg_to_update.status.value,
                                "conversation_id": conv.id
                            }
                        )
                except Exception as st_err:
                    logger.warning(f"Status broadcast error: {st_err}")

    return {"status": "success"}
