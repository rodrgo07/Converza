import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models import FollowUp, Task, Notification, Customer, User, Company, FollowUpStatus, TaskStatus, UserRole
from app.services.automations import process_due_followups_and_tasks
from tests.conftest import TestingSessionLocal
from app.core.security import create_access_token, get_password_hash

client = TestClient(app)

def ensure_test_fixtures():
    db = TestingSessionLocal()
    c = db.query(Company).first()
    if not c:
        c = Company(name="Empresa Automação Teste")
        db.add(c)
        db.commit()
        db.refresh(c)

    user = db.query(User).filter(User.company_id == c.id).first()
    if not user:
        user = User(
            company_id=c.id,
            name="Atendente Automação",
            email="auto@teste.com",
            hashed_password=get_password_hash("pass123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    cust = db.query(Customer).filter(Customer.company_id == c.id).first()
    if not cust:
        cust = Customer(
            company_id=c.id,
            name="Cliente Alvo Automação",
            phone="5511999990000",
            total_spent=500.0,
            orders_count=2
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)

    c_id = c.id
    u_id = user.id
    cust_id = cust.id
    db.close()
    return c_id, u_id, cust_id

def test_automations_process_due_followups_and_tasks():
    c_id, u_id, cust_id = ensure_test_fixtures()
    db = TestingSessionLocal()

    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=2)

    # 1. Criar Follow-up vencido
    fu = FollowUp(
        company_id=c_id,
        customer_id=cust_id,
        assigned_user_id=u_id,
        title="Cobrança Proposta Comercial",
        notes="Acompanhar fechamento",
        due_date=past,
        status=FollowUpStatus.PENDING
    )
    db.add(fu)

    # 2. Criar Tarefa vencida
    t = Task(
        company_id=c_id,
        customer_id=cust_id,
        assigned_user_id=u_id,
        title="Enviar Catálogo em PDF",
        description="Cliente solicitou catálogo de novos produtos",
        due_date=past,
        status=TaskStatus.PENDING
    )
    db.add(t)
    db.commit()

    # 3. Executar o processador de automação
    result = process_due_followups_and_tasks(db)
    assert result["processed_followups"] >= 1
    assert result["processed_tasks"] >= 1

    # 4. Verificar se notificações foram geradas no banco
    notifs = db.query(Notification).filter(
        Notification.company_id == c_id,
        Notification.user_id == u_id
    ).all()
    
    titles = [n.title for n in notifs]
    assert any("Cobrança Proposta Comercial" in title for title in titles)
    assert any("Enviar Catálogo em PDF" in title for title in titles)

    # 5. Executar novamente -> Idempotência: não deve duplicar notificações
    result_second = process_due_followups_and_tasks(db)
    assert result_second["processed_followups"] == 0
    assert result_second["processed_tasks"] == 0
    db.close()

def test_reports_process_automations_endpoint():
    c_id, u_id, _ = ensure_test_fixtures()
    token = create_access_token(subject=str(u_id))

    res = client.post("/api/v1/reports/process-automations", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "result" in res.json()
