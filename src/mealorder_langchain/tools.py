"""Local LangChain tools (date/time, Pinecone retriever, Slack, optional Pipedream gmail/pushover)."""

import asyncio
import json
from datetime import datetime, timezone
from functools import lru_cache

import httpx
from langchain_core.tools import BaseTool, tool
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from . import config


@tool
def todays_date_time() -> str:
    """Returns the current date and time (UTC). Use whenever relative dates (today, tomorrow, next Friday) must be resolved."""
    now = datetime.now(timezone.utc)
    return json.dumps(
        {
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timezone": "UTC",
        }
    )


@lru_cache(maxsize=1)
def _vector_store() -> PineconeVectorStore:
    if not config.PINECONE_API_KEY:
        raise RuntimeError("Missing PINECONE_API_KEY.")
    return PineconeVectorStore(
        host=config.PINECONE_HOST,
        pinecone_api_key=config.PINECONE_API_KEY,
        embedding=OpenAIEmbeddings(model=config.EMBEDDING_MODEL, api_key=config.OPENAI_API_KEY or None),
        namespace=config.PINECONE_NAMESPACE,
        text_key=config.PINECONE_TEXT_KEY,
    )


@tool("MealOrder")
async def search_mealorder(query: str) -> str:
    """Search the document store for general information concerning the Cloud Cafe including opening hours, location, menu items, and dietary options.

    Args:
        query: The search query to look up in the vector database.
    """
    docs = await _vector_store().asimilarity_search(query, k=5)
    texts = [d.page_content for d in docs if d.page_content and d.page_content.strip()]
    return "\n\n---\n\n".join(texts) or "No relevant matches found in the document store for this query."


@tool
async def send_slack_message(text: str, channel: str = "") -> str:
    """Sends Slack messages to a target channel using Slack API.

    Args:
        text: The message text to send to Slack (supports mrkdwn).
        channel: The Slack channel ID (e.g. C0AD5G1UX5L).
    """
    if not config.SLACK_BOT_TOKEN:
        raise RuntimeError("Missing SLACK_BOT_TOKEN.")
    if not text:
        raise RuntimeError("Missing text content for Slack message.")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {config.SLACK_BOT_TOKEN}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={"channel": channel or config.SLACK_CHANNEL_ID, "text": text},
            )
        return json.dumps(res.json())
    except Exception as e:
        return f"Error connecting to Slack: {e}"


def _run_pipedream_action(action_id: str, props: dict) -> str:
    from pipedream import Pipedream

    client = Pipedream(
        client_id=config.PIPEDREAM_CLIENT_ID,
        client_secret=config.PIPEDREAM_CLIENT_SECRET,
        project_id=config.PIPEDREAM_PROJECT_ID,
        project_environment=config.PIPEDREAM_ENVIRONMENT,
    )
    result = client.actions.run(
        id=action_id,
        external_user_id=config.PIPEDREAM_EXTERNAL_USER_ID,
        configured_props=props,
    )
    return str(result.model_dump() if hasattr(result, "model_dump") else result)


@tool
async def gmail(to: str, subject: str, body: str) -> str:
    """Sends an email via Gmail. Body should be professionally formatted HTML.

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: HTML email body.
    """
    props = {
        "gmail": {"authProvisionId": config.PIPEDREAM_GMAIL_ACCOUNT_ID},
        "to": to,
        "subject": subject,
        "body": body,
        "bodyType": "html",
    }
    return await asyncio.to_thread(_run_pipedream_action, "gmail-send-email", props)


@tool
async def send_pushover_message(message: str, title: str = "") -> str:
    """Sends a push notification / text-style alert via Pushover.

    Args:
        message: Concise notification message.
        title: Short notification title.
    """
    props = {
        "pushover": {"authProvisionId": config.PIPEDREAM_PUSHOVER_ACCOUNT_ID},
        "message": message,
        "title": title,
    }
    return await asyncio.to_thread(_run_pipedream_action, "pushover-send-message", props)


def local_tools() -> list[BaseTool]:
    tools: list[BaseTool] = [todays_date_time, search_mealorder, send_slack_message]
    if config.pipedream_enabled():
        if config.PIPEDREAM_GMAIL_ACCOUNT_ID:
            tools.append(gmail)
        if config.PIPEDREAM_PUSHOVER_ACCOUNT_ID:
            tools.append(send_pushover_message)
    return tools
