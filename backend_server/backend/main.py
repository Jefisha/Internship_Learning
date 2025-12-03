from fastapi import FastAPI
from pydantic import BaseModel
from query_handler import handle_query
from db import save_history, get_all_history

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/query")
async def query_api(q: Query):
    answer = await handle_query(q.question)
    save_history(q.question, answer)
    return {"question": q.question, "answer": answer}

@app.get("/history")
async def history_api():
    return get_all_history()
