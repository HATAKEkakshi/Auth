from fastapi.security import OAuth2PasswordBearer


oauth2_scheme_user1=OAuth2PasswordBearer(tokenUrl="/User1/login")
oauth2_scheme_user2=OAuth2PasswordBearer(tokenUrl="/User2/login")
