from auth.core.security import oauth2_scheme
from auth.model.model import User
from auth.config.redis import is_jti_blacklisted
from fastapi import Depends, HTTPException, status
from typing import Annotated
from auth.helper.utils import decode_access_token
from auth.config.database import user1_collection_name,user2_collection_name
async def get_access_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    data = decode_access_token(token)
    if data is None or await is_jti_blacklisted(data["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    return data

async def get_current_user1(token_data: Annotated[dict, Depends(get_access_token)]) -> dict:
    if "id" not in token_data:
     raise HTTPException(status_code=401, detail="Token payload missing 'id'")
    return await user1_collection_name.find_one({"id": token_data["id"]})
async def get_current_user2(token_data: Annotated[dict, Depends(get_access_token)]) -> dict:
    if "id" not in token_data:
     raise HTTPException(status_code=401, detail="Token payload missing 'id'")
    return await user2_collection_name.find_one({"id": token_data["id"]})
User1Dep = Annotated[User, Depends(get_current_user1)]
User2Dep = Annotated[User, Depends(get_current_user2)]