from aiohttp import ClientSession
from fastapi import HTTPException, status

from src.core.config.config import google_oid_config


class GoogleOAuthService:
    def __init__(self):
        self.token_url = google_oid_config.GOOGLE_TOKEN_URL
        self.client_id = google_oid_config.CLIENT_ID
        self.client_secret = google_oid_config.CLIENT_SECRET
        self.redirect_uri = google_oid_config.GOOGLE_REDIRECT_URL

    async def exchange_code_for_token(self, code: str):
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with ClientSession() as session:
            async with session.post(self.token_url, data=data, headers=headers, ssl=False) as response:
                text = await response.text()
                try:
                    tokens = await response.json()
                except Exception:
                    tokens = None

                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Google token endpoint error: {tokens or text}"
                    )
                return tokens

google_auth = GoogleOAuthService()