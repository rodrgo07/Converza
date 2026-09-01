import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_password_hash
from app.models import Company, User, Subscription, Customer, PipelineStage, Conversation, WhatsAppAccount, UserRole
from tests.conftest import TestingSessionLocal

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_audit_data():
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

    resp_alfa = client.get("/api/v1/customers/", headers={"Authorization": f"Bearer {token_alfa}"})
    assert resp_alfa.status_code == 200
    names = [c["name"] for c in resp_alfa.json()]
    assert "Cliente Alfa 1" in names
    assert "Cliente Beta Secreto" not in names

    # Finding ID of Beta Customer
    resp_beta = client.get("/api/v1/customers/", headers={"Authorization": f"Bearer {token_beta}"})
    beta_cust_id = [c["id"] for c in resp_beta.json() if c["name"] == "Cliente Beta Secreto"][0]

    # Alfa trying to access Beta customer -> MUST Return 404
    resp_cross = client.get(f"/api/v1/customers/{beta_cust_id}", headers={"Authorization": f"Bearer {token_alfa}"})
    assert resp_cross.status_code == 404

    # Alfa trying to delete Beta customer -> MUST Return 404
    resp_cross_del = client.delete(f"/api/v1/customers/{beta_cust_id}", headers={"Authorization": f"Bearer {token_alfa}"})
    assert resp_cross_del.status_code == 404

# 3. PLAN LIMITS TESTS (BACKEND ENFORCEMENT)
def test_plan_limits_customers_and_users():
    token_alfa = get_auth_token("admin@alfa.com")

    # Add 2nd customer (Allowed)
    r1 = client.post("/api/v1/customers/", json={"name": "Cliente Alfa 2", "phone": "+5511999990003"}, headers={"Authorization": f"Bearer {token_alfa}"})
    assert r1.status_code == 200

    # Add 3rd customer (Exceeds limit -> 403 Forbidden)
    r2 = client.post("/api/v1/customers/", json={"name": "Cliente Alfa 3 Excedente", "phone": "+5511999990004"}, headers={"Authorization": f"Bearer {token_alfa}"})
    assert r2.status_code == 403
    assert "Limite do plano atingido" in r2.json()["detail"]

    # Add 2nd user on free plan (Exceeds limit -> 403 Forbidden)
    r_user = client.post("/api/v1/team/", json={"name": "Vendedor Extra", "email": "extra@alfa.com", "password": "123"}, headers={"Authorization": f"Bearer {token_alfa}"})
    assert r_user.status_code == 403
    assert "Limite do plano atingido" in r_user.json()["detail"]

# 4. WHATSAPP WEBHOOK VERIFICATION TEST
def test_whatsapp_webhook_verification():
    resp = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=converza_verify_token_2026&hub.challenge=CHALLENGE_ACCEPTED_123")
    assert resp.status_code == 200
    assert resp.text == "CHALLENGE_ACCEPTED_123"

    resp_co = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=converza_token_alfa&hub.challenge=COMPANY_CHALLENGE_789")
    assert resp_co.status_code == 200
    assert resp_co.text == "COMPANY_CHALLENGE_789"

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

    r1 = client.post("/api/v1/webhooks/whatsapp", json=inbound_payload)
    assert r1.status_code == 200

    token_alfa = get_auth_token("admin@alfa.com")
    convs = client.get("/api/v1/conversations/", headers={"Authorization": f"Bearer {token_alfa}"}).json()
    matched = [c for c in convs if c["customer"]["name"] == "Fernanda Nova Compradora"]
    assert len(matched) == 1
    assert matched[0]["last_message_text"] == "Olá! Gostaria de saber os preços do catálogo."

    # Duplicate Webhook delivery -> MUST NOT duplicate
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

