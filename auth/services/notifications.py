from jinja2 import Environment, FileSystemLoader, select_autoescape
import html
import re
from auth.security.template_validator import SecureTemplateValidator
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from auth.config.notification import notification_settings
from auth.helper.utils import TEMPLATE_DIR
from auth.config.worker import celery_app
from twilio.rest import Client
from auth.logger.log import logger
import asyncio

class NotificationService:
    """Service for handling email and SMS notifications via Celery tasks"""
    
    def __init__(self):
        try:
            self.fastmail = FastMail(
                ConnectionConfig(
                    **notification_settings.model_dump(
                        exclude=["TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_NUMBER"]
                    ),
                    TEMPLATE_FOLDER=TEMPLATE_DIR,
                )
            )
            self.twilio_client = Client(
                notification_settings.TWILIO_SID,
                notification_settings.TWILIO_AUTH_TOKEN,
            )
            logger("Auth", "Notification", "INFO", "null", "NotificationService initialized successfully")
        except Exception as e:
            logger("Auth", "Notification", "ERROR", "ERROR", f"NotificationService initialization failed: {str(e)}")
            raise

    """Internal method to send plain email asynchronously"""
    async def _send_plain_email(self, message: MessageSchema):
        try:
            await self.fastmail.send_message(message)
            logger("Auth", "Notification", "INFO", "null", "Plain email sent successfully")
        except Exception as e:
            logger("Auth", "Notification", "ERROR", "ERROR", f"Plain email sending failed: {str(e)}")
            raise

    """Synchronous wrapper for plain email sending - REMOVED for security"""
    # Removed unsafe asyncio.run to prevent command injection

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

    """Internal method to send HTML template email asynchronously"""
    async def _send_html_email(self, message: MessageSchema, template_name: str):
        try:
            await self.fastmail.send_message(message=message, template_name=template_name)
            logger("Auth", "Notification", "INFO", "null", f"HTML template email sent successfully: {template_name}")
        except Exception as e:
            logger("Auth", "Notification", "ERROR", "ERROR", f"HTML template email sending failed for {template_name}: {str(e)}")
            raise

    """Synchronous wrapper for HTML template email sending - REMOVED for security"""
    # Removed unsafe asyncio.run to prevent command injection
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




# Celery tasks defined outside the class
@celery_app.task(name="notifications.send_plain_email")
def send_plain_email_task(email: str, subject: str, body: str):
    """Celery task for sending plain text emails"""
    try:
        logger("Auth", "Notification", "INFO", "null", f"Starting plain email task for: {email}")
        
        fastmail = FastMail(
            ConnectionConfig(
                **notification_settings.model_dump(
                    exclude=["TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_NUMBER"]
                ),
                TEMPLATE_FOLDER=TEMPLATE_DIR,
            )
        )
        
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=body,
            subtype=MessageType.plain,
        )
        
        # Use proper async context instead of asyncio.run
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(fastmail.send_message(message))
        finally:
            loop.close()
        logger("Auth", "Notification", "INFO", "null", f"Plain email sent successfully to: {email}")
    except Exception as e:
        logger("Auth", "Notification", "ERROR", "ERROR", f"Failed to send plain email to {email}: {str(e)}")
        raise




@celery_app.task(name="notifications.send_email_template")
def send_email_template_task(email: str, subject: str, context: dict, template_name: str):
    """Celery task for sending HTML template emails"""
    try:
        logger("Auth", "Notification", "INFO", "null", f"Starting template email task for: {email}, template: {template_name}")
        
        fastmail = FastMail(
            ConnectionConfig(
                **notification_settings.model_dump(
                    exclude=["TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_NUMBER"]
                ),
                TEMPLATE_FOLDER=TEMPLATE_DIR,
            )
        )
        
        # Use secure template validator
        validator = SecureTemplateValidator(TEMPLATE_DIR)
        
        if not validator.validate_template_name(template_name):
            logger("Auth", "Notification", "ERROR", "HIGH", f"Invalid template name: {template_name}")
            raise ValueError(f"Template not allowed: {template_name}")
        
        # Sanitize context data using validator
        sanitized_context = validator.sanitize_template_context(context)
        
        logger("Auth", "Notification", "INFO", "null", f"Template validated and context sanitized: {template_name}")

        message = MessageSchema(
            subject=subject,
            recipients=[email],
            template_body=sanitized_context,
            subtype=MessageType.html,
        )
        
        # Use proper async context instead of asyncio.run
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(fastmail.send_message(message=message, template_name=template_name))
        finally:
            loop.close()
        logger("Auth", "Notification", "INFO", "null", f"Template email sent successfully to: {email}, template: {template_name}")
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
