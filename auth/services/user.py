from random import randint
from fastapi import HTTPException, Request, status
from auth.config.notification import app_settings
from auth.services.notifications import NotificationService
from auth.config.redis import set_profile_data,get_profile_data,delete_profile_data
from auth.helper.utils import (
    generate_country, id_generator, password_hash,
    password_context, generate_access_token,
    generate_url_safe_token, decode_url_safe_token,generate_otp_token, decode_otp_token
)
from auth.logger.log import logger
from auth.config.bloom import bloom_service
import json


class UserService:
    """Base user service class providing common user operations"""
    
    def __init__(self, model):
        self.model = model
        self.notification_service = NotificationService()
        self.verification_salt = "email-verify"
        logger("Auth", "User Service", "INFO", "null", "UserService initialized")

    """Get user by ID with Redis caching"""
    async def _get(self, id: str, request: Request, collection_name, redis_key_prefix: str):
        try:
            cache_key = f"{redis_key_prefix}:id:{id}"
            cached = await get_profile_data(cache_key)
            if cached:
                logger("Auth", "User Service", "INFO", "null", f"User retrieved from cache: {id}")
                return json.loads(cached)

            user = await collection_name.find_one({"id": id})
            if not user:
                logger("Auth", "Database", "WARN", "MEDIUM", f"User not found in database: {id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {id} not found"
                )

            user.pop("_id", None)
            await set_profile_data(cache_key, 3600, json.dumps(user))
            logger("Auth", "Database", "INFO", "null", f"User retrieved from database and cached: {id}")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"Error getting user {id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")


    """Get user by email with Redis caching"""
    async def _get_by_email(self, email: str, request: Request, collection_name, redis_key_prefix: str):
        try:
            cache_key = f"{redis_key_prefix}:email:{email}"
            cached = await get_profile_data(cache_key)
            if cached:
                logger("Auth", "User Service", "INFO", "null", f"User retrieved from cache by email: {email}")
                return json.loads(cached)

            user = await collection_name.find_one({"email": email})
            if not user:
                logger("Auth", "Database", "WARN", "MEDIUM", f"User not found in database by email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email {email} not found"
                )

            user.pop("_id", None)
            await set_profile_data(cache_key, 3600, json.dumps(user))
            logger("Auth", "Database", "INFO", "null", f"User retrieved from database by email and cached: {email}")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"Error getting user by email {email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")



    """Create new user with email verification and caching"""
    async def _add(
        self,
        user_data,
        request: Request,
        collection_name,
        redis_key_prefix: str,
        router_prefix: str
    ):
        try:
            cache_key = f"{redis_key_prefix}:{user_data.email}"

            # Fast Bloom filter check first
            if bloom_service.is_email_registered(user_data.email):
                # Bloom filter says "maybe" - check cache and database for confirmation
                if await get_profile_data(cache_key) or await collection_name.find_one({"email": user_data.email}):
                    logger("Auth", "User Service", "WARN", "LOW", f"User registration attempt with existing email: {user_data.email}")
                    return {"message": "Email already exists", "Email": user_data.email}
            elif await collection_name.find_one({"email": user_data.email}):
                # Bloom filter said "no" but email exists - add to filter for future
                bloom_service.add_registered_email(user_data.email)
                logger("Auth", "User Service", "WARN", "LOW", f"User registration attempt with existing email: {user_data.email}")
                return {"message": "Email already exists", "Email": user_data.email}

            # Hash password and enrich data
            user_data.password = password_hash(user_data.password)
            user_dict = user_data.dict()
            user_id = id_generator()
            user_dict.update({
                "id": user_id,
                "country": generate_country(user_dict["country_code"]),
                "is_email_verified": False
            })

            # Insert user into database
            await collection_name.insert_one(user_dict)
            logger("Auth", "Database", "INFO", "null", f"New user created in database: {user_data.email}")
            
            # Add email to Bloom filter for future fast lookups
            bloom_service.add_registered_email(user_data.email)
            
            user_dict.pop("_id", None)
            key = f"{redis_key_prefix}:id:{user_id}"
            await set_profile_data(cache_key, 3600, json.dumps(user_dict))
            await set_profile_data(key, 3600, json.dumps(user_dict))

            # Generate verification token
            token = generate_url_safe_token(
                {"email": user_data.email, "id": user_id},
                salt=self.verification_salt
            )

            # Send registration and verification emails
            self.notification_service.send_email_template(
                email=user_data.email,
                subject="Registration Successful",
                context={"name": user_data.first_name},
                template_name="registration.html"
            )

            self.notification_service.send_email_template(
                email=user_data.email,
                subject="Verify your email",
                context={
                    "name": user_data.first_name,
                    "verification_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/verify?token={token}"
                },
                template_name="mail_email_verify.html"
            )

            logger("Auth", "User Service", "INFO", "null", f"User registration completed successfully: {user_data.email}")
            return {
                "message": "User created successfully",
                "Email": user_data.email,
                "id": user_id
            }
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"User registration failed for {user_data.email}: {str(e)}")
            raise HTTPException(status_code=500, detail="User registration failed")



    """Verify user email using token and update database"""
    async def verify_email(self, token: str, collection_name, request: Request, redis_key_prefix: str):
        try:
            token_data = decode_url_safe_token(token, salt=self.verification_salt)
            if not token_data:
                logger("Auth", "User Service", "WARN", "MEDIUM", "Invalid or expired email verification token")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired token"
                )

            user = await self._get(token_data["id"], request, collection_name, redis_key_prefix)
            user["is_email_verified"] = True

            # Update database
            await collection_name.update_one({"id": user["id"]}, {"$set": {"is_email_verified": True}})
            logger("Auth", "Database", "INFO", "null", f"Email verified for user: {user['email']}")

            # Update cache
            await delete_profile_data(f"{redis_key_prefix}:id:{user['id']}")
            await delete_profile_data(f"{redis_key_prefix}:{user['email']}")
            await set_profile_data(f"{redis_key_prefix}:{user['email']}", 3600, json.dumps(user))

            logger("Auth", "User Service", "INFO", "null", f"Email verification completed: {user['email']}")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"Email verification failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Email verification failed")



    """Delete user by CIN and clear cache"""
    async def _delete_user(self, CIN: str, email: str, request: Request, collection_name, redis_key_prefix: str):
        try:
            # Clear cache first
            await delete_profile_data(f"{redis_key_prefix}:CIN:{CIN}")
            await delete_profile_data(f"{redis_key_prefix}:{email}")

            user = await collection_name.find_one({"CIN": CIN})
            if not user:
                logger("Auth", "Database", "WARN", "MEDIUM", f"User not found for deletion: {CIN}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {CIN} not found"
                )

            await collection_name.delete_one({"CIN": CIN})
            logger("Auth", "Database", "INFO", "null", f"User deleted: {CIN}, {email}")
            return {"message": f"User with CIN {CIN} and email {email} deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"User deletion failed for {CIN}: {str(e)}")
            raise HTTPException(status_code=500, detail="User deletion failed")



    """Generate access token for user login"""
    async def _token(self, email: str, password: str, request: Request, collection_name, redis_key_prefix: str) -> str:
        try:
            user = await self._get_by_email(email, request, collection_name, redis_key_prefix)
            
            if not user or not password_context.verify(password, user["password"]):
                logger("Auth", "User Service", "WARN", "HIGH", f"Invalid login attempt: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
                
            if not user.get("is_email_verified", False):
                logger("Auth", "User Service", "WARN", "MEDIUM", f"Unverified email login attempt: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not verified"
                )

            token = generate_access_token({
                "id": user["id"],
                "email": user["email"]
            })
            logger("Auth", "User Service", "INFO", "null", f"Login successful: {email}")
            return token
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"Login failed for {email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Login failed")



    """Send password reset link via email"""
    async def _send_password_reset_link(self, email: str, router_prefix: str, collection_name):
        try:
            user = await collection_name.find_one({"email": email})
            if not user:
                logger("Auth", "Database", "WARN", "LOW", f"Password reset requested for non-existent user: {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            token = generate_url_safe_token(
                {"id": user["id"]},
                salt=self.verification_salt
            )

            self.notification_service.send_email_template(
                email=email,
                subject="Password Reset Request",
                context={
                    "name": user["first_name"],
                    "reset_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/reset_password_form?token={token}"
                },
                template_name="mail_password_reset.html"
            )

            logger("Auth", "User Service", "INFO", "null", f"Password reset link sent: {email}")
            return {"message": "Password reset link sent to your email"}
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"Password reset link failed for {email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send password reset link")



    """Reset user password using token"""
    async def reset_password(self, token: str, password: str, collection_name, request: Request, redis_key_prefix: str):
        try:
            token_data = decode_url_safe_token(token, salt=self.verification_salt)
            if not token_data:
                logger("Auth", "User Service", "WARN", "MEDIUM", "Invalid or expired password reset token")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired token"
                )

            user = await collection_name.find_one({"id": token_data["id"]})
            if not user:
                logger("Auth", "Database", "WARN", "MEDIUM", f"User not found for password reset: {token_data['id']}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Update password in database
            user["password"] = password_hash(password)
            await collection_name.update_one({"id": user["id"]}, {"$set": {"password": user["password"]}})
            logger("Auth", "Database", "INFO", "null", f"Password reset completed for user: {user['email']}")
            
            # Clear cache
            await delete_profile_data(f"{redis_key_prefix}:id:{user['id']}")
            await delete_profile_data(f"{redis_key_prefix}:{user['email']}")

            logger("Auth", "User Service", "INFO", "null", f"Password reset successful: {user['email']}")
            return {"message": "Password reset successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"Password reset failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Password reset failed")


    """Generate and send OTP for phone verification"""
    async def generate_otp(self, id: str, phone: str, request: Request, collection_name, redis_key_prefix: str):
        try:
            user = await self._get(id, request, collection_name, redis_key_prefix)
            if not user:
                logger("Auth", "User Service", "WARN", "MEDIUM", f"OTP generation attempted for non-existent user: {id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            otp = randint(100_000, 999_999)
            token = generate_otp_token({"otp": otp})
            
            self.notification_service.send_sms(
                to=phone,
                body=f"Your OTP is {otp}. It is valid for 5 minutes.",
            )
            
            logger("Auth", "User Service", "INFO", "null", f"OTP generated and sent to: {phone}")
            return {"message": "OTP generated successfully", "otp": token}
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"OTP generation failed for {id}: {str(e)}")
            raise HTTPException(status_code=500, detail="OTP generation failed")


    """Verify OTP token"""
    async def verify_otp(self, token: str, otp: int, request: Request):
        try:
            token_data = decode_otp_token(token)
            if not token_data or "otp" not in token_data:
                logger("Auth", "User Service", "WARN", "MEDIUM", "Invalid or expired OTP token")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired OTP"
                )
                
            if token_data["otp"] != otp:
                logger("Auth", "User Service", "WARN", "HIGH", "Invalid OTP verification attempt")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OTP"
                )
                
            logger("Auth", "User Service", "INFO", "null", "OTP verified successfully")
            return {"message": "OTP verified successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger("Auth", "User Service", "ERROR", "ERROR", f"OTP verification failed: {str(e)}")
            raise HTTPException(status_code=500, detail="OTP verification failed")