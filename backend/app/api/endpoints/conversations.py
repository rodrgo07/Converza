from typing import List, Optional
from datetime import datetime
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

    return query.order_by(Conversation.last_message_time.desc()).all()

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
        raise HTTPException(status_code=404, detail='Conversa nao encontrada.')

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
        raise HTTPException(status_code=404, detail='Conversa nao encontrada.')

    customer = db.query(Customer).filter(Customer.id == conv.customer_id).first()
    wa_account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()

    provider = WhatsAppProvider(
        phone_number_id=wa_account.phone_number_id if wa_account else None,
        access_token=wa_account.access_token if wa_account else None
    )

    if msg_in.message_type == MessageType.TEXT:
        await provider.send_text_message(customer.phone, msg_in.content)
    else:
        await provider.send_media_message(customer.phone, msg_in.message_type.value, msg_in.media_url or '', msg_in.content)

    new_msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        direction=MessageDirection.OUTBOUND,
        message_type=msg_in.message_type or MessageType.TEXT,
        content=msg_in.content,
        media_url=msg_in.media_url,
        status=MessageStatus.DELIVERED,
        created_at=datetime.utcnow()
    )
    db.add(new_msg)

    conv.last_message_text = msg_in.content
    conv.last_message_time = datetime.utcnow()
    customer.last_interaction = datetime.utcnow()

    db.commit()
    db.refresh(new_msg)
    return new_msg

@router.post('/{conversation_id}/simulate-receive', response_model=MessageOut)
def simulate_customer_reply(
    conversation_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Simulate an incoming message from the customer
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.company_id == current_user.company_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail='Conversa nao encontrada.')

    customer = db.query(Customer).filter(Customer.id == conv.customer_id).first()

    new_msg = Message(
        conversation_id=conv.id,
        sender_id=None,
        direction=MessageDirection.INBOUND,
        message_type=msg_in.message_type or MessageType.TEXT,
        content=msg_in.content,
        media_url=msg_in.media_url,
        status=MessageStatus.READ,
        created_at=datetime.utcnow()
    )
    db.add(new_msg)

    conv.last_message_text = msg_in.content
    conv.last_message_time = datetime.utcnow()
    conv.unread_count = (conv.unread_count or 0) + 1
    if customer:
        customer.last_interaction = datetime.utcnow()

    db.commit()
    db.refresh(new_msg)
    return new_msg
