from pybloom_live import BloomFilter
from auth.logger.log import logger
import pickle
import os
from pathlib import Path

"""Bloom filter configuration for Auth system security enhancements"""

class BloomFilterService:
    """Service for managing Bloom filters for security and performance"""
    
    def __init__(self):
        try:
            self.bloom_dir = Path(__file__).parent.parent / "data" / "bloom"
            self.bloom_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize bloom filters
            self.blacklisted_tokens = self._load_or_create_filter("blacklisted_tokens", 100000, 0.001)
            self.compromised_passwords = self._load_or_create_filter("compromised_passwords", 1000000, 0.001)
            self.suspicious_ips = self._load_or_create_filter("suspicious_ips", 50000, 0.001)
            self.registered_emails = self._load_or_create_filter("registered_emails", 500000, 0.001)
            
            logger("Auth", "Bloom Filter", "INFO", "null", "BloomFilterService initialized successfully")
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"BloomFilterService initialization failed: {str(e)}")
            raise
    
    def _load_or_create_filter(self, name: str, capacity: int, error_rate: float) -> BloomFilter:
        """Load existing bloom filter or create new one"""
        try:
            filter_path = self.bloom_dir / f"{name}.bloom"
            
            if filter_path.exists():
                with open(filter_path, 'rb') as f:
                    bloom_filter = pickle.load(f)
                logger("Auth", "Bloom Filter", "INFO", "null", f"Loaded existing bloom filter: {name}")
                return bloom_filter
            else:
                bloom_filter = BloomFilter(capacity=capacity, error_rate=error_rate)
                self._save_filter(name, bloom_filter)
                logger("Auth", "Bloom Filter", "INFO", "null", f"Created new bloom filter: {name}")
                return bloom_filter
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Failed to load/create bloom filter {name}: {str(e)}")
            raise
    
    def _save_filter(self, name: str, bloom_filter: BloomFilter):
        """Save bloom filter to disk"""
        try:
            filter_path = self.bloom_dir / f"{name}.bloom"
            with open(filter_path, 'wb') as f:
                pickle.dump(bloom_filter, f)
            logger("Auth", "Bloom Filter", "INFO", "null", f"Saved bloom filter: {name}")
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Failed to save bloom filter {name}: {str(e)}")
            raise


    """JWT Token Blacklisting Methods"""
    def is_token_blacklisted(self, jti: str) -> bool:
        """Fast check if JWT token might be blacklisted"""
        try:
            result = jti in self.blacklisted_tokens
            if result:
                logger("Auth", "Bloom Filter", "WARN", "MEDIUM", f"Token possibly blacklisted: {jti[:10]}...")
            return result
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Token blacklist check failed: {str(e)}")
            return False
    
    def add_blacklisted_token(self, jti: str):
        """Add JWT token to blacklist"""
        try:
            self.blacklisted_tokens.add(jti)
            self._save_filter("blacklisted_tokens", self.blacklisted_tokens)
            logger("Auth", "Bloom Filter", "INFO", "null", f"Token added to blacklist: {jti[:10]}...")
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Failed to blacklist token: {str(e)}")
            raise


    """Password Security Methods"""
    def is_password_compromised(self, password: str) -> bool:
        """Check if password is in breach database"""
        try:
            result = password in self.compromised_passwords
            if result:
                logger("Auth", "Bloom Filter", "WARN", "HIGH", "Compromised password detected")
            return result
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Password compromise check failed: {str(e)}")
            return False
    
    def add_compromised_password(self, password: str):
        """Add password to compromised list"""
        try:
            self.compromised_passwords.add(password)
            self._save_filter("compromised_passwords", self.compromised_passwords)
            logger("Auth", "Bloom Filter", "INFO", "null", "Compromised password added to filter")
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Failed to add compromised password: {str(e)}")
            raise


    """IP Security Methods"""
    def is_ip_suspicious(self, ip: str) -> bool:
        """Check if IP is marked as suspicious"""
        try:
            result = ip in self.suspicious_ips
            if result:
                logger("Auth", "Bloom Filter", "WARN", "HIGH", f"Suspicious IP detected: {ip}")
            return result
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"IP suspicion check failed: {str(e)}")
            return False
    
    def add_suspicious_ip(self, ip: str):
        """Mark IP as suspicious"""
        try:
            self.suspicious_ips.add(ip)
            self._save_filter("suspicious_ips", self.suspicious_ips)
            logger("Auth", "Bloom Filter", "INFO", "null", f"IP marked as suspicious: {ip}")
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Failed to mark IP as suspicious: {str(e)}")
            raise


    """Email Existence Methods"""
    def is_email_registered(self, email: str) -> bool:
        """Fast check if email might be already registered"""
        try:
            result = email.lower() in self.registered_emails
            if result:
                logger("Auth", "Bloom Filter", "WARN", "MEDIUM", f"Email possibly registered: {email}")
            return result
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Email registration check failed: {str(e)}")
            return False
    
    def add_registered_email(self, email: str):
        """Add email to registered emails filter"""
        try:
            self.registered_emails.add(email.lower())
            self._save_filter("registered_emails", self.registered_emails)
            logger("Auth", "Bloom Filter", "INFO", "null", f"Email added to registered filter: {email}")
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Failed to add registered email: {str(e)}")
            raise


    """Utility Methods"""
    def get_filter_stats(self) -> dict:
        """Get statistics about bloom filters"""
        try:
            stats = {
                "blacklisted_tokens": {
                    "capacity": self.blacklisted_tokens.capacity,
                    "count": self.blacklisted_tokens.count,
                    "error_rate": self.blacklisted_tokens.error_rate
                },
                "compromised_passwords": {
                    "capacity": self.compromised_passwords.capacity,
                    "count": self.compromised_passwords.count,
                    "error_rate": self.compromised_passwords.error_rate
                },
                "suspicious_ips": {
                    "capacity": self.suspicious_ips.capacity,
                    "count": self.suspicious_ips.count,
                    "error_rate": self.suspicious_ips.error_rate
                },
                "registered_emails": {
                    "capacity": self.registered_emails.capacity,
                    "count": self.registered_emails.count,
                    "error_rate": self.registered_emails.error_rate
                }
            }
            logger("Auth", "Bloom Filter", "INFO", "null", "Bloom filter stats retrieved")
            return stats
        except Exception as e:
            logger("Auth", "Bloom Filter", "ERROR", "ERROR", f"Failed to get filter stats: {str(e)}")
            return {}


# Global bloom filter service instance
bloom_service = BloomFilterService()