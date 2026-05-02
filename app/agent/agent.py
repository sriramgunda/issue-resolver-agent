from langchain_ollama import ChatOllama
#from langchain_community.chat_models import ChatOllama
from app.config import MODEL_NAME, TEMPERATURE
from app.agent.utils import safe_parse

from app.tools.access_tools import *
from app.tools.ticketing_tools import *
from app.tools.log_tools import *
from app.rag.retriever import retrieve_knowledge

llm = ChatOllama(model=MODEL_NAME, temperature=TEMPERATURE)

def robust_llm_call(prompt, retries=2):
    for _ in range(retries):
        response = llm.invoke(prompt)
        parsed = safe_parse(response.content)

        if parsed.get("action") != "fallback":
            return parsed

    return {"action": "fallback"}

def resolve_access(user_id: str, query: str):

    logs = query_logs(user_id)
    knowledge = retrieve_knowledge(query)

    prompt = f"""
    You are an Access Resolver AI Agent.

    User Query: {query}

    Logs: {logs}
    Knowledge: {knowledge}

    Return STRICT JSON:
    {{
      "action": "grant_access | create_ticket | unlock_required",
      "reason": "short explanation"
    }}
    """

    #response = llm.invoke(prompt)

    #parsed = safe_parse(response.content)
    parsed = robust_llm_call(prompt)
    action = parsed.get("action", "fallback")

    # Deterministic execution layer
    if action == "unlock_required":
        return {
            "action": action,
            "result": "Account is locked"
        }

    elif action == "grant_access":
        grant_access(user_id, "app")
        return {
            "action": action,
            "result": "Access granted"
        }

    elif action == "create_ticket":
        ticket = create_ticket(user_id, query)
        return {
            "action": action,
            "result": "Access request submitted",
            "ticket_id": ticket["ticket_id"]
        }

    # fallback safety
    ticket = create_ticket(user_id, query)
    return {
        "action": "fallback_ticket",
        "result": "LLM unclear → ticket created",
        "ticket_id": ticket["ticket_id"]
    }