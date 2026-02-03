from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):    
    model_config = SettingsConfigDict(        
            env_file="/.env",
            env_ignore_empty=True,
            extra="ignore",
        )   
     
    ENVIRONMENT: str = "development"
    
    PROJECT_NAME: str = "ycode"
    API_V1_STR: str = "/api/v1"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "dfjdg234dfj"
    POSTGRES_DB: str = "ycode_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"    
    
    JWT_SECRET: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30    

    REDIS_URL: str = "redis://localhost:6379/0"

    ALLOWED_ORIGINS: list[str] = []

    # Yandex ID OAuth/OIDC
    YANDEX_CLIENT_ID: str = "8b4247a8c6e949668bd64b75236afcd8"
    YANDEX_CLIENT_SECRET: str = "9fdcc620f6074059b363bddc6d10e615"
    YANDEX_AUTH_URL: str = "https://oauth.yandex.ru/authorize"
    YANDEX_TOKEN_URL: str = "https://oauth.yandex.ru/token"
    YANDEX_USERINFO_URL: str = "https://login.yandex.ru/info"
    YANDEX_JWKS_URL: str = "https://login.yandex.ru/jwks"
    YANDEX_REDIRECT_URI: str = "http://localhost:8000/auth/yandex/callback"
    YANDEX_SCOPES: list[str] = ["login:email", "login:info", "login:phone"]

    YANDEX_STATE_NAME: str = "yandex_oauth_state"

settings = Settings()  # type: ignore
