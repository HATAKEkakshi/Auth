from jinja2 import Environment, FileSystemLoader
import re
from auth.security.template_validator import SecureTemplateValidator
from auth.config.notification import notification_settings
from auth.helper.utils import TEMPLATE_DIR
from auth.config.worker import celery_app
from twilio.rest import Client
from auth.logger.log import logger
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationService:
    """Service for handling email and SMS notifications via Celery tasks"""
    
    def __init__(self):
        try:
            self.twilio_client = Client(
                notification_settings.TWILIO_SID,
                notification_settings.TWILIO_AUTH_TOKEN,
            )
            logger("Auth", "Notification", "INFO", "null", "NotificationService initialized successfully")
        except Exception as e:
            logger("Auth", "Notification", "ERROR", "ERROR", f"NotificationService initialization failed: {str(e)}")
            raise

    """Send plain text email via Celery task"""
    def send_message(self, email: str, subject: str, body: str):
        try:
            if not email:
                logger("Auth", "Notification", "WARN", "LOW", "Plain email not sent - no email address provided")
                return
            
            # Queue Celery task for plain email
            send_plain_email_task.delay(email, subject, body)
            logger("Auth", "Notification", "INFO", "null", f"Plain email task queued for: {email}")
        except Exception as e:
            logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to queue plain email task for {email}: {str(e)}")
            raise

    """Send HTML template email via Celery task"""
    def send_email_template(self, email: str, subject: str, context: dict, template_name: str):
        try:
            if not email:
                logger("Auth", "Notification", "WARN", "LOW", f"Template email not sent - no email address provided for template: {template_name}")
                return
            
            # Queue Celery task for template email
            send_email_template_task.delay(email, subject, context, template_name)
            logger("Auth", "Notification", "INFO", "null", f"Template email task queued for: {email}, template: {template_name}")
        except Exception as e:
            logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to queue template email task for {email}, template {template_name}: {str(e)}")
            raise

    """Send SMS via Celery task"""
    def send_sms(self, to: str, body: str):
        try:
            if not to:
                logger("Auth", "Notification", "WARN", "LOW", "SMS not sent - no phone number provided")
                return
            
            # Queue Celery task for SMS
            send_sms_task.delay(to, body)
            logger("Auth", "Notification", "INFO", "null", f"SMS task queued for: {to}")
        except Exception as e:
            logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to queue SMS task for {to}: {str(e)}")
            raise


async def _send_email_async(to_email: str, subject: str, body: str, is_html: bool = False):
    """Internal async function to send email via aiosmtplib"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{notification_settings.MAIL_FROM_NAME} <{notification_settings.MAIL_FROM}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
        
        await aiosmtplib.send(
            msg,
            hostname=notification_settings.MAIL_SERVER,
            port=notification_settings.MAIL_PORT,
            start_tls=notification_settings.MAIL_STARTTLS,
            use_tls=notification_settings.MAIL_SSL_TLS,
            username=notification_settings.MAIL_USERNAME,
            password=notification_settings.MAIL_PASSWORD,
        )
        logger("Auth", "Notification", "INFO", "null", f"Email sent successfully to: {to_email}")
    except Exception as e:
        logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to send email to {to_email}: {str(e)}")
        raise


# Celery tasks defined outside the class
@celery_app.task(name="notifications.send_plain_email")
def send_plain_email_task(email: str, subject: str, body: str):
    """Celery task for sending plain text emails"""
    try:
        logger("Auth", "Notification", "INFO", "null", f"Starting plain email task for: {email}")
        
        # Run async function in sync Celery task
        asyncio.run(_send_email_async(email, subject, body, is_html=False))
        
        logger("Auth", "Notification", "INFO", "null", f"Plain email task completed for: {email}")
    except Exception as e:
        logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to send plain email to {email}: {str(e)}")
        raise


@celery_app.task(name="notifications.send_email_template")
def send_email_template_task(email: str, subject: str, context: dict, template_name: str):
    """Celery task for sending HTML template emails"""
    try:
        logger("Auth", "Notification", "INFO", "null", f"Starting template email task for: {email}, template: {template_name}")
        
        # Use secure template validator
        validator = SecureTemplateValidator(TEMPLATE_DIR)
        
        if not validator.validate_template_name(template_name):
            logger("Auth", "Notification", "ERROR", "HIGH", f"Invalid template name: {template_name}")
            raise ValueError(f"Template not allowed: {template_name}")
        
        # Sanitize context data using validator
        sanitized_context = validator.sanitize_template_context(context)
        
        # Render template
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template(template_name)
        rendered_html = template.render(sanitized_context)
        
        logger("Auth", "Notification", "INFO", "null", f"Template rendered: {template_name}")

        # Run async function in sync Celery task
        asyncio.run(_send_email_async(email, subject, rendered_html, is_html=True))
        
        logger("Auth", "Notification", "INFO", "null", f"Template email task completed for: {email}")
    except Exception as e:
        logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to send template email to {email}, template {template_name}: {str(e)}")
        raise


def _validate_phone_number(phone: str) -> bool:
    """Validate phone number format to prevent injection"""
    # Only allow digits, +, -, (, ), and spaces
    pattern = r'^[+]?[0-9\s\-\(\)]+$'
    return bool(re.match(pattern, phone)) and len(phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 10

def _sanitize_sms_body(body: str) -> str:
    """Sanitize SMS body to prevent injection"""
    # Remove any potential command injection characters
    sanitized = re.sub(r'[;&|`$(){}\[\]<>]', '', body)
    return sanitized[:160]  # SMS length limit

@celery_app.task(name="notifications.send_sms")
def send_sms_task(to: str, body: str):
    """Celery task for sending SMS via Twilio with security validation"""
    try:
        # Validate phone number
        if not _validate_phone_number(to):
            logger("Auth", "Notification", "ERROR", "HIGH", f"Invalid phone number format: {to}")
            raise ValueError("Invalid phone number format")
        
        # Sanitize SMS body
        sanitized_body = _sanitize_sms_body(body)
        
        logger("Auth", "Notification", "INFO", "null", f"Starting SMS task for validated number")
        
        twilio_client = Client(
            notification_settings.TWILIO_SID,
            notification_settings.TWILIO_AUTH_TOKEN,
        )
        
        message = twilio_client.messages.create(
            body=sanitized_body,
            from_=notification_settings.TWILIO_NUMBER,
            to=to
        )
        
        logger("Auth", "Notification", "INFO", "null", f"SMS sent successfully, SID: {message.sid}")
    except Exception as e:
        logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to send SMS: {str(e)}")
        raise
