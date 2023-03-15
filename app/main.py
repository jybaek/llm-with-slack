from fastapi import FastAPI
from starlette.responses import Response
from .routers import chatgpt

app = FastAPI()
app.include_router(chatgpt.router)


@app.get("/")
async def root():
    return Response("Hello ChatGPT Applications!")
