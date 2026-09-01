from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, Base
from app.models import *

from app.api.endpoints import (
    auth, customers, conversations, pipeline, followups, tasks, extra_routers, webhooks
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Converza - CRM de WhatsApp para Pequenos Negócios Brasileiros",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://converza.com.br", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# API Routers
api_v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=f"{api_v1}/auth", tags=["Auth"])
app.include_router(customers.router, prefix=f"{api_v1}/customers", tags=["Customers"])
app.include_router(conversations.router, prefix=f"{api_v1}/conversations", tags=["Conversations"])
app.include_router(pipeline.router, prefix=f"{api_v1}/pipeline", tags=["Pipeline & Opportunities"])
app.include_router(followups.router, prefix=f"{api_v1}/followups", tags=["Follow-ups"])
app.include_router(tasks.router, prefix=f"{api_v1}/tasks", tags=["Tasks"])
app.include_router(extra_routers.tags_router, prefix=f"{api_v1}/tags", tags=["Tags"])
app.include_router(extra_routers.qr_router, prefix=f"{api_v1}/quick-replies", tags=["Quick Replies"])
app.include_router(extra_routers.wa_router, prefix=f"{api_v1}/whatsapp", tags=["WhatsApp"])
app.include_router(extra_routers.notif_router, prefix=f"{api_v1}/notifications", tags=["Notifications"])
app.include_router(extra_routers.sub_router, prefix=f"{api_v1}/subscription", tags=["Subscription"])
app.include_router(extra_routers.team_router, prefix=f"{api_v1}/team", tags=["Team"])
app.include_router(extra_routers.company_router, prefix=f"{api_v1}/company", tags=["Company"])
app.include_router(extra_routers.dashboard_router, prefix=f"{api_v1}/dashboard", tags=["Dashboard"])
app.include_router(extra_routers.reports_router, prefix=f"{api_v1}/reports", tags=["Reports"])
app.include_router(webhooks.router, prefix=f"{api_v1}/webhooks", tags=["WhatsApp Webhook"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["WhatsApp Webhook Root"])

# Realtime WebSocket & SSE Endpoints
from fastapi import WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from app.core.events import manager
from jose import jwt
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import User
import json
import asyncio

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket em tempo real com autenticação JWT e isolamento multi-tenant por empresa (company_id).
    Permite que múltiplos atendentes recebam novas mensagens e eventos instantaneamente.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=1008) # Policy Violation
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            await websocket.close(code=1008)
            return
        company_id = user.company_id
    finally:
        db.close()

    await manager.connect(websocket, company_id)
    try:
        while True:
            # Manter conexão viva recebendo pings/mensagens de presença do atendente
            data = await websocket.receive_text()
            try:
                msg_data = json.loads(data)
                if msg_data.get("type") == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id)
    except Exception:
        manager.disconnect(websocket, company_id)

@app.get("/api/v1/realtime/events")
async def sse_events(token: str = Query(...)):
    """
    Server-Sent Events (SSE) fallback para atualizações em tempo real.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        return {"error": "Invalid token"}

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        company_id = user.company_id
    finally:
        db.close()

    queue = manager.subscribe_sse(company_id)

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            manager.unsubscribe_sse(company_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
def root():
    return {
        "app": "Converza API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    db_status = "connected"
    try:
        from sqlalchemy import text
        from app.db.session import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }

