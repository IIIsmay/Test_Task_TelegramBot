import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message

from app.config import Settings
from app.nlp import parse_query
from app.query_builder import execute_query

logger = logging.getLogger(__name__)

settings = Settings()

bot = Bot(token=settings.bot_token)
dp = Dispatcher()


@dp.message()
async def handle_query(message: Message):
    text = message.text.strip()
    logger.info("Incoming message: %s", text)

    try:
        query_struct = await parse_query(text)
        logger.info("Parsed query: %s", query_struct)

        result = await execute_query(query_struct)
        logger.info("Query result: %s", result)

        await message.answer(str(result))

    except Exception:
        logger.exception("Failed to process message")
        await message.answer("Не удалось обработать запрос")
