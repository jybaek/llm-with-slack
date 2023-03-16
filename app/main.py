from fastapi import FastAPI
from starlette.responses import Response
from .routers import chatgpt
from .internal import admin

app = FastAPI()
app.include_router(chatgpt.router)
app.include_router(admin.router, prefix="/admin", tags=["admin"], responses={418: {"description": "I'm a teapot"}})


@app.get("/")
async def root():
    return Response("Hello ChatGPT Applications!")
