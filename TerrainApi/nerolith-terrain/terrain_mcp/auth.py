from functools import wraps
from config.settings import settings


def require_api_key(api_key: str) -> bool:
    return api_key == settings.api_secret_key