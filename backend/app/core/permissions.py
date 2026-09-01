from fastapi import HTTPException, status
from app.models import User, UserRole

# Permissões por perfil (Role-Based Access Control)
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        'whatsapp.view', 'whatsapp.send', 'whatsapp.manage', 'whatsapp.assign', 'whatsapp.transfer', 'whatsapp.disconnect',
        'team.manage', 'company.manage', 'subscription.manage'
    },
    UserRole.MANAGER: {
        'whatsapp.view', 'whatsapp.send', 'whatsapp.assign', 'whatsapp.transfer',
        'team.view', 'company.view'
    },
    UserRole.SALES: {
        'whatsapp.view', 'whatsapp.send', 'whatsapp.assign', 'whatsapp.transfer'
    },
    UserRole.SUPPORT: {
        'whatsapp.view', 'whatsapp.send', 'whatsapp.assign', 'whatsapp.transfer'
    }
}

def has_permission(user: User, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(user.role, set())
    return permission in perms

def check_permission(user: User, permission: str):
    if not has_permission(user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Acesso negado: permissão necessária {permission}'
        )
