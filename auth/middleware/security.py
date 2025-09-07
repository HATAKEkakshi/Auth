from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import re
from collections import defaultdict
from auth.logger.log import logger
import html

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for input validation, rate limiting, and security headers"""
    
    def __init__(self, app, rate_limit_requests: int = 100, rate_limit_window: int = 3600):
        super().__init__(app)
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.request_counts = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Rate limiting
        if self._is_rate_limited(client_ip):
            logger("Auth", "Security", "WARN", "HIGH", f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Input validation for suspicious patterns
        if await self._has_malicious_input(request):
            logger("Auth", "Security", "WARN", "HIGH", f"Malicious input detected from IP: {client_ip}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid input detected"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address safely"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited"""
        now = time.time()
        
        # Clean old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if now - req_time < self.rate_limit_window
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.rate_limit_requests:
            return True
        
        # Add current request
        self.request_counts[client_ip].append(now)
        return False
    
    async def _has_malicious_input(self, request: Request) -> bool:
        """Check for malicious input patterns"""
        try:
            # Check URL for suspicious patterns
            if self._contains_malicious_patterns(str(request.url)):
                return True
            
            # Check headers
            for header_value in request.headers.values():
                if self._contains_malicious_patterns(header_value):
                    return True
            
            # Check query parameters
            for param_value in request.query_params.values():
                if self._contains_malicious_patterns(param_value):
                    return True
            
            return False
        except Exception:
            return False
    
    def _contains_malicious_patterns(self, input_str: str) -> bool:
        """Check for common attack patterns"""
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',  # XSS
            r'on\w+\s*=',  # Event handlers
            r'union\s+select',  # SQL injection
            r'drop\s+table',  # SQL injection
            r'\.\./.*\.\.',  # Path traversal
            r'exec\s*\(',  # Code injection
            r'eval\s*\(',  # Code injection
            r'system\s*\(',  # Command injection
            r'[;&|`$]',  # Command injection
        ]
        
        input_lower = input_str.lower()
        for pattern in malicious_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                return True
        return False
    
    def _add_security_headers(self, response: Response):
        """Add comprehensive security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not isinstance(input_str, str):
        return input_str
    
    # HTML escape
    sanitized = html.escape(input_str)
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\&]', '', sanitized)
    
    return sanitized.strip()

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) and len(email) <= 254

def validate_password_strength(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    # Check for at least one uppercase, lowercase, digit, and special character
    patterns = [
        r'[A-Z]',  # Uppercase
        r'[a-z]',  # Lowercase
        r'\d',     # Digit
        r'[!@#$%^&*(),.?":{}|<>]'  # Special character
    ]
    
    return all(re.search(pattern, password) for pattern in patterns)