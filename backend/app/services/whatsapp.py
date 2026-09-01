from typing import Optional, Dict, Any, List
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

META_ERROR_MAPPINGS = {
    190: ("TOKEN_INVALID", "Token de acesso do WhatsApp expirado ou inválido. Reconecte a conta."),
    100: ("INVALID_PARAMETER", "Parâmetro inválido enviado para a API da Meta."),
    130429: ("RATE_LIMIT", "Limite de taxa de envio de mensagens do WhatsApp atingido. Aguarde alguns instantes."),
    131030: ("RECIPIENT_NOT_ALLOWED", "Número de destino não permitido ou em lista de restrições."),
    131047: ("MESSAGE_WINDOW_EXPIRED", "Janela de 24 horas expirada. Utilize um template oficial aprovado para retomar contato."),
    131051: ("PHONE_NOT_REGISTERED", "Número de telefone não está registrado no WhatsApp Business Platform."),
    132000: ("TEMPLATE_NOT_APPROVED", "Template de mensagem não encontrado ou não aprovado pela Meta."),
    133010: ("PHONE_NUMBER_NOT_VERIFIED", "O número da empresa ainda não passou pela verificação da Meta."),
}

def parse_meta_error(status_code: int, error_obj: Dict[str, Any]) -> tuple[str, str]:
    err = error_obj.get("error", {})
    code = err.get("code")
    subcode = err.get("error_subcode")
    msg = err.get("message", "Erro desconhecido na Meta Cloud API")
    if code in META_ERROR_MAPPINGS:
        return META_ERROR_MAPPINGS[code]
    if subcode in META_ERROR_MAPPINGS:
        return META_ERROR_MAPPINGS[subcode]
    if status_code == 401:
        return ("TOKEN_INVALID", "Token de acesso do WhatsApp inválido ou sem permissão.")
    if status_code == 404:
        return ("PHONE_NOT_REGISTERED", "Phone Number ID não encontrado na plataforma Meta.")
    return ("META_API_ERROR", msg)

class WhatsAppProvider:
    def __init__(self, phone_number_id: Optional[str] = None, access_token: Optional[str] = None, api_version: Optional[str] = None):
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.api_version = api_version or settings.WHATSAPP_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}" if self.phone_number_id else None

    @property
    def is_configured(self) -> bool:
        return bool(self.phone_number_id and self.access_token)

    async def verify_credentials(self) -> Dict[str, Any]:
        """
        Realiza teste real de conectividade com a Meta Graph API.
        """
        if not self.phone_number_id or not self.access_token:
            raise ValueError("WHATSAPP_NOT_CONFIGURED: Phone Number ID e Access Token são obrigatórios no backend.")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}?fields=id,verified_name,display_phone_number,quality_rating,code_verification_status",
                    headers=headers
                )
                data = resp.json()
                if resp.status_code >= 400:
                    err_code, err_msg = parse_meta_error(resp.status_code, data)
                    raise ValueError(f"[{err_code}] {err_msg}")
                return data
            except httpx.RequestError as exc:
                raise ValueError(f"[API_UNAVAILABLE] Não foi possível conectar aos servidores da Meta: {str(exc)}")

    async def send_text_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto real via Meta WhatsApp Cloud API.
        """
        if not self.is_configured:
            raise ValueError("WHATSAPP_NOT_CONNECTED: WhatsApp Cloud API não está configurada no backend.")

        clean_phone = "".join([c for c in to_phone if c.isdigit()])
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {"preview_url": False, "body": text}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/messages", json=payload, headers=headers)
                data = resp.json()
                if resp.status_code >= 400:
                    err_code, err_msg = parse_meta_error(resp.status_code, data)
                    logger.error(f"WhatsApp Cloud API Error: {resp.status_code} - {err_code}: {err_msg}")
                    raise RuntimeError(f"[{err_code}] {err_msg}")
                return data
            except httpx.RequestError as exc:
                logger.error(f"HTTP request error sending WhatsApp message: {exc}")
                raise RuntimeError(f"[API_UNAVAILABLE] Falha de conexão com a Meta Cloud API: {str(exc)}")

    async def send_media_message(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Envia mensagem de mídia real via Meta WhatsApp Cloud API.
        """
        if not self.is_configured:
            raise ValueError("WHATSAPP_NOT_CONNECTED: WhatsApp Cloud API não está configurada no backend.")

        clean_phone = "".join([c for c in to_phone if c.isdigit()])
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": media_type,
            media_type: {"link": media_url, "caption": caption or ""}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/messages", json=payload, headers=headers)
                data = resp.json()
                if resp.status_code >= 400:
                    err_code, err_msg = parse_meta_error(resp.status_code, data)
                    logger.error(f"WhatsApp Cloud API Media Error: {resp.status_code} - {err_code}: {err_msg}")
                    raise RuntimeError(f"[{err_code}] {err_msg}")
                return data
            except httpx.RequestError as exc:
                logger.error(f"HTTP request error sending WhatsApp media: {exc}")
                raise RuntimeError(f"[API_UNAVAILABLE] Falha de conexão com a Meta Cloud API: {str(exc)}")

    async def send_template_message(self, to_phone: str, template_name: str, language_code: str = "pt_BR", components: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Envia mensagem de template oficial do WhatsApp.
        """
        if not self.is_configured:
            raise ValueError("WHATSAPP_NOT_CONNECTED: WhatsApp Cloud API não está configurada no backend.")

        clean_phone = "".join([c for c in to_phone if c.isdigit()])
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or []
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/messages", json=payload, headers=headers)
                data = resp.json()
                if resp.status_code >= 400:
                    err_code, err_msg = parse_meta_error(resp.status_code, data)
                    raise RuntimeError(f"[{err_code}] {err_msg}")
                return data
            except httpx.RequestError as exc:
                raise RuntimeError(f"[API_UNAVAILABLE] Falha de conexão com a Meta Cloud API: {str(exc)}")

