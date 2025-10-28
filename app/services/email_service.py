from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template engine
env = Environment(
    loader=FileSystemLoader("app/templates/email"),
    autoescape=select_autoescape(["html", "xml"])
)

# Email config
conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAIL_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_STARTTLS=settings.SMTP_STARTTLS,
    MAIL_SSL_TLS=settings.SMTP_SSL,
    MAIL_FROM_NAME=settings.EMAIL_FROM_NAME,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

async def send_email(subject: str, recipients: list[str], template_name: str, context: dict):
    """
    Send an HTML email using a Jinja2 template.
    """
    try:
        template = env.get_template(template_name)
        html_content = template.render(**context)

        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html_content,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"📧 Email sent to {recipients} with subject: '{subject}'")

    except Exception as e:
        print(f"❌ Email send failed: {e}")
        raise



async def send_verification_email(to_email: str, username: str, token: str):
    await send_email(
        subject="Verify your InkBoard account",
        recipients=[to_email],
        template_name="verify_email.html",
        context={
            "username": username,
            "verify_url": f"http://localhost:8000/v1/auth/verify?token={token}"
        }
    )


async def send_password_reset_email(to_email: str, username: str, token: str):
    await send_email(
        subject="Reset your InkBoard password",
        recipients=[to_email],
        template_name="reset_password.html",
        context={
            "username": username,
            "reset_url": f"http://localhost:8000/v1/auth/reset-password?token={token}"
        }
    )
