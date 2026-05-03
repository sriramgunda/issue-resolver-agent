#from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from app.config import MODEL_NAME, TEMPERATURE, OLLAMA_BASE_URL

from app.tools.access_tools import (
    check_account_locked,
    check_user_access,
    grant_access,
)

from app.tools.ticketing_tools import create_ticket

from app.agent.callbacks import ToolTrackingCallback
from app.models.schemas import AgentResponse, AgentStep

# LLM (Open-source - Ollama)
llm_kwargs = {"model": MODEL_NAME, "temperature": TEMPERATURE}
if OLLAMA_BASE_URL:
    llm_kwargs["base_url"] = OLLAMA_BASE_URL

llm = ChatOllama(**llm_kwargs)

# Tools list
tools = [
    check_account_locked,
    check_user_access,
    grant_access,
    create_ticket
]

# Prompt
messages = [
    ("system", """
You are an Access Resolver AI Agent.

Rules:
1. Always check if account is locked first.
2. Then check access.
3. If locked, stop and inform user.
4. If no access, either grant access or create ticket.
5. Use tools to perform actions.
6. Do NOT guess, always call tools.

STRICT RULES:
- If account is locked, respond with "Account is locked. Please contact support."
- If user has access, respond with "User has access."
- If user does not have access, call grant_access tool. If successful, respond with "Access granted."
- If grant_access fails, call create_ticket tool and respond with "Access issue. Ticket created."
- Always return a clear final response based on the tool outputs.
- If you cannot determine the intent, respond with "Unknown issue. Please contact support."
- You MUST use tools. Do not answer without calling a tool.
"""),
    ("human", "{input}")
]

# Create agent
#agent = create_tool_calling_agent(llm, tools, prompt)

agent = create_agent(
    model=llm,
    tools=tools
)

def resolve_access(user_id: str, query: str):
    input_text = f"user_id: {user_id}, query: {query}"

    callback = ToolTrackingCallback()

    try:
        response = agent.invoke(
            input={"user_id": user_id, "query": query},
            messages=messages,
            callbacks=[callback]
        )
    except ValueError as e:
        # Surface more actionable debugging info for Ollama streaming failures
        msg = (
            f"LLM invocation failed: {e}\n"
            f"Model: {MODEL_NAME}\n"
            f"OLLAMA_BASE_URL: {OLLAMA_BASE_URL}\n"
            "Possible causes: Ollama server not running, model name incorrect, or network issues.\n"
            "If you're using a local Ollama server, run: `ollama serve` and ensure the model exists."
        )
        print(msg)
        raise

    print("Final Response:", response)

    # Decision inference (deterministic)
    decision = "unknown"
    ticket_id = None

    for step in callback.steps:
        if step["step"] == "create_ticket":
            decision = "create_ticket"
            ticket_id = step["details"]
        elif step["step"] == "grant_access":
            decision = "grant_access"
        elif step["step"] == "check_account_locked" and "true" in step["details"]:
            decision = "unlock_required"

    # fallback
    if decision == "unknown":
        decision = "manual_review"

    # 🔹 Build structured steps
    steps = [
        AgentStep(**s) for s in callback.steps
    ]

    # Confidence heuristic
    confidence = 0.9 if decision != "manual_review" else 0.5

    return AgentResponse(
        user_id=user_id,
        query=query,
        decision=decision,
        result=response,
        ticket_id=ticket_id,
        steps=steps,
        confidence=confidence
    )

    # if "output" not in response:
    #    return {
    #        "result": "Agent failed, fallback triggered. Please contact support."
    #    }

    # return {
    #    "result": response["output"]
    #}
