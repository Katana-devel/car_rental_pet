from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr, SecretStr
from sqlalchemy import UUID

from src.core.config.config import email_config
from src.services.auth import auth_service
from src.core.logger.logger import logger

conf = ConnectionConfig(
    MAIL_USERNAME=email_config.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(email_config.MAIL_PASSWORD),
    MAIL_FROM=email_config.MAIL_FROM,
    MAIL_PORT=email_config.MAIL_PORT,
    MAIL_SERVER=email_config.MAIL_SERVER,
    MAIL_FROM_NAME=email_config.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_confirmation_email(email: EmailStr, host: str):
    try:
        token_verification = await auth_service.create_email_token({"sub": email})

        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={"host": host, "user_name": email, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_confirmation.html")
        print("Confirmation message were successfully sent")
    except ConnectionErrors as err:
        logger.error(err)


async def send_password_reset(user_id: UUID, email: EmailStr, host: str):
    try:
        token_verification = await auth_service.create_password_reset_token({"sub": str(user_id)})

        message = MessageSchema(
            subject="Reset Your Password",
            recipients=[email],
            template_body={"host": host, "user_id": user_id," email": email, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="password_reset.html")
        print("Password reset message were successfully sent")
    except ConnectionErrors as err:
        logger.error(err)
