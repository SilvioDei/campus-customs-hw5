"""Settings for the Campus Customs agent team. The model name lives here only."""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
PROMPTS_DIR = BACKEND_DIR / "prompts"
MCP_SERVER_SCRIPT = PROJECT_DIR / "mcp_server" / "server.py"
AUDIT_TRAIL_PATH = PROJECT_DIR / "output" / "audit_trail.json"
ORIGINAL_DB_PATH = PROJECT_DIR / "data" / "campus_customs.db"      # never written
WORKING_DB_PATH = PROJECT_DIR / "data" / "campus_customs_new.db"   # what the tools use

# AI model (OpenAI via Portkey). Every agent uses this one model.
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# Guardrails that stop delegation loops and runaway token use.
MAX_DELEGATION_DEPTH = 3        # Boss -> A -> B -> C, then no further delegation
MAX_DELEGATIONS_PER_RUN = 8     # total delegate() calls allowed in one ticket run
MAX_STEPS_PER_RUN = 30          # model requests across all agents in one ticket run
MAX_TOKENS_PER_RUN = 150_000    # input + output tokens across all agents in one run
MAX_TOOL_RESULT_CHARS = 4_000   # tool results longer than this are truncated in the audit trail
MAX_ASKS_PER_AGENT = 2          # times one agent can be delegated to per run; after that, earlier answers are reused
MAX_FACT_CHARS = 700            # each shared fact is clipped to this length
MAX_FACTS_CHARS = 8_000         # total shared facts shown to agents (oldest dropped first)

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR.parent / ".env")


def get_model() -> OpenAIResponsesModel:
    """Build the shared model, authenticated with PORTKEY_API_KEY from .env.

    Uses the OpenAI Responses API (/v1/responses) through Portkey: this model
    rejects function tools on /v1/chat/completions when reasoning is on.
    """
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the HW 5 or course-root .env file.")
    client = AsyncOpenAI(api_key=key, base_url=PORTKEY_BASE_URL, default_headers={"x-portkey-api-key": key})
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
