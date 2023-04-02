import logging
from typing import Annotated

import openai
from fastapi import APIRouter, Depends
from starlette.responses import Response

from app.services.openai_chat import get_chatgpt
from app.services.openai_completions import get_completions
from app.services.openai_images import get_images

router = APIRouter()

logging.getLogger("backoff").setLevel(logging.ERROR)

ChatGPT = Annotated[str, Depends(get_chatgpt)]
Completions = Annotated[str, Depends(get_completions)]
Images = Annotated[str, Depends(get_images)]


@router.get("/models")
async def models(api_key: str):
    openai.api_key = api_key

    return await openai.Model.alist()


@router.post("/chatgpt")
async def chatgpt(
    message: ChatGPT,
):
    return Response(message)


@router.post("/completions")
async def completions(
    message: Completions,
):
    return Response(message)


@router.post("/images")
async def images(
    message: Images,
):
    return message
