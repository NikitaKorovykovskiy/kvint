from pydantic_settings import BaseSettings
import logging


class AppSettings(BaseSettings):
    url: str
    queue: str
    mongo_url: str

    class Config:
        env_file = ".env"
        extra = "allow"


def setup_settings() -> AppSettings:
    return AppSettings()


logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
    ]
)