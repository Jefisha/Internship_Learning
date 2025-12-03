from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FastAPI working!"}

@app.get("/async")
async def async_endpoint():
    await asyncio.sleep(3)
    return {"message": "Finished async (3 sec delay)"}
