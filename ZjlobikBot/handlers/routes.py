from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (Message,
                           CallbackQuery,
                           ReplyKeyboardMarkup,
                           KeyboardButton, 
                           InlineKeyboardMarkup, 
                           InlineKeyboardButton
)


router = Router()

def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="О боте")],
            [KeyboardButton(text="Команды"), KeyboardButton(text="Старт"), KeyboardButton(text="Помощь")]
        ],
        resize_keyboard=True
    )

    return keyboard

"""Обработка текста пользователя"""
#чтарт бота
@router.message(Command("start"), F.chat.type == "private")
@router.message(F.text.lower() == "старт")
async def start(message: Message):
    await message.answer("Привет!, Я бот для модерации чатов\n\nНапиши /commands для большей информации")

#помощь
@router.message(Command("help"), F.chat.type == "private")
@router.message(F.text.lower() == "помощь")
async def help(message: Message):
    await message.answer("Чтобы я работал, меня сначала нужно добавить группу"
                         " и выдать права администратора\n\nПосле этого, ты можешь использовать" 
                         " следующие команды:\n\n/ban - забанить пользователя\n/unban - разбанить пользователя" 
                         "\n/mute" 
                         " - замутить пользователя\n/unmute - размутить пользователя\n/warn - выдать предупреждение пользователю\n/warns"
                         " - посмотреть количество предупреждений у пользователя\n/clearwarns" 
                         " - очистить предупреждения у пользователя\n\nЕсли у тебя есть вопросы," 
                         " не стесняйся обращаться к моему создателю!\n@Forest_dArc")
# о боте
@router.message(Command("about"), F.chat.type == "private")
@router.message(F.text.lower() == "о боте")
async def about(message: Message):
    await message.answer("Я бот для модерации чатов\nПомогаю администраторам управлять своими сообществами.\nЯ могу удалять сообщения, банить пользователей и многое другое. \nЕсли у тебя есть вопросы, не стесняйся обращаться к моему создателю!\n@Forest_dArc")

#команды
@router.message(Command("commands"), F.chat.type == "private")
@router.message(F.text.lower() == "команды")
async def commands(message: Message):
    await message.answer("Команды:\n/start - запуск бота\n/help - помощь с его использованием\n/about - информация о боте\n/commands - список команд", reply_markup=create_main_keyboard())

@router.message(F.chat.type == "private")
async def someone_text(message: Message):
    await message.answer("Я не знаю такой команды, попробуй /commands для списка команд")