from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, Base
from app.models import *

# Create tables
Base.metadata.create_all(bind=engine)

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def root():
    return {
        "app": "Converza API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }
