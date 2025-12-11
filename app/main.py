import asyncio
import logging

from app.bot import dp, bot
from app.logger import setup_logging


async def main():
    setup_logging()

    # Включаем логирование aiogram
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("Telegram bot starting")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
