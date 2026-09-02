from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Task, User, TaskStatus
from app.schemas import TaskOut, TaskCreate, TaskUpdate
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[TaskOut])
def get_tasks(
    status: Optional[TaskStatus] = None,
    customer_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task).filter(Task.company_id == current_user.company_id)
    if status:
        query = query.filter(Task.status == status)
    if customer_id:
        query = query.filter(Task.customer_id == customer_id)
    return query.order_by(Task.due_date.asc().nullslast()).all()

@router.post("", response_model=TaskOut)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = Task(
        company_id=current_user.company_id,
        customer_id=task_in.customer_id,
        assigned_user_id=task_in.assigned_user_id or current_user.id,
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        status=TaskStatus.PENDING
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put('/{task_id}', response_model=TaskOut)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.company_id == current_user.company_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail='Tarefa não encontrada.')

    update_data = task_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(task, field, val)

    db.commit()
    db.refresh(task)
    return task

@router.delete('/{task_id}')
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.company_id == current_user.company_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail='Tarefa não encontrada.')

    db.delete(task)
    db.commit()
    return {'message': 'Tarefa removida com sucesso.'}
