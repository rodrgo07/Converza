from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import (
    Conversation, Message, Customer, User, WhatsAppAccount, ConversationEvent,
    MessageDirection, MessageType, MessageStatus, UserRole
)
from app.schemas import (
    ConversationOut, ConversationDetailOut, MessageCreate, MessageOut,
    ConversationAssignRequest, ConversationTransferRequest, WhatsAppTemplateSendRequest
)
from app.services.whatsapp import WhatsAppProvider
from app.core.events import manager
from app.core.audit import log_audit
from app.core.permissions import check_permission
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[ConversationOut])
def get_conversations(
    queue: Optional[str] = None, # all, mine, unassigned, resolved, waiting
    status_filter: Optional[str] = Query(None, alias="status"),
    assigned_user_id: Optional[int] = None,
    whatsapp_account_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de conversas da empresa filtradas por fila (queue), status ou atendente responsável.
    """
    query = db.query(Conversation).filter(Conversation.company_id == current_user.company_id)

    if whatsapp_account_id:
        query = query.filter(Conversation.whatsapp_account_id == whatsapp_account_id)

    if queue == 'mine':
        query = query.filter(Conversation.assigned_user_id == current_user.id, Conversation.status != 'resolved')
    elif queue == 'unassigned':
        query = query.filter(Conversation.assigned_user_id == None, Conversation.status != 'resolved')
    elif queue == 'resolved':
        query = query.filter(Conversation.status == 'resolved')
    elif queue == 'waiting':
        query = query.filter(Conversation.status == 'waiting')
    elif status_filter:
        query = query.filter(Conversation.status == status_filter)

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

@router.post('/{conversation_id}/assign', response_model=ConversationDetailOut)
async def assign_conversation(
    conversation_id: int,
    assign_req: ConversationAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atribui a conversa a um atendente específico ou a si próprio.
    Previne concorrência via optimistic locking (expected_version).
    """
    check_permission(current_user, 'whatsapp.assign')

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.company_id == current_user.company_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail='Conversa não encontrada.')

    # Optimistic locking check
    if assign_req.expected_version is not None and conv.version != assign_req.expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='A conversa foi modificada por outro atendente. Por favor, atualize a tela.'
        )

    target_user_id = assign_req.assigned_user_id or current_user.id
    target_user = db.query(User).filter(User.id == target_user_id, User.company_id == current_user.company_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail='Atendente não encontrado na empresa.')

    previous_assigned_id = conv.assigned_user_id
    conv.assigned_user_id = target_user.id
    conv.queue = 'mine'
    conv.version = (conv.version or 1) + 1

    # Registra evento no histórico da conversa
    desc = f'Conversa assumida por {target_user.name}.' if target_user.id == current_user.id else f'Conversa atribuída a {target_user.name} por {current_user.name}.'
    event = ConversationEvent(
        conversation_id=conv.id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        event_type='ASSIGNED',
        description=desc,
        created_at=datetime.now(timezone.utc)
    )
    db.add(event)

    log_audit(
        db=db,
        company_id=current_user.company_id,
        user_id=current_user.id,
        action='CONVERSATION_ASSIGNED',
        resource='Conversation',
        resource_id=str(conv.id),
        details={'target_user_id': target_user.id, 'previous_assigned_id': previous_assigned_id}
    )

    db.commit()
    db.refresh(conv)

    # Realtime Broadcast da atribuição
    try:
        await manager.broadcast_to_company(
            company_id=current_user.company_id,
            event_type='CONVERSATION_ASSIGNED',
            data={
                'conversation_id': conv.id,
                'assigned_user_id': target_user.id,
                'assigned_user_name': target_user.name,
                'version': conv.version,
                'description': desc
            }
        )
    except Exception:
        pass

    return conv

