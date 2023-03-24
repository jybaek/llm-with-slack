import logging

import uvicorn
from fastapi import FastAPI
from starlette.responses import Response
from .routers import chatgpt
from .internal import admin


app = FastAPI()
app.include_router(chatgpt.router)
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
