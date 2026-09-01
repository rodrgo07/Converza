from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import (
    Customer, CustomerTag, Tag, User, Conversation, Message,
    MessageDirection, MessageType, MessageStatus, Company, Subscription
)
from app.schemas import CustomerCreate, CustomerUpdate, CustomerOut
from app.api.deps import get_current_user, get_current_company

router = APIRouter()

@router.get('/', response_model=List[CustomerOut])
def get_customers(
    search: Optional[str] = None,
    filter_stage: Optional[str] = None,
    tag_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Customer).filter(Customer.company_id == current_user.company_id)

    if search:
        s = f'%{search}%'
        query = query.filter((Customer.name.ilike(s)) | (Customer.phone.ilike(s)) | (Customer.company_name.ilike(s)))

    if tag_id:
        query = query.join(CustomerTag).filter(CustomerTag.tag_id == tag_id)

    customers = query.order_by(Customer.last_interaction.desc().nullslast(), Customer.created_at.desc()).offset(skip).limit(limit).all()
    return customers

@router.post('/', response_model=CustomerOut)
def create_customer(
    customer_in: CustomerCreate,
    current_user: User = Depends(get_current_user),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    # Rule: Plan max customers validation
    sub = db.query(Subscription).filter(Subscription.company_id == company.id).first()
    max_allowed = sub.max_customers if sub else 100
    current_count = db.query(Customer).filter(Customer.company_id == company.id).count()

    if current_count >= max_allowed:
        raise HTTPException(
            status_code=403,
            detail=f'Limite do plano atingido ({max_allowed} clientes). Faça upgrade da sua assinatura para cadastrar mais clientes.'
        )

    now = datetime.now(timezone.utc)
    customer = Customer(
        company_id=company.id,
        name=customer_in.name,
        phone=customer_in.phone,
        email=customer_in.email,
        company_name=customer_in.company_name,
        notes=customer_in.notes,
        assigned_user_id=customer_in.assigned_user_id or current_user.id,
        last_interaction=now,
        created_at=now
    )
    db.add(customer)
    db.flush()

    if customer_in.tag_ids:
        for tid in customer_in.tag_ids:
            ct = CustomerTag(customer_id=customer.id, tag_id=tid)
            db.add(ct)

    # Automatically create the real conversation thread in PostgreSQL
    conversation = Conversation(
        company_id=current_user.company_id,
        customer_id=customer.id,
        assigned_user_id=customer.assigned_user_id,
        status='open',
        unread_count=0,
        last_message_text=None,
        last_message_time=now,
        created_at=now
    )
    db.add(conversation)

    db.commit()
    db.refresh(customer)
    return customer

@router.get('/{customer_id}', response_model=CustomerOut)
def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')
    return customer

@router.put('/{customer_id}', response_model=CustomerOut)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')

    update_data = customer_in.model_dump(exclude_unset=True)
    if 'tag_ids' in update_data:
        tag_ids = update_data.pop('tag_ids')
        if tag_ids is not None:
            db.query(CustomerTag).filter(CustomerTag.customer_id == customer.id).delete()
            for tid in tag_ids:
                db.add(CustomerTag(customer_id=customer.id, tag_id=tid))

    for field, value in update_data.items():
        setattr(customer, field, value)

    customer.last_interaction = datetime.now(timezone.utc)
    db.commit()
    db.refresh(customer)
    return customer

@router.delete('/{customer_id}')
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')

    db.delete(customer)
    db.commit()
    return {'message': 'Cliente removido com sucesso.'}