@router.post('/{conversation_id}/transfer', response_model=ConversationDetailOut)
async def transfer_conversation(
    conversation_id: int,
    transfer_req: ConversationTransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transfere o atendimento da conversa para outro colega da equipe com notas opcionais.
    """
    check_permission(current_user, 'whatsapp.transfer')

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.company_id == current_user.company_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail='Conversa não encontrada.')

    if transfer_req.expected_version is not None and conv.version != transfer_req.expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='A conversa foi modificada por outro atendente. Por favor, atualize a tela.'
        )

    target_user = db.query(User).filter(User.id == transfer_req.target_user_id, User.company_id == current_user.company_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail='Atendente de destino não encontrado na empresa.')

    previous_assigned_id = conv.assigned_user_id
    conv.assigned_user_id = target_user.id
    conv.queue = 'mine'
    conv.version = (conv.version or 1) + 1

    desc = f'Conversa transferida por {current_user.name} para {target_user.name}.'
    if transfer_req.notes:
        desc += f' Motivo: {transfer_req.notes}'

    event = ConversationEvent(
        conversation_id=conv.id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        event_type='TRANSFERRED',
        description=desc,
        created_at=datetime.now(timezone.utc)
    )
    db.add(event)

    log_audit(
        db=db,
        company_id=current_user.company_id,
        user_id=current_user.id,
        action='CONVERSATION_TRANSFERRED',
        resource='Conversation',
        resource_id=str(conv.id),
        details={'target_user_id': target_user.id, 'previous_assigned_id': previous_assigned_id, 'notes': transfer_req.notes}
    )

    db.commit()
    db.refresh(conv)

    # Realtime Broadcast
    try:
        await manager.broadcast_to_company(
            company_id=current_user.company_id,
            event_type='CONVERSATION_TRANSFERRED',
            data={
                'conversation_id': conv.id,
                'assigned_user_id': target_user.id,
                'assigned_user_name': target_user.name,
                'transferred_by_name': current_user.name,
                'version': conv.version,
                'description': desc
            }
        )
    except Exception:
        pass

    return conv

@router.post('/{conversation_id}/resolve', response_model=ConversationDetailOut)
async def resolve_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marca o atendimento como resolvido/finalizado.
    """
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.company_id == current_user.company_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail='Conversa não encontrada.')

    conv.status = 'resolved'
    conv.queue = 'resolved'
    conv.version = (conv.version or 1) + 1

    desc = f'Atendimento finalizado por {current_user.name}.'
    event = ConversationEvent(
        conversation_id=conv.id,
        company_id=current_user.company_id,
        user_id=current_user.id,
        event_type='RESOLVED',
        description=desc,
        created_at=datetime.now(timezone.utc)
    )
    db.add(event)

    log_audit(
        db=db,
        company_id=current_user.company_id,
        user_id=current_user.id,
        action='CONVERSATION_RESOLVED',
        resource='Conversation',
        resource_id=str(conv.id)
    )

    db.commit()
    db.refresh(conv)

    try:
        await manager.broadcast_to_company(
            company_id=current_user.company_id,
            event_type='CONVERSATION_RESOLVED',
            data={'conversation_id': conv.id, 'status': 'resolved', 'version': conv.version}
        )
    except Exception:
        pass

    return conv

