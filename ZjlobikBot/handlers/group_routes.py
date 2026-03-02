import asyncio
from datetime import timedelta
from aiogram import Router, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import Message, ChatPermissions, ChatMemberUpdated
from aiogram.exceptions import TelegramBadRequest
from database import add_warn, get_warns, clear_warns
from filters import IsAdminFilter
import re
from config import BAD_WORDS, BLOCK_LINKS, WHITE_LIST_DOMAINS
from database import update_user_cache
router = Router()
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


@router.my_chat_member()
async def bot_added_to_group(event: ChatMemberUpdated):
    """Срабатывает когда статус бота в чате меняется"""
    # Бота добавили в группу (был не участником, стал участником/админом)
    was_member = event.old_chat_member.status in ["left", "kicked"]
    is_member = event.new_chat_member.status in ["member", "administrator", "restricted"]

    if was_member and is_member:
        await event.answer(
            "👋 Привет! Я бот для модерации чата.\n\n"
            "⚠️ Чтобы я мог банить, мутить и удалять сообщения — "
            "выдайте мне права администратора с разрешениями:\n"
            "• Удалять сообщения\n"
            "• Блокировать пользователей\n"
            "• Ограничивать пользователей\n\n"
            "После этого я начну работать в полную силу! 🛡"
        )



def normalize_text(text: str) -> str:
    replacements = {
        'a': 'а', 'b': 'в', 'e': 'е', 'k': 'к', 'm': 'м', 'h': 'н', 'o': 'о', 'p': 'р',
        'c': 'с', 't': 'т', 'x': 'х', 'y': 'у', 'u': 'у', 'i': 'и', 'g': 'г', 'i': '1', 'l': '1', 's': '5', 'z': '3',
        '0': 'о', '3': 'з', '4': 'ч'
    }
    if not text:
        return ""
    text = text.lower()
    for eng, rus in replacements.items():
        text = text.replace(eng, rus)
    return text



