import logging
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from . import config
from .agent import run_agent

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MealOrder Agent (Max) - LangChain")


class ChatRequest(BaseModel):
    message: str | None = None
    question: str | None = None


def check_auth(authorization: str | None = Header(default=None)) -> None:
    if not config.API_TOKEN:
        return
    expected = f"Bearer {config.API_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


async def chat(req: ChatRequest) -> dict:
    prompt = req.message or req.question
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'message' or 'question' field in JSON request body.")
    try:
        answer = await run_agent(prompt)
    except Exception as e:
        logging.exception("Agent execution error")
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})
    return {"status": "success", "agent": "Max", "provider": config.PROVIDER, "response": answer}


# If CHAT_PATH_SECRET is set the endpoint is served only at /chat/<secret> (the URL acts as the
# credential, like a Pipedream trigger URL); any other path, including plain /chat, returns 404.
CHAT_PATH = f"/chat/{config.CHAT_PATH_SECRET}" if config.CHAT_PATH_SECRET else "/chat"
app.add_api_route(CHAT_PATH, chat, methods=["POST"], dependencies=[Depends(check_auth)])


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
