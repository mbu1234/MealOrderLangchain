"""Configuration. Secrets are read from the environment, loaded from a local .env via python-dotenv."""

import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


# LLM provider: "openai" or "gemini"
PROVIDER = _get("PROVIDER", "openai").lower()
OPENAI_API_KEY = _get("OPENAI_API_KEY")
GEMINI_API_KEY = _get("GEMINI_API_KEY")
OPENAI_MODEL = _get("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-3.8-flash")
TEMPERATURE = float(_get("TEMPERATURE", "0.9"))

# Max model<->tool round trips per request
MAX_TOOL_ROUNDS = int(_get("MAX_TOOL_ROUNDS", "15"))

# MCP server (Workday MealOrder)
MCP_URL = _get("MCP_URL", "https://workday-mcp-server-mpt2.onrender.com/mcp")

# Pinecone
PINECONE_API_KEY = _get("PINECONE_API_KEY")
PINECONE_HOST = _get("PINECONE_HOST", "https://mealorder-h5zbu6u.svc.aped-4627-b74a.pinecone.io")
PINECONE_NAMESPACE = _get("PINECONE_NAMESPACE", "mealorder")
PINECONE_TEXT_KEY = _get("PINECONE_TEXT_KEY", "text")
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "text-embedding-3-small")

# Slack
SLACK_BOT_TOKEN = _get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = _get("SLACK_CHANNEL_ID", "C0AD5G1UX5L")

# Pipedream Connect (optional: enables gmail + pushover tools)
PIPEDREAM_CLIENT_ID = _get("PIPEDREAM_CLIENT_ID")
PIPEDREAM_CLIENT_SECRET = _get("PIPEDREAM_CLIENT_SECRET")
PIPEDREAM_PROJECT_ID = _get("PIPEDREAM_PROJECT_ID")
PIPEDREAM_ENVIRONMENT = _get("PIPEDREAM_ENVIRONMENT", "production")
PIPEDREAM_EXTERNAL_USER_ID = _get("PIPEDREAM_EXTERNAL_USER_ID", "mealorder-agent")
PIPEDREAM_GMAIL_ACCOUNT_ID = _get("PIPEDREAM_GMAIL_ACCOUNT_ID")
PIPEDREAM_PUSHOVER_ACCOUNT_ID = _get("PIPEDREAM_PUSHOVER_ACCOUNT_ID")

# Optional hard-to-guess URL segment: when set, the chat endpoint is /chat/<CHAT_PATH_SECRET>
CHAT_PATH_SECRET = _get("CHAT_PATH_SECRET").strip("/")

# Optional shared secret; if set, callers must send "Authorization: Bearer <token>"
API_TOKEN = _get("API_TOKEN")


def pipedream_enabled() -> bool:
    return bool(PIPEDREAM_CLIENT_ID and PIPEDREAM_CLIENT_SECRET and PIPEDREAM_PROJECT_ID)
