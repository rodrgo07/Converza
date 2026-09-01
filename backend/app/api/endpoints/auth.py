from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models import User, Company, Subscription, Tag, PipelineStage, PipelineStageType, UserRole
from app.schemas import Token, UserCreate, UserOut, OnboardingSetup
from app.api.deps import get_current_user, get_current_company

router = APIRouter()

DEFAULT_STAGES = [
    ('Novo contato', PipelineStageType.NEW, 0, '#3B82F6'),
    ('Interessado', PipelineStageType.INTERESTED, 1, '#10B981'),
    ('Orçamento enviado', PipelineStageType.QUOTE, 2, '#F59E0B'),
    ('Em negociação', PipelineStageType.NEGOTIATION, 3, '#8B5CF6'),
    ('Venda fechada', PipelineStageType.SALE, 4, '#10B981'),
    ('Pós-venda', PipelineStageType.POST_SALE, 5, '#06B6D4'),
    ('Perdido', PipelineStageType.LOST, 6, '#EF4444'),
]

DEFAULT_TAGS = [
    ('Novo cliente', '#3B82F6'),
    ('VIP', '#F59E0B'),
    ('Interessado', '#10B981'),
    ('Aguardando resposta', '#EC4899'),
    ('Orçamento pendente', '#8B5CF6'),
]

@router.post('/register', response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check existing email
    user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail='Este e-mail já está cadastrado no sistema.'
        )

    # Create Company
    company_name = user_in.company_name or f'Empresa de {user_in.name}'
    company = Company(
        name=company_name,
        phone=user_in.phone
    )
    db.add(company)
    db.flush()

    # Create default Subscription
    subscription = Subscription(
        company_id=company.id,
        plan='free',
        status='active',
        max_users=1,
        max_customers=100,
        price_cents=0
    )
    db.add(subscription)

    # Create default pipeline stages
    for name, stype, order, color in DEFAULT_STAGES:
        stage = PipelineStage(
            company_id=company.id,
            name=name,
            stage_type=stype,
            order=order,
            color=color
        )
        db.add(stage)

    # Create default tags
    for name, color in DEFAULT_TAGS:
        tag = Tag(company_id=company.id, name=name, color=color)
        db.add(tag)

    # Create user (Admin)
    new_user = User(
        company_id=company.id,
        name=user_in.name,
        email=user_in.email.lower(),
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.password),
        role=UserRole.ADMIN,
        onboarding_completed=False,
        theme_preference='system'
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(subject=new_user.id)
    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user': UserOut.model_validate(new_user)
    }

@router.post('/login', response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='E-mail ou senha incorretos.'
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Usuário inativo. Contate o administrador.'
        )

    access_token = create_access_token(subject=user.id)
    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user': UserOut.model_validate(user)
    }

@router.get('/me', response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.post('/onboarding', response_model=UserOut)
def complete_onboarding(
    data: OnboardingSetup,
    current_user: User = Depends(get_current_user),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    company.segment = data.segment
    company.team_size = data.team_size
    company.whatsapp_usage = data.whatsapp_usage
    current_user.onboarding_completed = True
    db.commit()
    db.refresh(current_user)
    return current_user
