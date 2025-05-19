import asyncio
import json
import os
import requests
from io import BytesIO

from telethon import TelegramClient, events, Button
from telethon.tl.types import InputUserSelf
from telethon.tl.tlobject import TLObject
from telethon.tl.core import TLRequest

# === Config ===
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
group_id = int(os.getenv("GROUP_ID"))

client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=bot_token)

approved_users = set()
try:
    with open("approved_users.json", "r") as f:
        approved_users = set(json.load(f))
except FileNotFoundError:
    approved_users = set()

# === Ручная реализация GetUserStarGiftsRequest ===
class GetUserStarGiftsRequest(TLRequest):
    def __init__(self, *, user_id, offset, limit):
        self.user_id = user_id
        self.offset = offset
        self.limit = limit

    def write(self):
        b = BytesIO()
        b.write(b'\xaf\x36\xb0\xf8')  # ID метода payments.getUserStarGifts (0xf8b036af)
        self.user_id.write(b)
        b.write(len(self.offset).to_bytes(1, 'little'))
        b.write(self.offset.encode('utf-8'))
        b.write(self.limit.to_bytes(4, 'little'))
        return b.getvalue()

    @staticmethod
    def read(b):
        # Заглушка — парсинг ответа зависит от TL-схемы
        pass

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

    try:
        gifts = await client.invoke(GetUserStarGiftsRequest(
            user_id=InputUserSelf(),
            offset="",
            limit=100
        ))
    except Exception as e:
        print(f"Ошибка при получении подарков: {e}")
        await event.respond("Ошибка при проверке подарков. Возможно, они скрыты.")
        return

    try:
        gift_list = gifts.gifts
    except Exception:
        await event.respond("⚠️ Не удалось прочитать список подарков.")
        return

    count = 0
    for g in gift_list:
        try:
            title = getattr(g.gift, "title", "").lower()
            if "jack" in title and "knockout" in title:
                count += 1
        except:
            continue

    if count >= 6:
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
        except Exception as e:
            print(f"Ошибка создания ссылки: {e}")
            await event.respond("✅ Подарки найдены, но не удалось создать ссылку.")
    else:
        await event.respond("❌ Подарков недостаточно или они скрыты. Попробуй позже или купи на @mrkt.")

print("Бот запущен.")
client.run_until_disconnected()
