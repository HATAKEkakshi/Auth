def individual_serializer(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "country_code": user.get("country_code"),
        "password": user.get("password"),
        "country": user.get("country"),
    }
def list_serializer(users)->list:
    return [individual_serializer(user) for user in users]
    