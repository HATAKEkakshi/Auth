import random
import string
from phonenumbers.phonenumberutil import region_code_for_country_code
import pycountry
from passlib.context import CryptContext
# Password hashing context
password_context=CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_country_from_dial_code(dial_code: str) -> str:
    try:
        # Remove '+' if present and convert to integer
        code = int(dial_code.strip().replace("+", ""))
        
        # Get ISO Alpha-2 region code (e.g., 'IN' for +91)
        region_code = region_code_for_country_code(code)
        if not region_code:
            return "Country not recognized for this code."

        # Use pycountry to get full country name
        country = pycountry.countries.get(alpha_2=region_code)
        return country.name if country else "Country not found in database."
    except Exception as e:
        return f"Invalid input: {e}"
def id_generator(length=7):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    return ''.join(random.choices(characters, k=length))
def generate_country(dial_code: str) -> str:
     try:
        # Remove '+' if present and convert to integer
        code = int(dial_code.strip().replace("+", ""))
        
        # Get ISO Alpha-2 region code (e.g., 'IN' for +91)
        region_code = region_code_for_country_code(code)
        if not region_code:
            return "Country not recognized for this code."

        # Use pycountry to get full country name
        country = pycountry.countries.get(alpha_2=region_code)
        return country.name if country else "Country not found in database."
     except Exception as e:
        return f"Invalid input: {e}"
def password_hash(password: str) -> str:
    password_hash=password_context.hash(password)
    return password_hash