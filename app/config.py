from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_EMAILS: str = "feverjp751111@gmail.com,aaa2003.loveyou@gmail.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
