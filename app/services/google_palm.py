import json
import os
from typing import Annotated

import google.generativeai as palm
from fastapi import Query

from app.config.messages import context_unit_description, temperature_description, top_p_description
from app.models.redis import RedisClient

palm.configure(api_key=os.environ['API_KEY'])


async def get_palm_chat(
    message,
    context_unit: Annotated[str, Query(description=context_unit_description)] = "u_1234",
    temperature: Annotated[float, Query(description=temperature_description)] = 0.25,
    top_p: Annotated[float, Query(description=top_p_description)] = 0.95,
):
    context = ""
    examples = []
    defaults = {
        'model': 'models/chat-bison-001',
        'temperature': temperature,
        'candidate_count': 1,
        'top_k': 40,
        'top_p': top_p,
    }

    redis_conn = RedisClient().get_conn()

    messages = redis_conn.get(f"palm_{context_unit}") if redis_conn.get(f"palm_{context_unit}") else "[]"
    messages = json.loads(messages)
    messages.append(message)

    response = await palm.chat_async(**defaults, context=context, examples=examples, messages=messages)

    if not response.last:
        return "PaLM is gone... :'( "

    redis_conn.set(f"palm_{context_unit}", json.dumps(response.messages))
    return response.last
