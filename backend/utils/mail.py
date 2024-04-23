import json
import os
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from core.config import settings
from pydantic import BaseModel

TEMPLATE_FOLDER: str = os.path.join("assets", "templates", 'email')


class SMTPConnectionConfigModel(BaseModel):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_SSL_TLS: bool
    MAIL_STARTTLS: bool
    TEMPLATE_FOLDER: str = TEMPLATE_FOLDER

    @classmethod
    def from_json(cls, name: str = "default"):
        with open(os.path.join("conf", "emails", "smtp.json"), encoding="utf-8") as fp:
            c = json.load(fp)
            connection_config = cls(**c[name])
        return connection_config

    def to_connection_config(self) -> ConnectionConfig:
        return ConnectionConfig(**self.__dict__)


CONF_SYSTEM_NOTIFIER = SMTPConnectionConfigModel.from_json("notifier").to_connection_config()


async def send_email_async(email_to: str, subject: str,
                           body: str, template_body: dict = None,
                           template_file: str = None):
    """
    Send email asynchronously.
    :param email_to: Email address of the recipient.
    :param subject:  Subject of the email.
    :param body: Body of the email.
    :param template_body: Dict of data to be used in the email template.
    :param template_file: Name of the template file to be used in the email.
    :return:
    """
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        template_body=template_body,
        subtype='html'
    )
    fm = FastMail(CONF_SYSTEM_NOTIFIER)
    await fm.send_message(message, template_file)


def send_email_background(email_to: str, subject: str, body: str,
                          background_tasks: BackgroundTasks,
                          template_body: dict = None,
                          template_file: str = None):
    """
    Send email in background task.

    :param email_to: Email address of the recipient.
    :param subject: Subject of the email.
    :param body: Body of the email.
    :param background_tasks: BackgroundTasks instance from FastAPI.
    :param template_body: Dict of data to be used in the email template.
    :param template_file: Name of the template file to be used in the email.
    """
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        template_body=template_body,
        subtype='html'
    )
    fm = FastMail(CONF_SYSTEM_NOTIFIER)
    background_tasks.add_task(fm.send_message, message, template_file)
