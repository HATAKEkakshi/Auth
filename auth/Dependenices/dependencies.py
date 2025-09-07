from auth.core.security import oauth2_scheme_user1,oauth2_scheme_user2
from auth.model.model import User
from auth.config.redis import is_jti_blacklisted
from fastapi import Depends, HTTPException, status
from typing import Annotated
from auth.helper.utils import decode_access_token
from auth.config.database import user1_collection_name,user2_collection_name
from auth.logger.log import logger
"""Decode and validate access token, check if blacklisted"""
async def _get_access_token(token: str) -> dict:
    try:
        data = decode_access_token(token)
        if data is None:
            logger("Auth", "Token Validation", "WARN", "MEDIUM", "Invalid token format or expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )
        
        if await is_jti_blacklisted(data["jti"]):
            logger("Auth", "Token Validation", "WARN", "HIGH", f"Blacklisted token attempted: {data['jti'][:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )
        
        logger("Auth", "Token Validation", "INFO", "null", "Token validation successful")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger("Auth", "Token Validation", "ERROR", "ERROR", f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
        )
"""Get and validate User1 access token"""
async def get_user1_access_token(token:Annotated[str,Depends(oauth2_scheme_user1)]):
   return await _get_access_token(token)

"""Get and validate User2 access token"""
async def get_user2_access_token(token:Annotated[str,Depends(oauth2_scheme_user2)]):
   return await _get_access_token(token)
"""Get current User1 from database using token data"""
async def get_current_user1(token_data: Annotated[dict, Depends(get_user1_access_token)]) -> dict:
    try:
        if "id" not in token_data:
            logger("Auth", "User Lookup", "WARN", "MEDIUM", "Token missing user ID")
            raise HTTPException(status_code=401, detail="Token payload missing 'id'")
        
        user = await user1_collection_name.find_one({"id": token_data["id"]})
        if not user:
            logger("Auth", "User Lookup", "WARN", "MEDIUM", f"User1 not found: {token_data['id']}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger("Auth", "User Lookup", "INFO", "null", f"User1 retrieved successfully: {token_data['id']}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger("Auth", "User Lookup", "ERROR", "ERROR", f"User1 lookup error: {str(e)}")
        raise HTTPException(status_code=500, detail="User lookup failed")
"""Get current User2 from database using token data"""
async def get_current_user2(token_data: Annotated[dict, Depends(get_user2_access_token)]) -> dict:
    try:
        if "id" not in token_data:
            logger("Auth", "User Lookup", "WARN", "MEDIUM", "Token missing user ID")
            raise HTTPException(status_code=401, detail="Token payload missing 'id'")
        
        user = await user2_collection_name.find_one({"id": token_data["id"]})
        if not user:
            logger("Auth", "User Lookup", "WARN", "MEDIUM", f"User2 not found: {token_data['id']}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger("Auth", "User Lookup", "INFO", "null", f"User2 retrieved successfully: {token_data['id']}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger("Auth", "User Lookup", "ERROR", "ERROR", f"User2 lookup error: {str(e)}")
        raise HTTPException(status_code=500, detail="User lookup failed")
# Type annotations for dependency injection
User1Dep = Annotated[User, Depends(get_current_user1)]  # User1 dependency for protected routes
User2Dep = Annotated[User, Depends(get_current_user2)]  # User2 dependency for protected routes