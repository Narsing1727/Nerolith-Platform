from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str
    database_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket: str
    api_secret_key: str
    anthropic_api_key: str
    environment: str = "development"
    broker_connection_retry_on_startup: bool = True

    class Config:
        env_file = ".env"


settings = Settings()