# 7. MULTI-ATTENDANT TESTS: ASSIGNMENT, TRANSFER, OPTIMISTIC LOCKING
def test_multi_attendant_assignment_and_transfer():
    db = TestingSessionLocal()
    c2 = db.query(Company).filter(Company.name == "Empresa Beta").first()
    
    # Criar 2 atendentes adicionais na Empresa Beta
    u_maria = User(company_id=c2.id, name="Maria Atendente", email="maria@beta.com", hashed_password=get_password_hash("pass123"), role=UserRole.SALES)
    u_carlos = User(company_id=c2.id, name="Carlos Atendente", email="carlos@beta.com", hashed_password=get_password_hash("pass123"), role=UserRole.SUPPORT)
    db.add(u_maria)
    db.add(u_carlos)

    cust2 = db.query(Customer).filter(Customer.company_id == c2.id).first()
    conv2 = Conversation(company_id=c2.id, customer_id=cust2.id, status="open", queue="unassigned")
    db.add(conv2)
    db.commit()
    maria_id = u_maria.id
    carlos_id = u_carlos.id
    conv_id = conv2.id
    db.close()

    token_admin = get_auth_token("admin@beta.com")
    token_maria = get_auth_token("maria@beta.com")
    token_carlos = get_auth_token("carlos@beta.com")

    # Obter conversa de Beta
    target_conv = client.get(f"/api/v1/conversations/{conv_id}", headers={"Authorization": f"Bearer {token_maria}"}).json()

    # 1. Maria assume o atendimento
    r_assign = client.post(
        f"/api/v1/conversations/{conv_id}/assign",
        json={"assigned_user_id": maria_id, "expected_version": target_conv["version"]},
        headers={"Authorization": f"Bearer {token_maria}"}
    )
    assert r_assign.status_code == 200
    assigned_data = r_assign.json()
    assert assigned_data["assigned_user_id"] == maria_id
    assert len(assigned_data["events"]) >= 1
    assert "Maria Atendente" in assigned_data["events"][-1]["description"]

    # 2. Carlos visualiza a mesma conversa e vê que Maria é a responsável
    r_carlos_view = client.get(f"/api/v1/conversations/{conv_id}", headers={"Authorization": f"Bearer {token_carlos}"})
    assert r_carlos_view.status_code == 200
    assert r_carlos_view.json()["assigned_user"]["name"] == "Maria Atendente"

    # 3. Concorrência / Optimistic locking: tentar alterar com versão defasada
    r_conflict = client.post(
        f"/api/v1/conversations/{conv_id}/assign",
        json={"assigned_user_id": carlos_id, "expected_version": target_conv["version"]}, # Versão antiga
        headers={"Authorization": f"Bearer {token_carlos}"}
    )
    assert r_conflict.status_code == 409

    # 4. Maria transfere para Carlos com nota
    new_version = assigned_data["version"]
    r_transfer = client.post(
        f"/api/v1/conversations/{conv_id}/transfer",
        json={"target_user_id": carlos_id, "notes": "Cliente precisa de suporte técnico", "expected_version": new_version},
        headers={"Authorization": f"Bearer {token_maria}"}
    )
    assert r_transfer.status_code == 200
    transf_data = r_transfer.json()
    assert transf_data["assigned_user_id"] == carlos_id
    assert "transferida por Maria Atendente para Carlos Atendente" in transf_data["events"][-1]["description"]
    assert "suporte técnico" in transf_data["events"][-1]["description"]

# 8. TEST RBAC PERMISSIONS ENFORCEMENT
def test_rbac_permissions():
    token_sales = get_auth_token("maria@beta.com")
    
    # Atendente de vendas tentando desconectar WhatsApp -> 403 Proibido
    resp = client.post("/api/v1/whatsapp/disconnect", headers={"Authorization": f"Bearer {token_sales}"})
    assert resp.status_code == 403
    assert "whatsapp.disconnect" in resp.json()["detail"]

# 9. TEST TEST-CONNECTION REAL GRAPH API ENDPOINT
def test_whatsapp_test_connection_endpoint():
    token_admin = get_auth_token("admin@alfa.com")
    resp = client.post("/api/v1/whatsapp/test-connection", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data
    assert "status" in data

