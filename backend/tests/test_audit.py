import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db
from app.core.security import get_password_hash
from app.models import Company, User, Subscription, Customer, PipelineStage, Opportunity, Conversation, Message, WhatsAppAccount, UserRole, MessageDirection, MessageType, MessageStatus

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audit.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Company 1
    c1 = Company(name="Empresa Alfa", phone="+55 11 91111-1111")
    db.add(c1)
    db.flush()
    sub1 = Subscription(company_id=c1.id, plan="free", max_users=1, max_customers=2, price_cents=0)
    db.add(sub1)
    u1_admin = User(company_id=c1.id, name="Admin Alfa", email="admin@alfa.com", hashed_password=get_password_hash("pass123"), role=UserRole.ADMIN)
    db.add(u1_admin)
    st1 = PipelineStage(company_id=c1.id, name="Novo Contato", order=0)
    db.add(st1)
    cust1 = Customer(company_id=c1.id, name="Cliente Alfa 1", phone="+5511999990001", total_spent=500.0, orders_count=1)
    db.add(cust1)
    db.flush()
    conv1 = Conversation(company_id=c1.id, customer_id=cust1.id, status="open")
    db.add(conv1)
    wa1 = WhatsAppAccount(company_id=c1.id, phone_number_id="PHONE_ID_1", access_token="TOKEN_1", is_connected=True, webhook_verify_token="converza_token_alfa")
    db.add(wa1)

    # Company 2
    c2 = Company(name="Empresa Beta", phone="+55 11 92222-2222")
    db.add(c2)
    db.flush()
    sub2 = Subscription(company_id=c2.id, plan="essential", max_users=3, max_customers=1000, price_cents=3990)
    db.add(sub2)
    u2_admin = User(company_id=c2.id, name="Admin Beta", email="admin@beta.com", hashed_password=get_password_hash("pass123"), role=UserRole.ADMIN)
    db.add(u2_admin)
    cust2 = Customer(company_id=c2.id, name="Cliente Beta Secreto", phone="+5511999990002")
    db.add(cust2)

    db.commit()
    db.close()

def get_auth_token(email, password="pass123"):
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]

