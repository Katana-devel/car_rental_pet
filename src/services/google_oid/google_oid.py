import urllib.parse
from src.core.config.config import google_oid_config


async def generate_user_url():
    query_params = {
        "client_id": google_oid_config.CLIENT_ID,
        "redirect_uri": google_oid_config.GOOGLE_REDIRECT_URL,
        "response_type": "code",
        "scope": "openid profile email",
        "access_type": "offline",
        "prompt": "consent"
    }

    query_string = urllib.parse.urlencode(query_params)
    google_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    return f"{google_base_url}?{query_string}"