import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_password_hash
from app.models import Company, User, Subscription, Customer, Conversation, Message, WhatsAppAccount, UserRole, MessageDirection, MessageType
from tests.conftest import TestingSessionLocal

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_security_data():
    db = TestingSessionLocal()

    # Company 1
    c1 = Company(name="Empresa Segura A", phone="+55 11 91111-1111")
    db.add(c1)
    db.flush()
    sub1 = Subscription(company_id=c1.id, plan="essential", max_users=3, max_customers=100)
    db.add(sub1)
    u1 = User(company_id=c1.id, name="Admin Seguro", email="admin@seguro.com", hashed_password=get_password_hash("pass123"), role=UserRole.ADMIN)
    db.add(u1)
    cust1 = Customer(company_id=c1.id, name="Joao Silva", phone="+5511999998888", email="joao.silva@email.com", notes="Interessado em tenis")
    db.add(cust1)
    db.flush()
    conv1 = Conversation(company_id=c1.id, customer_id=cust1.id)
    db.add(conv1)
    db.flush()
    msg1 = Message(conversation_id=conv1.id, content="Olá, quero comprar o tênis tamanho 41", direction=MessageDirection.INBOUND, message_type=MessageType.TEXT)
    db.add(msg1)
    wa1 = WhatsAppAccount(company_id=c1.id, phone_number_id="PH_123", access_token="SECRET_TOKEN_META_999", is_connected=True)
    db.add(wa1)

    # Company 2
    c2 = Company(name="Empresa Externa B", phone="+55 11 92222-2222")
    db.add(c2)
    db.flush()
    u2 = User(company_id=c2.id, name="Hacker Externo", email="hacker@externo.com", hashed_password=get_password_hash("pass123"), role=UserRole.ADMIN)
    db.add(u2)

    db.commit()
    db.close()

def get_auth_token(email, password="pass123"):
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]

# 1. TEST WHATSAPP ACCESS TOKEN PROTECTION
def test_whatsapp_access_token_is_never_returned_in_api():
    token = get_auth_token("admin@seguro.com")
    resp = client.get("/api/v1/whatsapp/status", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" not in data
    assert data["has_token_configured"] is True

# 2. TEST LGPD DATA PORTABILITY / EXPORT
def test_lgpd_customer_data_export():
    token = get_auth_token("admin@seguro.com")
    cust_resp = client.get("/api/v1/customers/", headers={"Authorization": f"Bearer {token}"})
    cust_id = [c["id"] for c in cust_resp.json() if c["name"] == "Joao Silva"][0]

    resp = client.get(f"/api/v1/customers/{cust_id}/export", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer"]["name"] == "Joao Silva"
    assert data["customer"]["email"] == "joao.silva@email.com"
    assert len(data["conversations"]) == 1
    assert data["conversations"][0]["messages"][0]["content"] == "Olá, quero comprar o tênis tamanho 41"

    # IDOR Protection: External company attempting to export customer -> 404
    token_ext = get_auth_token("hacker@externo.com")
    resp_ext = client.get(f"/api/v1/customers/{cust_id}/export", headers={"Authorization": f"Bearer {token_ext}"})
    assert resp_ext.status_code == 404

# 3. TEST LGPD ANONYMIZATION / ELIMINATION
def test_lgpd_customer_data_anonymization():
    token = get_auth_token("admin@seguro.com")
    cust_resp = client.get("/api/v1/customers/", headers={"Authorization": f"Bearer {token}"})
    cust_id = [c["id"] for c in cust_resp.json() if c["name"] == "Joao Silva"][0]

    resp = client.post(f"/api/v1/customers/{cust_id}/anonymize", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Verify PII was redacted
    cust_updated = client.get(f"/api/v1/customers/{cust_id}", headers={"Authorization": f"Bearer {token}"}).json()
    assert "Cliente Anonimizado" in cust_updated["name"]
    assert cust_updated["email"] is None
    assert "ANONIMIZADOS" in cust_updated["notes"]

    conv_id = cust_updated["id"]
    convs = client.get("/api/v1/conversations/", headers={"Authorization": f"Bearer {token}"}).json()
    matched_conv = [c for c in convs if c["customer_id"] == cust_id][0]
    conv_detail = client.get(f"/api/v1/conversations/{matched_conv['id']}", headers={"Authorization": f"Bearer {token}"}).json()
    assert conv_detail["messages"][0]["content"] == "[MENSAGEM ANONIMIZADA - LGPD]"

# 4. TEST SECURITY HEADERS
def test_security_headers_present():
    resp = client.get("/")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in resp.headers
