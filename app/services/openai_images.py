from enum import Enum
from typing import Optional, Literal
from openai import AsyncOpenAI


class ResponseFormat(Enum):
    URL = "url"
    B64_JSON = "b64_json"


async def generate_image(
    api_key: str,
    prompt: str,
    size: Optional[Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]],
    quality: Literal["standard", "hd"],
    model: str = "dall-e-3",
    n: int = 1,
):
    client = AsyncOpenAI(api_key=api_key)
    response = await client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        n=n,
    )
    return response.data[0].url
