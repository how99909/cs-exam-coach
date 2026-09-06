from api.client import ApiClient


def login(
    user_name: str,
    password: str,
):
    client = ApiClient()
    
    return client.post(
        "/auth/login",
        json={
            "user_name": user_name,
            "password": password,
        },
    )
    
    
def register(
    user_name: str,
    email: str | None,
    password: str,
):
    client = ApiClient()
    
    return client.post(
        "/auth/register",
        json={
            "user_name": user_name,
            "email": email,
            "password": password,
        },
    )
    
    
def get_me(access_token: str):
    client = ApiClient(access_token=access_token)
    
    return client.get(
        "/auth/me",
        timeout=10,
    )