import asyncio
from app.services.google_palm import get_palm_chat


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    while True:
        user_message = input("input: ")
        future = asyncio.ensure_future(get_palm_chat(user_message, context_unit="bard_test"))
        loop.run_until_complete(future)
        print(future.result())

    loop.close()
