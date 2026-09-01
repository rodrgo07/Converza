from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
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

@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    db: Session = Depends(get_db)
):
    """
    Endpoint de verificação de Webhook exigido pela Meta/Facebook.
    Valida se o hub.verify_token coincide com o token configurado no sistema ou de alguma empresa.
    """
    if not hub_mode or not hub_verify_token:
        raise HTTPException(status_code=400, detail="Missing hub.mode or hub.verify_token parameters")

    if hub_mode == "subscribe":
        # Check global verify token or company-specific verify token
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
    """
    Endpoint que recebe eventos reais de mensagens recebidas e status de entrega/leitura da Meta WhatsApp Cloud API.
    Possui idempotência garantida através do ID único da mensagem (wamid).
    Notifica atendentes conectados em tempo real via WebSocket.
    """
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

            # 1. Identificar a conta WhatsApp correspondente ao Phone Number ID
            wa_account = None
            if phone_number_id:
                wa_account = db.query(WhatsAppAccount).filter(WhatsAppAccount.phone_number_id == phone_number_id).first()

            if not wa_account:
                # Fallback: primeira conta conectada
                wa_account = db.query(WhatsAppAccount).filter(WhatsAppAccount.is_connected == True).first()

            if not wa_account:
                logger.warning(f"Webhook recebido para phone_number_id={phone_number_id}, mas nenhuma conta encontrada.")
                continue

            company_id = wa_account.company_id

            # 2. Processar Mensagens Recebidas (Inbound)
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

                # Normalizar telefone (com DDI +55 se aplicável)
                phone_formatted = f"+{from_phone}" if not from_phone.startswith("+") else from_phone

                # Extrair conteúdo baseado no tipo
                content = ""
                media_url = None
                m_type = MessageType.TEXT

                if msg_type_str == "text":
                    content = msg_item.get("text", {}).get("body", "")
                    m_type = MessageType.TEXT
                elif msg_type_str in ["image", "audio", "video", "document"]:
                    media_data = msg_item.get(msg_type_str, {})
                    content = media_data.get("caption", f"[{msg_type_str.upper()} recebido]")
                    media_url = media_data.get("id") # media ID do WhatsApp
                    m_type = MessageType(msg_type_str)
                else:
                    content = f"[{msg_type_str} message]"

                # IDEMPOTÊNCIA: Verificar se a mensagem já foi salva anteriormente
                existing_msg = db.query(Message).filter(Message.external_id == wamid).first()
                if existing_msg:
                    logger.info(f"Mensagem já processada anteriormente (idempotência): {wamid}")
                    continue

                now = datetime.now(timezone.utc)

                # 3. Identificar ou Criar Cliente
                customer = db.query(Customer).filter(
                    Customer.company_id == company_id,
                    Customer.phone == phone_formatted
                ).first()

                if not customer:
                    customer_name = contact_profile_name or f"Lead WhatsApp ({phone_formatted[-4:]})"
                    customer = Customer(
                        company_id=company_id,
                        name=customer_name,
                        phone=phone_formatted,
                        last_interaction=now,
                        created_at=now
                    )
                    db.add(customer)
                    db.flush()

                # 4. Identificar ou Criar Conversa
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

                # 5. Salvar Mensagem no Banco
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

                # Criar Notificação interna para a equipe
                notif = Notification(
                    company_id=company_id,
                    user_id=customer.assigned_user_id or conv.assigned_user_id or 1,
                    title=f"Nova mensagem de {customer.name}",
                    message=content[:100],
                    notification_type="message",
                    link="/inbox",
                    is_read=False
                )
                db.add(notif)
                db.commit()
                db.refresh(new_msg)
                db.refresh(conv)

                # 6. Realtime WebSocket Broadcast para todos os atendentes conectados
                try:
                    await manager.broadcast_to_company(
                        company_id=company_id,
                        event_type="NEW_MESSAGE",
                        data={
                            "message": MessageOut.model_validate(new_msg).model_dump(mode="json"),
                            "conversation": ConversationOut.model_validate(conv).model_dump(mode="json")
                        }
                    )
                except Exception as b_err:
                    logger.warning(f"Erro no broadcast websocket: {b_err}")

            # 7. Processar Atualizações de Status (sent, delivered, read, failed)
            statuses = value.get("statuses", [])
            for st in statuses:
                status_wamid = st.get("id")
                status_val = st.get("status") # sent, delivered, read, failed

                if not status_wamid or not status_val:
                    continue

                msg_to_update = db.query(Message).filter(Message.external_id == status_wamid).first()
                if msg_to_update:
                    if status_val == "sent":
                        msg_to_update.status = MessageStatus.SENT
                    elif status_val == "delivered":
                        msg_to_update.status = MessageStatus.DELIVERED
                    elif status_val == "read":
                        msg_to_update.status = MessageStatus.READ
                    elif status_val == "failed":
                        msg_to_update.status = MessageStatus.FAILED
                    db.commit()
                    db.refresh(msg_to_update)

                    # Realtime Broadcast de Status
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
                        logger.warning(f"Erro no broadcast de status: {st_err}")

    return {"status": "success"}

