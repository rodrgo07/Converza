import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models import (
    Company, User, Subscription, PipelineStage, PipelineStageType,
    Tag, WhatsAppAccount, UserRole
)
from app.core.security import get_password_hash

def init_dev_admin():
    db = SessionLocal()
    existing_user = db.query(User).filter(User.email == 'admin@converza.com.br').first()
    if existing_user:
        print("Admin user already initialized in PostgreSQL.")
        db.close()
        return

    print("Initializing clean dev admin and default stages in PostgreSQL...")

    # 1. Company
    company = Company(
        name="Minha Empresa",
        segment="Comércio & Serviços",
        team_size="1 a 3 pessoas",
        whatsapp_usage="Vendas e Atendimento",
        phone=""
    )
    db.add(company)
    db.flush()

    # 2. Subscription
    sub = Subscription(
        company_id=company.id,
        plan="free",
        status="active",
        max_users=1,
        max_customers=100,
        price_cents=0
    )
    db.add(sub)

    # 3. Pipeline Stages
    stages_data = [
        ("Novo contato", PipelineStageType.NEW, 0, "#3B82F6"),
        ("Interessado", PipelineStageType.INTERESTED, 1, "#10B981"),
        ("Orçamento", PipelineStageType.QUOTE, 2, "#F59E0B"),
        ("Negociação", PipelineStageType.NEGOTIATION, 3, "#8B5CF6"),
        ("Venda", PipelineStageType.SALE, 4, "#10B981"),
        ("Pós-venda", PipelineStageType.POST_SALE, 5, "#06B6D4"),
        ("Perdido", PipelineStageType.LOST, 6, "#EF4444"),
    ]
    for name, stype, order, color in stages_data:
        stage = PipelineStage(
            company_id=company.id,
            name=name,
            stage_type=stype,
            order=order,
            color=color
        )
        db.add(stage)

    # 4. WhatsApp Account (unconnected status)
    wa = WhatsAppAccount(
        company_id=company.id,
        is_connected=False,
        status="disconnected",
        webhook_verify_token=f"converza_verify_{company.id}"
    )
    db.add(wa)

    # 5. Clean Admin User
    admin = User(
        company_id=company.id,
        name="Administrador",
        email="admin@converza.com.br",
        phone="",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        onboarding_completed=True,
        theme_preference="system"
    )
    db.add(admin)
    db.commit()
    print("Dev admin initialized in PostgreSQL: admin@converza.com.br / admin123")
    db.close()

if __name__ == "__main__":
    init_dev_admin()