# 1. AUTH TESTS
def test_auth_login_valid_and_invalid():
    resp = client.post("/api/v1/auth/login", data={"username": "admin@alfa.com", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    resp_invalid = client.post("/api/v1/auth/login", data={"username": "admin@alfa.com", "password": "wrongpassword"})
    assert resp_invalid.status_code == 400

    resp_me = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert resp_me.status_code == 401

# 2. MULTI-TENANT ISOLATION TESTS
def test_multi_tenant_isolation_customers():
    token_alfa = get_auth_token("admin@alfa.com")
    token_beta = get_auth_token("admin@beta.com")

    # Alfa list should only contain Alfa customers
    resp_alfa = client.get("/api/v1/customers/", headers={"Authorization": f"Bearer {token_alfa}"})
    assert resp_alfa.status_code == 200
    names = [c["name"] for c in resp_alfa.json()]
    assert "Cliente Alfa 1" in names
    assert "Cliente Beta Secreto" not in names

    # Alfa trying to access Beta customer directly -> MUST Return 404 (Not accessible)
    resp_cross = client.get("/api/v1/customers/2", headers={"Authorization": f"Bearer {token_alfa}"})
    assert resp_cross.status_code == 404

    # Alfa trying to delete Beta customer -> MUST Return 404
    resp_cross_del = client.delete("/api/v1/customers/2", headers={"Authorization": f"Bearer {token_alfa}"})
    assert resp_cross_del.status_code == 404

# 3. PLAN LIMITS TESTS (BACKEND ENFORCEMENT)
def test_plan_limits_customers_and_users():
    token_alfa = get_auth_token("admin@alfa.com")

    # Alfa limit is 2 customers (currently has 1)
    # Add 2nd customer (Allowed)
    r1 = client.post("/api/v1/customers/", json={"name": "Cliente Alfa 2", "phone": "+5511999990003"}, headers={"Authorization": f"Bearer {token_alfa}"})
    assert r1.status_code == 200

    # Add 3rd customer (Exceeds limit -> 403 Forbidden)
    r2 = client.post("/api/v1/customers/", json={"name": "Cliente Alfa 3 Excedente", "phone": "+5511999990004"}, headers={"Authorization": f"Bearer {token_alfa}"})
    assert r2.status_code == 403
    assert "Limite do plano atingido" in r2.json()["detail"]

    # Alfa limit is 1 user (already has Admin)
    # Trying to add 2nd user -> 403 Forbidden
    r_user = client.post("/api/v1/team/", json={"name": "Vendedor Extra", "email": "extra@alfa.com", "password": "123"}, headers={"Authorization": f"Bearer {token_alfa}"})
    assert r_user.status_code == 403
    assert "Limite do plano atingido" in r_user.json()["detail"]

# 4. WHATSAPP WEBHOOK VERIFICATION TEST
def test_whatsapp_webhook_verification():
    # Correct verify token
    resp = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=converza_verify_token_2026&hub.challenge=CHALLENGE_ACCEPTED_123")
    assert resp.status_code == 200
    assert resp.text == "CHALLENGE_ACCEPTED_123"

    # Company specific token
    resp_co = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=converza_token_alfa&hub.challenge=COMPANY_CHALLENGE_789")
    assert resp_co.status_code == 200
    assert resp_co.text == "COMPANY_CHALLENGE_789"

    # Invalid token
    resp_invalid = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=FAIL")
    assert resp_invalid.status_code == 403

# 5. WHATSAPP WEBHOOK INBOUND & IDEMPOTENCY TEST
def test_whatsapp_webhook_inbound_message_and_idempotency():
    inbound_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "+5511911111111",
                        "phone_number_id": "PHONE_ID_1"
                    },
                    "contacts": [{
                        "profile": {"name": "Fernanda Nova Compradora"},
                        "wa_id": "5511988880099"
                    }],
                    "messages": [{
                        "from": "5511988880099",
                        "id": "wamid.TEST_UNIQUE_ID_9999",
                        "timestamp": "1725140000",
                        "text": {"body": "Olá! Gostaria de saber os preços do catálogo."},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    # 1st time received -> Customer created, Conversation created, Message saved
    r1 = client.post("/api/v1/webhooks/whatsapp", json=inbound_payload)
    assert r1.status_code == 200

    token_alfa = get_auth_token("admin@alfa.com")
    convs = client.get("/api/v1/conversations/", headers={"Authorization": f"Bearer {token_alfa}"}).json()
    matched = [c for c in convs if c["customer"]["name"] == "Fernanda Nova Compradora"]
    assert len(matched) == 1
    assert matched[0]["last_message_text"] == "Olá! Gostaria de saber os preços do catálogo."

    # 2nd time received (Duplicate Webhook delivery) -> MUST NOT duplicate message (Idempotency)
    r2 = client.post("/api/v1/webhooks/whatsapp", json=inbound_payload)
    assert r2.status_code == 200

    conv_detail = client.get(f"/api/v1/conversations/{matched[0]['id']}", headers={"Authorization": f"Bearer {token_alfa}"}).json()
    assert len(conv_detail["messages"]) == 1

# 6. WHATSAPP STATUS UPDATE VIA WEBHOOK TEST
def test_whatsapp_webhook_status_update():
    status_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "PHONE_ID_1"},
                    "statuses": [{
                        "id": "wamid.TEST_UNIQUE_ID_9999",
                        "status": "read",
                        "timestamp": "1725140100",
                        "recipient_id": "5511988880099"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    r = client.post("/api/v1/webhooks/whatsapp", json=status_payload)
    assert r.status_code == 200

    token_alfa = get_auth_token("admin@alfa.com")
    convs = client.get("/api/v1/conversations/", headers={"Authorization": f"Bearer {token_alfa}"}).json()
    matched = [c for c in convs if c["customer"]["name"] == "Fernanda Nova Compradora"]
    conv_detail = client.get(f"/api/v1/conversations/{matched[0]['id']}", headers={"Authorization": f"Bearer {token_alfa}"}).json()
    assert conv_detail["messages"][0]["status"] == "read"
