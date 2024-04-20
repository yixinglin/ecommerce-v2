import os
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.FROM_EMAIL,
    MAIL_FROM_NAME=settings.FROM_MAIL_NAME,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_SSL_TLS=settings.SMTP_SSL_TLS,
    MAIL_STARTTLS=False,
    TEMPLATE_FOLDER=os.path.join("assets", "templates", 'email'),
)

async def send_email_async(email_to: str, subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype='html'
    )
    fm = FastMail(conf)
    await fm.send_message(message, "hello.html")


def send_email_background(email_to: str, subject: str, body: str, background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        template_body={
            "name": "John Doe"
        },
        subtype='html'
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message, "hello.html")