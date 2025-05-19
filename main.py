import asyncio
import json
import os
from typing import List

import requests
from telethon import Button, TelegramClient, events, types
from telethon.tl import TLObject
from telethon.tl.types import InputUserSelf

# === Config ===
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
group_id = int(os.getenv("GROUP_ID"))
check_interval = int(os.getenv("CHECK_INTERVAL", "3600"))  # seconds

client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=bot_token)

approved_users = set()
try:
    with open("approved_users.json", "r") as f:
        approved_users = set(json.load(f))
except FileNotFoundError:
    approved_users = set()

# === Заглушка TLObject (не будет работать без поддержки сервером Telegram) ===
class GetUserStarGiftsRequest(TLObject):
    QUALNAME = "payments.getUserStarGifts"
    __slots__ = ["user_id", "offset", "limit"]

    def __init__(self, *, user_id, offset, limit):
        self.user_id = user_id
        self.offset = offset
        self.limit = limit

    def to_dict(self):
        return {
            "_": self.QUALNAME,
            "user_id": self.user_id,
            "offset": self.offset,
            "limit": self.limit
        }


async def get_user_gifts(user_id: int) -> List[types.TypeMessage]:
    """Return a list of gifts for the given user.

    This function relies on the unofficial ``payments.getUserStarGifts``
    request which may not be supported by Telegram. It will return an empty
    list if the request fails.
    """
    try:
        entity = await client.get_input_entity(user_id)
        result = await client(
            GetUserStarGiftsRequest(user_id=entity, offset="", limit=100)
        )
        return getattr(result, "gifts", [])
    except Exception as e:
        print(f"Failed to fetch gifts for {user_id}: {e}")
        return []


async def has_six_knockout_gifts(user_id: int) -> bool:
    """Check if the user has at least six Jack-in-the-Box Knockout gifts."""
    gifts = await get_user_gifts(user_id)
    count = 0
    for g in gifts:
        try:
            title = getattr(g.gift, "title", "").lower()
            if "jack" in title and "knockout" in title:
                count += 1
        except Exception:
            continue
    return count >= 6


async def periodic_verify() -> None:
    """Periodically verify gifts for approved users and kick if needed."""
    while True:
        to_remove = []
        for user_id in list(approved_users):
            if not await has_six_knockout_gifts(user_id):
                try:
                    await client.kick_participant(group_id, user_id)
                except Exception as e:
                    print(f"Failed to kick {user_id}: {e}")
                try:
                    await client.send_message(
                        user_id,
                        "Вы были удалены из группы из-за отсутствия необходимых подарков.",
                    )
                except Exception as e:
                    print(f"Failed to notify {user_id}: {e}")
                to_remove.append(user_id)
        if to_remove:
            for uid in to_remove:
                approved_users.discard(uid)
            with open("approved_users.json", "w") as f:
                json.dump(list(approved_users), f)
        await asyncio.sleep(check_interval)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    welcome = (
        f"Привет, {user.first_name}!\n\n"
        "Я проверю, есть ли у тебя 6 подарков Jack-in-the-Box модели Knockout.\n"
        "Нажми кнопку ниже:"
    )
    await event.respond(welcome, buttons=[Button.inline("🔍 Проверить подарки", b"check")])

@client.on(events.CallbackQuery)
async def check(event):
    if event.data != b"check":
        return

    user_id = event.sender_id

    if await has_six_knockout_gifts(user_id):
        if user_id not in approved_users:
            approved_users.add(user_id)
            with open("approved_users.json", "w") as f:
                json.dump(list(approved_users), f)
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{bot_token}/createChatInviteLink",
                params={"chat_id": group_id, "member_limit": 1}
            )
            invite_link = r.json()["result"]["invite_link"]
            await event.respond(f"✅ У тебя есть 6 подарков! Вот ссылка: {invite_link}")
        except:
            await event.respond("✅ Подарки найдены, но не удалось создать ссылку.")
    else:
        await event.respond(
            "❌ Подарков недостаточно или они скрыты. Попробуй позже или купи на @mrkt."
        )

client.loop.create_task(periodic_verify())
print("Бот запущен.")
client.run_until_disconnected()