async def get_target_id_by_mention(message: Message):
    # А. Проверяем, что команду пишет админ
    member = await message.chat.get_member(user_id=message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return None
    # Если вы написали @username
    if message.entities:
        for entity in message.entities:
            # Если это "умное" упоминание (выбрали из списка)
            if entity.type == "text_mention" and entity.user:
                return entity.user.id
            # Если это просто текст @имя
            elif entity.type == "mention":
                # Вырезаем никнейм из текста
                username = message.text[entity.offset:entity.offset + entity.length].replace("@", "")
                # Ищем этот никнейм в нашей базе (которую мы создали в database.py)
                from database import get_user_id_from_cache
                target_id = await get_user_id_from_cache(username)
                if target_id:
                    return target_id
    # Г. Если ничего не помогло
    await message.answer("⚠️ Я не знаю этого пользователя. Он должен что-то написать в чате, чтобы я его запомнил!")
    return None


# --- ОБРАБОТЧИКИ КОМАНД ДЛЯ ЛЮДЕЙ БЕЗ ПРАВ---

@router.message(Command("info"))
async def start(message: Message):
    await message.answer("👋Привет! Я Жлобик - бот для модерации чатов" "\nЯ могу удалять сообщения, банить пользователей и многое другое.\n\n\n"
                         "Контакты владельца бота - @Forest_dArc\n"
                         "🪙Накиньте деняк для поддержания сервера, чтобы бот работал стабильно и быстро!\n\n📞+7-(968)-034-39-87 (Т-Банк, Сбер, Яндекс Кошелек, Озон Банк, ВБ Кошелекю)")

# --- ОБРАБОТЧИКИ КОМАНД ДЛЯ ЛЮДЕЙ БЕЗ ПРАВ---



# --- ОБРАБОТЧИКИ КОМАНД ДЛЯ ЛЮДЕЙ С ПРАВАМИ---

@router.message(Command("mute"))
async def mute_user(message: Message):
    target_id = await get_target_id_by_mention(message)
    if not target_id:
        return
    try:
        permissions = ChatPermissions(can_send_messages=False)
        await message.chat.restrict(
            user_id=target_id, 
            permissions=permissions, 
            until_date=timedelta(minutes=30)
        )
        # Получаем имя пользователя для красивого ответа
        try:
            member = await message.chat.get_member(user_id=target_id)
            name = member.user.full_name
        except:
            name = f"ID: {target_id}"
        await message.answer(f"🔇 {name} замучен на 30 минут.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ Ошибка: {e}. Проверьте права бота (нужна супергруппа).")


@router.message(Command("unmute"))
async def unmute_user(message: Message):
    # Используем нашу универсальную функцию поиска ID
    target_id = await get_target_id_by_mention(message)
    if not target_id:
        return
    try:
        # Устанавливаем полные права (размучиваем)
        # Мы разрешаем отправку сообщений, медиа и предпросмотр ссылок
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await message.chat.restrict(user_id=target_id, permissions=permissions)
        # Пытаемся получить имя для красивого ответа
        try:
            member = await message.chat.get_member(user_id=target_id)
            name = member.user.full_name
        except:
            name = f"ID: {target_id}" 
        await message.answer(f"🔊 С пользователя {name} сняты все ограничения. Теперь он может писать!")
    except TelegramBadRequest as e:
        await message.answer(f"❌ Ошибка при размуте: {e}")



@router.message(Command("warn"))
async def warn_user(message: Message):
    target_id = await get_target_id_by_mention(message)
    if not target_id:
        return
    new_warns = await add_warn(target_id, message.chat.id)
    try:
        member = await message.chat.get_member(user_id=target_id)
        name = member.user.full_name
    except:
        name = f"Пользователь (ID: {target_id})"
    await message.answer(f"⚠️ {name} получил предупреждение ({new_warns}/3)")
    if new_warns >= 3:
        try:
            await message.chat.ban(user_id=target_id)
            await message.answer(f"🚫 {name} забанен за 3/3 предупреждений.")
        except TelegramBadRequest as e:
            await message.answer(f"❌ Не удалось забанить: {e}")


@router.message(Command("clearwarns"))
async def clear_warns_cmd(message: Message):
    target_id = await get_target_id_by_mention(message)
    if not target_id:
        return
    await clear_warns(target_id, message.chat.id)
    try:
        member = await message.chat.get_member(user_id=target_id)
        name = member.user.full_name
    except:
        name = f"ID: {target_id}"
    await message.answer(f"✨ Предупреждения пользователя {name} очищены.")


@router.message(Command("ban"))
async def ban_user(message: Message):
    target_id = await get_target_id_by_mention(message)
    if not target_id:
        return
    try:
        await message.chat.ban(user_id=target_id)
        try:
            member = await message.chat.get_member(user_id=target_id)
            name = member.user.full_name
        except:
            name = f"ID: {target_id}"
        await message.answer(f"🚫 {name} забанен.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ Ошибка при бане: {e}")


@router.message(Command("unban"))
async def unban_user(message: Message):
    target_id = await get_target_id_by_mention(message)
    if not target_id:
        return
    try:
        await message.chat.unban(user_id=target_id)
        await clear_warns(target_id, message.chat.id)
        try:
            member = await message.chat.get_member(user_id=target_id)
            name = member.user.full_name
        except:
            name = f"ID: {target_id}"
        await message.answer(f"✅ Пользователь {name} разбанен, варны сброшены.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- ОБРАБОТЧИКИ КОМАНД ДЛЯ ЛЮДЕЙ С ПРАВАМИ---

@router.message(F.text)
async def filter_messages(message: Message):
    # Кэшируем username -> user_id при каждом сообщении
    if message.from_user.username:
        await update_user_cache(message.from_user.username, message.from_user.id)
    # Пропускаем команды — их обработают специализированные хэндлеры
    if message.text and message.text.startswith("/"):
        return
    # Пропускаем админов
    member = await message.chat.get_member(user_id=message.from_user.id)
    if member.status in ["administrator", "creator"]:
        return
    # NEW: Очищаем текст от подмен
    text_to_check = normalize_text(message.text)
    # 1. Проверка на плохие слова (используем очищенный текст)
    found_bad_word = False
    for word in BAD_WORDS:
        if word in text_to_check:
            found_bad_word = True
            break
    # 2. Проверка ссылок (используем оригинальные сущности сообщения)
    has_link = False
    if BLOCK_LINKS and message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:
                has_link = True
                break
    if found_bad_word or has_link:
        try:
            await message.delete()
            new_warns = await add_warn(message.from_user.id, message.chat.id)
            reason = "ссылки" if has_link else "запрещенные слова"
            warning_msg = await message.answer(
                f"⚠️ {message.from_user.mention_html()}, сообщение удалено!\n"
                f"Причина: {reason}. Варны: {new_warns}/3",
                parse_mode="HTML"
            )
            if new_warns >= 3:
                await message.chat.ban(user_id=message.from_user.id)
                await message.answer(f"🚫 {message.from_user.full_name} забанен (3/3 варнов).")
            await asyncio.sleep(7)
            await warning_msg.delete()
        except Exception as e:
            print(f"Ошибка фильтра: {e}")
        return