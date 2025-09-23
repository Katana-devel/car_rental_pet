from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr, SecretStr

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
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
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


