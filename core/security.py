from fastapi.security import OAuth2PasswordBearer


oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/User1/login")