from fastapi import FastAPI
from app.models.schemas import UserQuery
from app.agent.agent import resolve_access

app = FastAPI()

@app.post("/resolve")
def resolve(query: UserQuery):
    response = resolve_access(query.user_id, query.query)
    return response