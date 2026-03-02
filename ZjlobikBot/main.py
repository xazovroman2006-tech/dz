
from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllChatAdministrators, BotCommandScopeAllPrivateChats
from dotenv import load_dotenv
from handlers.routes import router
from database import init_db
from handlers.routes import router as private_router
from handlers.group_routes import router as group_router

load_dotenv()

"""Токен бота, который вы получили от BotFather"""
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

dp.include_router(group_router)
dp.include_router(private_router)


async def main():
    await init_db()
    bot = Bot(token=TOKEN)

    # Команды для обычных участников (видят все)
    await bot.set_my_commands(
        commands=[
            BotCommand(command="info", description="Информация о боте"),
        ],
        scope=BotCommandScopeAllGroupChats()
    )

    # Команды для администраторов (видят только админы)
    await bot.set_my_commands(
        commands=[
            BotCommand(command="info",       description="Информация о боте"),
            BotCommand(command="ban",        description="Забанить пользователя"),
            BotCommand(command="unban",      description="Разбанить пользователя"),
            BotCommand(command="mute",       description="Замутить пользователя на 30 минут"),
            BotCommand(command="unmute",     description="Размутить пользователя"),
            BotCommand(command="warn",       description="Выдать предупреждение"),
            BotCommand(command="clearwarns", description="Сбросить предупреждения"),
        ],
        scope=BotCommandScopeAllChatAdministrators()
    )

    # Команды для личных сообщений
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start",    description="Запустить бота"),
            BotCommand(command="help",     description="Помощь по использованию"),
            BotCommand(command="about",    description="Информация о боте"),
            BotCommand(command="commands", description="Список команд"),
        ],
        scope=BotCommandScopeAllPrivateChats()
    )

    print("Starting bot...")
    await dp.start_polling(bot, allowed_updates=["message", "my_chat_member"])


"""Запуск бота"""
if __name__ == "__main__":
    asyncio.run(main())