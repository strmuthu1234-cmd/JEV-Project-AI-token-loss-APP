"""
Central application settings, loaded from environment variables (.env).
No API keys or secrets are hard-coded here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")
APP_MODE = os.environ.get("APP_MODE", "demo")

TYPESAFE_API_KEY = os.environ.get("TYPESAFE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

MONTHLY_AI_BUDGET = float(os.environ.get("MONTHLY_AI_BUDGET", "1000"))

OPENAI_CHEAP_MODEL = os.environ.get("OPENAI_CHEAP_MODEL", "gpt-4o-mini")
OPENAI_STANDARD_MODEL = os.environ.get("OPENAI_STANDARD_MODEL", "gpt-4o")
OPENAI_ADVANCED_MODEL = os.environ.get("OPENAI_ADVANCED_MODEL", "gpt-4.1")

ANTHROPIC_CHEAP_MODEL = os.environ.get("ANTHROPIC_CHEAP_MODEL", "claude-haiku-4-5")
ANTHROPIC_STANDARD_MODEL = os.environ.get("ANTHROPIC_STANDARD_MODEL", "claude-sonnet-5")
ANTHROPIC_ADVANCED_MODEL = os.environ.get("ANTHROPIC_ADVANCED_MODEL", "claude-opus-5-5")

DEFAULT_DEPARTMENTS = [
    "R&D",
    "Web Development",
    "Game Development",
    "Android",
    "UI/UX",
    "Video Team",
    "Content Team",
    "2D/3D Team",
    "Automation",
]

DEFAULT_PROJECTS = [
    ("Shopify Development", "Web Development"),
    ("AI Video Research", "Video Team"),
    ("Game Development", "Game Development"),
    ("Content Automation", "Content Team"),
    ("Internal R&D", "R&D"),
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "jev_ai.db")


def is_jev_configured() -> bool:
    return bool(TYPESAFE_API_KEY)


def is_openai_configured() -> bool:
    return bool(OPENAI_API_KEY)


def is_anthropic_configured() -> bool:
    return bool(ANTHROPIC_API_KEY)
