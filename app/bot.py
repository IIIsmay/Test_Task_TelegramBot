import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart

from .config import Settings
from .nlp import parse_query
from .query_builder import execute_query

settings = Settings()

bot = Bot(token=settings.bot_token)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет. Я бот для аналитики по видео. Задай мне вопрос, например:\n"
        "• Сколько всего видео есть в системе?\n"
        "• На сколько просмотров в сумме выросли все видео 28 ноября 2025?\n"
    )


@dp.message()
async def handle_query(message: Message):
    user_text = message.text.strip()
    try:
        query_struct = await parse_query(user_text)
        result = await execute_query(query_struct)
        await message.answer(str(result))
    except Exception as e:
        traceback.print_exc()   # 🔥 вот это важно
        await message.answer(f"Ошибка: {e}")
