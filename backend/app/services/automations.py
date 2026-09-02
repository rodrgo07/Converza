import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models import FollowUp, Task, Notification, FollowUpStatus, TaskStatus
from app.core.events import manager

logger = logging.getLogger(__name__)

def process_due_followups_and_tasks(db: Session):
    """
    Motor de automação que processa follow-ups e tarefas vencidas ou próximas do vencimento,
    gerando notificações no sistema para os atendentes e disparando eventos em tempo real.
    """
    now = datetime.now(timezone.utc)
    
    # 1. Processar Follow-ups pendentes com due_date <= now
    expired_followups = db.query(FollowUp).filter(
        FollowUp.status == FollowUpStatus.PENDING,
        FollowUp.due_date <= now
    ).all()

    processed_followups = 0
    for fu in expired_followups:
        # Criar notificação para o atendente responsável se ainda não foi notificado
        existing_notif = db.query(Notification).filter(
            Notification.company_id == fu.company_id,
            Notification.user_id == fu.assigned_user_id,
            Notification.title.like(f"%Follow-up pendente: {fu.title}%")
        ).first()

        if not existing_notif and fu.assigned_user_id:
            notif = Notification(
                company_id=fu.company_id,
                user_id=fu.assigned_user_id,
                title=f"⚠️ Follow-up pendente: {fu.title}",
                message=f"O follow-up agendado com o cliente precisa de atenção imediata.",
                link=f"/inbox?customer_id={fu.customer_id}" if fu.customer_id else "/followups",
                is_read=False
            )
            db.add(notif)
            processed_followups += 1

    # 2. Processar Tarefas pendentes com due_date <= now
    expired_tasks = db.query(Task).filter(
        Task.status == TaskStatus.PENDING,
        Task.due_date <= now
    ).all()

    processed_tasks = 0
    for t in expired_tasks:
        existing_notif = db.query(Notification).filter(
            Notification.company_id == t.company_id,
            Notification.user_id == t.assigned_user_id,
            Notification.title.like(f"%Tarefa atrasada: {t.title}%")
        ).first()

        if not existing_notif and t.assigned_user_id:
            notif = Notification(
                company_id=t.company_id,
                user_id=t.assigned_user_id,
                title=f"⏰ Tarefa atrasada: {t.title}",
                message=f"A tarefa está com prazo expirado e aguarda conclusão.",
                link=f"/tasks",
                is_read=False
            )
            db.add(notif)
            processed_tasks += 1

    db.commit()
    return {
        "processed_followups": processed_followups,
        "processed_tasks": processed_tasks
    }
