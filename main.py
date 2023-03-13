from enum import Enum

import openai
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from starlette import status
from starlette.responses import Response


API_KEY_NAME = "X-API-KEY"
app = FastAPI()


class Message(BaseModel):
    role: str = "user"
    content: str


class Model(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    TEXT_DAVINCI_003 = "text-davinci-003"
    DAVINCI = "davinci"
    CURIE = "curie"
    BABBAGE = "babbage"
    ADA = "ada"


messages = []


@app.get("/models")
async def models(api_key: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=True))):
    openai.api_key = api_key

    return await openai.Model.alist()


@app.post("/chat")
async def chat(
    message: Message,
    model: Model = Model.GPT_3_5_TURBO,
    max_tokens: int = 2048,
    presence_penalty: int = 0.5,
    frequency_penalty: int = 0.5,
    api_key: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=True)),
):
    openai.api_key = api_key
    global messages

    if len(messages) > 10:
        messages = messages[2:]

    messages.append(message.__dict__)

    # https://platform.openai.com/docs/api-reference/completions/create
    result = openai.ChatCompletion.create(
        model=model,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        messages=messages,
    )
    try:
        response = result.get("choices")[0].get("message")
        messages.append(Message(role=response.get("role"), content=response.get("content")).__dict__)
        return Response(response.get("content"))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)


@app.get("/")
async def index(request: Request):
    ip = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else request.client.host
    request.state.ip = ip.split(",")[0] if "," in ip else ip
    return Response(f"IP: {request.state.ip}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
