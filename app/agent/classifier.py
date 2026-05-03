from langchain_openai import ChatOpenAI
#from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from app.config import MODEL_NAME, TEMPERATURE

class IntentOutput(BaseModel):
    intent: str
    confidence: float

# llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
llm = ChatOllama(model=MODEL_NAME, temperature=TEMPERATURE)

def classify_intent(query: str) -> IntentOutput:
    prompt = f"""
    Classify user intent:
    Query: {query}

    Options:
    - access issue
    - account locked
    - password reset
    - unknown

    Return JSON with intent and confidence.
    """

    response = llm.invoke(prompt)

    # For Local models - sometimes return messy output, so clean it
    text = response.content
    print(text.strip())

    # Simple fallback parser
    if "locked" in query.lower():
        return IntentOutput(intent="account locked", confidence=0.8)

    # parsing results
    return IntentOutput(intent=text.strip(), confidence=response.confidence)