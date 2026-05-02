from app.agent.classifier import classify_intent
from app.tools.access_tools import *
from app.tools.ticketing_tools import *
from app.tools.log_tools import *
from app.rag.retriever import retrieve_knowledge


def resolve_access(user_id: str, query: str):

    intent_obj = classify_intent(query)
    intent = intent_obj.intent

    logs = query_logs(user_id)
    knowledge = retrieve_knowledge(query)

    if intent == "account_locked":
        locked = check_account_locked(user_id)
        if locked["locked"]:
            return {
                "intent": intent,
                "action": "unlock_required",
                "result": "Account is locked"
            }

    if intent == "access_issue":
        access = check_user_access(user_id, "app")

        if not access["has_access"]:
            if logs["reason"] == "ROLE_MISSING":
                ticket = create_ticket(user_id, "Access Request")

                return {
                    "intent": intent,
                    "action": "ticket_created",
                    "result": "Access request submitted",
                    "ticket_id": ticket["ticket_id"]
                }
            else:
                grant_access(user_id, "app")
                return {
                    "intent": intent,
                    "action": "access_granted",
                    "result": "Access granted"
                }

    return {
        "intent": "unknown",
        "action": "manual_review",
        "result": "Need human intervention"
    }