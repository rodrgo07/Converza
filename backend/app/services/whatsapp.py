from typing import Optional, Dict, Any
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhatsAppProvider:
    def __init__(self, phone_number_id: Optional[str] = None, access_token: Optional[str] = None):
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.api_version = settings.WHATSAPP_API_VERSION
        self.base_url = f'https://graph.facebook.com/{self.api_version}/{self.phone_number_id}' if self.phone_number_id else None

    @property
    def is_configured(self) -> bool:
        return bool(self.phone_number_id and self.access_token)

    async def send_text_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        """
        Sends an outbound text message via Meta WhatsApp Cloud API.
        If credentials are not configured, raises an explicit informative error.
        """
        if not self.is_configured:
            raise ValueError("WHATSAPP_NOT_CONNECTED: WhatsApp Cloud API não está configurada com Access Token e Phone Number ID.")

        clean_phone = to_phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': clean_phone,
            'type': 'text',
            'text': {'preview_url': False, 'body': text}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(f'{self.base_url}/messages', json=payload, headers=headers)
                data = resp.json()
                if resp.status_code >= 400:
                    error_msg = data.get("error", {}).get("message", "Erro desconhecido na Meta Cloud API")
                    logger.error(f"WhatsApp Cloud API Error: {resp.status_code} - {error_msg}")
                    raise RuntimeError(f"Meta API Error: {error_msg}")
                return data
            except httpx.RequestError as exc:
                logger.error(f"HTTP request error sending WhatsApp message: {exc}")
                raise RuntimeError(f"Falha de conexão com a Meta Cloud API: {str(exc)}")

    async def send_media_message(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends an outbound media message via Meta WhatsApp Cloud API.
        """
        if not self.is_configured:
            raise ValueError("WHATSAPP_NOT_CONNECTED: WhatsApp Cloud API não está configurada com Access Token e Phone Number ID.")

        clean_phone = to_phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': clean_phone,
            'type': media_type,
            media_type: {'link': media_url, 'caption': caption or ''}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(f'{self.base_url}/messages', json=payload, headers=headers)
                data = resp.json()
                if resp.status_code >= 400:
                    error_msg = data.get("error", {}).get("message", "Erro desconhecido na Meta Cloud API")
                    logger.error(f"WhatsApp Cloud API Error: {resp.status_code} - {error_msg}")
                    raise RuntimeError(f"Meta API Error: {error_msg}")
                return data
            except httpx.RequestError as exc:
                logger.error(f"HTTP request error sending WhatsApp media: {exc}")
                raise RuntimeError(f"Falha de conexão com a Meta Cloud API: {str(exc)}")
