from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict

class Settings(BaseSettings):
    NODE_ROLE: str = 'hq'
    NODE_ID: str = 'hq'
    DATABASE_URL: str = 'sqlite:///./dhruva.db'
    JWT_SECRET: str = 'dhruva-secret-key-change-in-production'
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRY_HOURS: int = 24
    DEMO_MODE: bool = True
    HQ_URL: str = 'http://hq:8000'
    LINK_STATUS: str = 'UP'

    model_config = SettingsConfigDict(env_prefix='DHRUVA_')

settings = Settings()

# Global dict to simulate link status per station for HQ
link_status: Dict[str, str] = {
    'hq': 'UP',
    'maitri': 'UP',
    'bharati': 'UP',
    'himadri': 'UP'
}
