# MealOrder Agent (Max) - LangChain

FastAPI web service (uv project) that runs the MealOrder agent on LangChain:

- `langchain.agents.create_agent` runs the tool-calling loop (replaces the hand-written OpenAI loop)
- `langchain-openai` / `langchain-google-genai` chat models, selected by `PROVIDER`
- `langchain-mcp-adapters` loads the Workday MealOrder MCP server tools
- `langchain-pinecone` + `OpenAIEmbeddings` back the `MealOrder` document-store tool
- Slack and optional Pipedream Connect (gmail/pushover) are `@tool` functions in `tools.py`

## Local
    uv sync
    cp .env.example .env   # fill in secrets
    uv run mealorder-langchain
    curl -X POST localhost:8000/chat/<CHAT_PATH_SECRET> -H "Content-Type: application/json" -d '{"message":"List restaurants"}'

If `CHAT_PATH_SECRET` is empty the endpoint is plain `/chat`.

## Deploy (Render)
Push to GitHub, then Render > New > Blueprint pointing at the repo (uses `render.yaml`). Set secrets in the dashboard.
Set `CHAT_PATH_SECRET` (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`); the
service URL then is `https://<service>.onrender.com/chat/<CHAT_PATH_SECRET>`, so no keys need to be passed in
the request payload. Optionally set `API_TOKEN` to also require a bearer token.
