from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import FollowUp, User, FollowUpStatus
from app.schemas import FollowUpOut, FollowUpCreate, FollowUpUpdate
from app.api.deps import get_current_user

router = APIRouter()

@router.get('/', response_model=List[FollowUpOut])
def get_follow_ups(
    status: Optional[FollowUpStatus] = None,
    customer_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FollowUp).filter(FollowUp.company_id == current_user.company_id)
    if status:
        query = query.filter(FollowUp.status == status)
    if customer_id:
        query = query.filter(FollowUp.customer_id == customer_id)
    return query.order_by(FollowUp.due_date.asc()).all()

@router.post('/', response_model=FollowUpOut)
def create_follow_up(
    fu_in: FollowUpCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fu = FollowUp(
        company_id=current_user.company_id,
        customer_id=fu_in.customer_id,
        assigned_user_id=fu_in.assigned_user_id or current_user.id,
        title=fu_in.title,
        notes=fu_in.notes,
        due_date=fu_in.due_date,
        status=FollowUpStatus.PENDING
    )
    db.add(fu)
    db.commit()
    db.refresh(fu)
    return fu

@router.put('/{follow_up_id}', response_model=FollowUpOut)
def update_follow_up(
    follow_up_id: int,
    fu_in: FollowUpUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fu = db.query(FollowUp).filter(
        FollowUp.id == follow_up_id,
        FollowUp.company_id == current_user.company_id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail='Follow-up não encontrado.')

    update_data = fu_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(fu, field, val)

    db.commit()
    db.refresh(fu)
    return fu

@router.delete('/{follow_up_id}')
def delete_follow_up(
    follow_up_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fu = db.query(FollowUp).filter(
        FollowUp.id == follow_up_id,
        FollowUp.company_id == current_user.company_id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail='Follow-up não encontrado.')

    db.delete(fu)
    db.commit()
    return {'message': 'Follow-up removido com sucesso.'}
