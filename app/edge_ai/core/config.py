from pydantic import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # 프로젝트 루트 C:...\Smart-Home-PuriPilot
ENV_PATH = BASE_DIR / "app" / "edge_ai" / ".env"

class EdgeSettings(BaseSettings):
    EDGE_OPENAI_API_KEY: str
    EDGE_OPENAI_MODEL: str = "gpt-4.1-mini"

    class Config:
        env_file = str(ENV_PATH)

settings = EdgeSettings()
