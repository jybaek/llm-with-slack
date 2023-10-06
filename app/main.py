import logging

import uvicorn
from platform import system
from fastapi import FastAPI
from starlette.responses import Response
from .routers import chatgpt, slack
from .internal import admin


if system().lower().startswith("darwin"):
    app = FastAPI()
else:
    app = FastAPI(docs_url=None, redoc_url=None)
app.include_router(chatgpt.router, prefix="/openai", tags=["openai"])
app.include_router(slack.router, prefix="/slack", tags=["slack"])
app.include_router(admin.router, prefix="/admin", tags=["admin"], responses={418: {"description": "I'm a teapot"}})

logging.basicConfig(level=logging.INFO)


@app.get("/")
async def root():
    return Response("Hello ChatGPT Applications!")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        access_log=False,
        reload=True,
        timeout_keep_alive=65,
    )
