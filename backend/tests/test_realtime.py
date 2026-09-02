import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_password_hash
from app.core.events import manager
from app.models import User, Company, UserRole
from tests.conftest import TestingSessionLocal

client = TestClient(app)

def get_auth_token_for_user(email: str) -> str:
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        c = db.query(Company).first()
        if not c:
            c = Company(name="Empresa Teste Realtime")
            db.add(c)
            db.commit()
            db.refresh(c)
        user = User(
            company_id=c.id,
            name="Usuario Realtime",
            email=email,
            hashed_password=get_password_hash("pass123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return create_access_token(subject=str(user.id))

def test_websocket_connection_and_ping_pong():
    token = get_auth_token_for_user("admin_rt@alfa.com")
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text(json.dumps({"type": "PING"}))
        data = websocket.receive_text()
        parsed = json.loads(data)
        assert parsed["type"] == "PONG"

def test_websocket_rejects_invalid_token():
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=invalid_token_xyz"):
            pass

def test_sse_endpoint_invalid_token():
    res_invalid = client.get("/api/v1/realtime/events?token=invalid_token_123")
    assert res_invalid.status_code == 401

@pytest.mark.asyncio
async def test_connection_manager_broadcast_isolation():
    q_alfa = manager.subscribe_sse(company_id=1)
    q_beta = manager.subscribe_sse(company_id=2)

    try:
        # Broadcast para empresa 1 (Alfa)
        await manager.broadcast_to_company(1, "TEST_EVENT", {"message": "Hello Alfa"})
        
        # Verificar que Alfa recebeu
        assert not q_alfa.empty()
        item_alfa = q_alfa.get_nowait()
        assert item_alfa["type"] == "TEST_EVENT"
        assert item_alfa["data"]["message"] == "Hello Alfa"

        # Verificar que Beta NÃO recebeu
        assert q_beta.empty()
    finally:
        manager.unsubscribe_sse(1, q_alfa)
        manager.unsubscribe_sse(2, q_beta)
