from aiogram.filters import BaseFilter
from aiogram.types import Message

class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        member = await message.chat.get_member(user_id=message.from_user.id)
        return member.status in ["administrator", "creator"]