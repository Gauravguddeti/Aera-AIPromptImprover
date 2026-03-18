
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"
    OLLAMA_MODEL: str = "llama3:8b"
    OLLAMA_HOST: str = "http://localhost:11434"
    
    class Config:
        env_file = ".env"

settings = Settings()
