async def async_generator(message):
    for char in message:
        yield char
    yield " "
