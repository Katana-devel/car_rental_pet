from fastapi import FastAPI, APIRouter
from fastapi.security import HTTPBearer
from fastapi_mail import FastMail

from src.services.messages.email import send_password_reset

test_email = APIRouter(prefix='/test_email', tags=['test_email'])
get_refresh_token = HTTPBearer()

@test_email.get("/test-reset-email")
async def test_reset_email():
    await send_password_reset(
        user_id="f3edab0b-bfe2-42ee-bdf2-7196e265e945",  # тестовый UUID
        email="test@example.com",  # сюда Mailtrap пропустит любое значение
        host="http://localhost:8000"
    )
    return {"status": "email sent to Mailtrap"}