@router.post('/{conversation_id}/messages', response_model=MessageOut)
async def send_message(
    conversation_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Envia mensagem real através da WhatsApp Cloud API oficial da Meta.
    Identifica o atendente autor no banco (sender_id / sender_type) e atualiza todos via WebSocket.
    """
    check_permission(current_user, 'whatsapp.send')

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
        raise HTTPException(status_code=400, detail='Cliente não possui telefone válido para envio.')

    # Identificar a conta WhatsApp associada ou primária
    wa_account = None
    if conv.whatsapp_account_id:
        wa_account = db.query(WhatsAppAccount).filter(
            WhatsAppAccount.id == conv.whatsapp_account_id,
            WhatsAppAccount.company_id == current_user.company_id
        ).first()

    if not wa_account:
        wa_account = db.query(WhatsAppAccount).filter(
            WhatsAppAccount.company_id == current_user.company_id,
            WhatsAppAccount.is_connected == True
        ).first()

    if not wa_account or not wa_account.access_token or not wa_account.phone_number_id:
        raise HTTPException(
            status_code=400,
            detail={'code': 'WHATSAPP_NOT_CONNECTED', 'message': 'WhatsApp não conectado na empresa.'}
        )

    provider = WhatsAppProvider(
        phone_number_id=wa_account.phone_number_id,
        access_token=wa_account.access_token
    )

    external_msg_id = None
    now = datetime.now(timezone.utc)

    try:
        if msg_in.message_type == MessageType.TEXT:
            res = await provider.send_text_message(customer.phone, msg_in.content)
        else:
            res = await provider.send_media_message(
                customer.phone,
                msg_in.message_type.value if msg_in.message_type else 'text',
                msg_in.media_url or '',
                msg_in.content
            )

        messages_list = res.get('messages', [])
        if messages_list and isinstance(messages_list, list) and 'id' in messages_list[0]:
            external_msg_id = messages_list[0]['id']

    except ValueError as ve:
        raise HTTPException(status_code=400, detail={'code': 'WHATSAPP_CONFIG_ERROR', 'message': str(ve)})
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail={'code': 'WHATSAPP_API_ERROR', 'message': str(re)})

    new_msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        sender_type='agent',
        whatsapp_account_id=wa_account.id,
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
    conv.status = 'open'
    conv.version = (conv.version or 1) + 1
    if not conv.assigned_user_id:
        conv.assigned_user_id = current_user.id
        conv.queue = 'mine'

    if customer:
        customer.last_interaction = now

    log_audit(
        db=db,
        company_id=current_user.company_id,
        user_id=current_user.id,
        action='MESSAGE_SENT',
        resource='Message',
        resource_id=external_msg_id,
        details={'conversation_id': conv.id, 'content_preview': msg_in.content[:50]}
    )

    db.commit()
    db.refresh(new_msg)
    db.refresh(conv)

    # Realtime Broadcast do envio para todos os atendentes
    try:
        await manager.broadcast_to_company(
            company_id=current_user.company_id,
            event_type='NEW_MESSAGE',
            data={
                'message': MessageOut.model_validate(new_msg).model_dump(mode='json'),
                'conversation': ConversationOut.model_validate(conv).model_dump(mode='json')
            }
        )
    except Exception:
        pass

    return new_msg

@router.post('/{conversation_id}/template', response_model=MessageOut)
async def send_template_message(
    conversation_id: int,
    tmpl_req: WhatsAppTemplateSendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Envia template aprovado da Meta quando a janela de 24 horas estiver expirada.
    """
    check_permission(current_user, 'whatsapp.send')

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
        raise HTTPException(status_code=400, detail='Telefone do cliente inválido.')

    wa_account = db.query(WhatsAppAccount).filter(
        WhatsAppAccount.company_id == current_user.company_id,
        WhatsAppAccount.is_connected == True
    ).first()
    if not wa_account:
        raise HTTPException(status_code=400, detail='WhatsApp não conectado.')

    provider = WhatsAppProvider(
        phone_number_id=wa_account.phone_number_id,
        access_token=wa_account.access_token
    )

    try:
        res = await provider.send_template_message(
            to_phone=customer.phone,
            template_name=tmpl_req.template_name,
            language_code=tmpl_req.language_code or 'pt_BR',
            components=tmpl_req.components
        )
        external_id = res.get('messages', [{}])[0].get('id')
    except Exception as exc:
        raise HTTPException(status_code=502, detail={'code': 'TEMPLATE_SEND_FAILED', 'message': str(exc)})

    now = datetime.now(timezone.utc)
    new_msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        sender_type='agent',
        whatsapp_account_id=wa_account.id,
        direction=MessageDirection.OUTBOUND,
        message_type=MessageType.TEXT,
        content=f'[Template: {tmpl_req.template_name}]',
        status=MessageStatus.SENT,
        external_id=external_id,
        created_at=now
    )
    db.add(new_msg)
    conv.last_message_text = f'[Template: {tmpl_req.template_name}]'
    conv.last_message_time = now
    conv.status = 'open'
    db.commit()
    db.refresh(new_msg)
    return new_msg