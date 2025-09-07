import os
from pathlib import Path
from typing import Set
import html
import re

class SecureTemplateValidator:
    """Secure template validation to prevent path traversal and code injection"""
    
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir).resolve()
        self.allowed_templates: Set[str] = {
            'registration.html',
            'mail_email_verify.html', 
            'mail_password_reset.html',
            'email_verified.html',
            'email_verified_failed.html',
            'reset.html',
            'reset_success.html',
            'reset_failed.html'
        }
    
    def validate_template_name(self, template_name: str) -> bool:
        """Validate template name against whitelist"""
        if not isinstance(template_name, str):
            return False
        
        # Check against whitelist
        if template_name not in self.allowed_templates:
            return False
        
        # Additional security checks
        if '..' in template_name or '/' in template_name or '\\' in template_name:
            return False
        
        return True
    
    def sanitize_template_context(self, context: dict) -> dict:
        """Sanitize template context to prevent XSS"""
        sanitized = {}
        
        for key, value in context.items():
            # Sanitize key
            safe_key = re.sub(r'[^a-zA-Z0-9_]', '', str(key))
            
            # Sanitize value
            if isinstance(value, str):
                safe_value = html.escape(value)
                # Remove potentially dangerous patterns
                safe_value = re.sub(r'javascript:', '', safe_value, flags=re.IGNORECASE)
                safe_value = re.sub(r'on\w+\s*=', '', safe_value, flags=re.IGNORECASE)
                sanitized[safe_key] = safe_value
            elif isinstance(value, (int, float, bool)):
                sanitized[safe_key] = value
            else:
                # Convert to string and sanitize
                sanitized[safe_key] = html.escape(str(value))
        
        return sanitized
    
    def get_safe_template_path(self, template_name: str) -> Path:
        """Get safe template path with validation"""
        if not self.validate_template_name(template_name):
            raise ValueError(f"Invalid template name: {template_name}")
        
        template_path = self.template_dir / template_name
        
        # Ensure path is within template directory
        if not str(template_path.resolve()).startswith(str(self.template_dir)):
            raise ValueError(f"Path traversal attempt: {template_name}")
        
        return template_path