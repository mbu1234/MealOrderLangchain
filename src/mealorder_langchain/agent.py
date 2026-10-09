import logging
from datetime import datetime, timezone

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.errors import GraphRecursionError

from . import config
from .prompt import build_system_prompt
from .tools import local_tools

log = logging.getLogger("mealorder.agent")


def build_model() -> BaseChatModel:
    if config.PROVIDER == "gemini":
        if not config.GEMINI_API_KEY:
            raise RuntimeError("Missing API key for provider: gemini")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL, api_key=config.GEMINI_API_KEY, temperature=config.TEMPERATURE
        )
    if not config.OPENAI_API_KEY:
        raise RuntimeError(f"Missing API key for provider: {config.PROVIDER}")
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=config.OPENAI_MODEL, api_key=config.OPENAI_API_KEY, temperature=config.TEMPERATURE)


async def run_agent(user_prompt: str) -> str:
    model = build_model()
    mcp_client = MultiServerMCPClient(
        {"workday": {"transport": "streamable_http", "url": config.MCP_URL}},
    )
    mcp_tools = await mcp_client.get_tools()

    now = datetime.now(timezone.utc).strftime("%m/%d/%Y, %I:%M:%S %p")
    agent = create_agent(model, tools=[*mcp_tools, *local_tools()], system_prompt=build_system_prompt(now))

    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(user_prompt)]},
            config={"recursion_limit": config.MAX_TOOL_ROUNDS * 2 + 1},
        )
    except GraphRecursionError:
        return "Sorry, I hit the maximum number of tool steps before finishing."
    return result["messages"][-1].text
