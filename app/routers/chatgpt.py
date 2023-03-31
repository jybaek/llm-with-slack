import logging
from typing import Annotated

import openai
from fastapi import APIRouter, Depends
from starlette.responses import Response

from app.services.openai_chat import get_chatgpt

router = APIRouter()

logging.getLogger("backoff").setLevel(logging.ERROR)

ChatGPT = Annotated[str, Depends(get_chatgpt)]


@router.get("/models")
async def models(api_key: str):
    openai.api_key = api_key

    return await openai.Model.alist()


@router.post("/chatgpt")
async def chatgpt(
    message: ChatGPT,
):
    return Response(message)
