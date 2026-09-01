from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Conversation, Message, Customer, User, WhatsAppAccount, MessageDirection, MessageType, MessageStatus
from app.schemas import ConversationOut, ConversationDetailOut, MessageCreate, MessageOut
from app.services.whatsapp import WhatsAppProvider
from app.api.deps import get_current_user

router = APIRouter()

@router.get('/', response_model=List[ConversationOut])
def get_conversations(
    status: Optional[str] = None,
    assigned_user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Conversation).filter(Conversation.company_id == current_user.company_id)
    if status:
        query = query.filter(Conversation.status == status)
    if assigned_user_id:
        query = query.filter(Conversation.assigned_user_id == assigned_user_id)

    return query.order_by(Conversation.last_message_time.desc().nullslast(), Conversation.created_at.desc()).all()

@router.get('/{conversation_id}', response_model=ConversationDetailOut)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.company_id == current_user.company_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail='Conversa não encontrada.')

    if conv.unread_count > 0:
        conv.unread_count = 0
        db.commit()
        db.refresh(conv)

    return conv

@router.post('/{conversation_id}/messages', response_model=MessageOut)
async def send_message(
    conversation_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.company_id == current_user.company_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail='Conversa não encontrada.')

    customer = db.query(Customer).filter(
        Customer.id == conv.customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer or not customer.phone:
        raise HTTPException(status_code=400, detail='Cliente não possui telefone cadastrado para envio.')

    wa_account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()

    provider = WhatsAppProvider(
        phone_number_id=wa_account.phone_number_id if wa_account else None,
        access_token=wa_account.access_token if wa_account else None
    )

    external_msg_id = None
    try:
        if msg_in.message_type == MessageType.TEXT:
            res = await provider.send_text_message(customer.phone, msg_in.content)
        else:
            res = await provider.send_media_message(customer.phone, msg_in.message_type.value, msg_in.media_url or '', msg_in.content)
        
        # Capture Meta wamid if returned
        messages_list = res.get("messages", [])
        if messages_list and isinstance(messages_list, list) and "id" in messages_list[0]:
            external_msg_id = messages_list[0]["id"]

    except ValueError as ve:
        raise HTTPException(status_code=400, detail={"code": "WHATSAPP_NOT_CONNECTED", "message": str(ve)})
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail={"code": "WHATSAPP_API_ERROR", "message": str(re)})

    now = datetime.now(timezone.utc)
    new_msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        direction=MessageDirection.OUTBOUND,
        message_type=msg_in.message_type or MessageType.TEXT,
        content=msg_in.content,
        media_url=msg_in.media_url,
        status=MessageStatus.SENT,
        external_id=external_msg_id,
        created_at=now
    )
    db.add(new_msg)

    conv.last_message_text = msg_in.content
    conv.last_message_time = now
    if customer:
        customer.last_interaction = now

    db.commit()
    db.refresh(new_msg)
    return new_msg