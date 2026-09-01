from typing import Optional, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

class WhatsAppProvider:
    def __init__(self, phone_number_id: Optional[str] = None, access_token: Optional[str] = None):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = f'https://graph.facebook.com/v19.0/{phone_number_id}' if phone_number_id else None

    async def send_text_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        if not self.phone_number_id or not self.access_token:
            return {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': to_phone, 'wa_id': to_phone.replace('+', '')}],
                'messages': [{'id': f'wamid.HBgL{to_phone[-4:]}DEMO'}],
                'status': 'simulated_success'
            }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to_phone,
            'type': 'text',
            'text': {'preview_url': False, 'body': text}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f'{self.base_url}/messages', json=payload, headers=headers)
            return resp.json()

    async def send_media_message(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        if not self.phone_number_id or not self.access_token:
            return {'status': 'simulated_success', 'media_url': media_url}

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to_phone,
            'type': media_type,
            media_type: {'link': media_url, 'caption': caption or ''}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f'{self.base_url}/messages', json=payload, headers=headers)
            return resp.json()
