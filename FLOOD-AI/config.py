from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    llm_api_key: str
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model_name: str = "gpt-4o"

    flood_engine_host: str = "localhost"
    flood_engine_port: int = 5050

    agent_api_host: str = "localhost"
    agent_api_port: int = 8000

    data_dir: str = "./data"
    output_dir: str = "./output"
    log_dir: str = "./logs"

    timestep_interval_ms: int = 1000
    max_regions: int = 100
    agent_memory_window: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()