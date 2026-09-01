from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import PipelineStage, Opportunity, Customer, User
from app.schemas import (
    PipelineStageOut, PipelineStageCreate,
    OpportunityOut, OpportunityCreate, OpportunityUpdate,
    KanbanColumn
)
from app.api.deps import get_current_user

router = APIRouter()

@router.get('/stages', response_model=List[PipelineStageOut])
def get_stages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(PipelineStage).filter(
        PipelineStage.company_id == current_user.company_id
    ).order_by(PipelineStage.order.asc()).all()

@router.get('/kanban', response_model=List[KanbanColumn])
def get_kanban_board(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stages = db.query(PipelineStage).filter(
        PipelineStage.company_id == current_user.company_id
    ).order_by(PipelineStage.order.asc()).all()

    kanban_columns = []
    for stage in stages:
        opps = db.query(Opportunity).filter(
            Opportunity.stage_id == stage.id,
            Opportunity.company_id == current_user.company_id
        ).order_by(Opportunity.updated_at.desc()).all()

        total_val = sum(o.value for o in opps)
        kanban_columns.append(
            KanbanColumn(
                stage=PipelineStageOut.model_validate(stage),
                opportunities=[OpportunityOut.model_validate(o) for o in opps],
                total_value=round(total_val, 2),
                count=len(opps)
            )
        )
    return kanban_columns

@router.get('/opportunities', response_model=List[OpportunityOut])
def get_opportunities(
    customer_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Opportunity).filter(Opportunity.company_id == current_user.company_id)
    if customer_id:
        query = query.filter(Opportunity.customer_id == customer_id)
    return query.order_by(Opportunity.created_at.desc()).all()

@router.post('/opportunities', response_model=OpportunityOut)
def create_opportunity(
    opp_in: OpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    opp = Opportunity(
        company_id=current_user.company_id,
        customer_id=opp_in.customer_id,
        stage_id=opp_in.stage_id,
        title=opp_in.title,
        value=opp_in.value,
        probability=opp_in.probability,
        expected_close_date=opp_in.expected_close_date,
        assigned_user_id=opp_in.assigned_user_id or current_user.id,
        notes=opp_in.notes
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

@router.put('/opportunities/{opportunity_id}', response_model=OpportunityOut)
def update_opportunity(
    opportunity_id: int,
    opp_in: OpportunityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    opp = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.company_id == current_user.company_id
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail='Oportunidade não encontrada.')

    update_data = opp_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(opp, field, val)

    opp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(opp)
    return opp

@router.delete('/opportunities/{opportunity_id}')
def delete_opportunity(
    opportunity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    opp = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.company_id == current_user.company_id
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail='Oportunidade não encontrada.')

    db.delete(opp)
    db.commit()
    return {'message': 'Oportunidade removida com sucesso.'}
