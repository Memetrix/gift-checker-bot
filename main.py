import asyncio
import json
import os
import requests
from io import BytesIO

from telethon import TelegramClient, events, Button
from telethon.tl.types import InputUserSelf

# === Конфигурация ===
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

# === Кастомный TL-запрос через __bytes__ без BinaryWriter ===
class GetUserStarGiftsRequest:
    CONSTRUCTOR_ID = 0xf8b036af  # payments.getUserStarGifts

    def __init__(self, user_id, offset, limit):
        self.user_id = user_id
        self.offset = offset
        self.limit = limit

    def __bytes__(self):
        b = BytesIO()
        b.write(self.CONSTRUCTOR_ID.to_bytes(4, 'little', signed=False))
        b.write(bytes(self.user_id))  # Telethon TLObject поддерживает bytes(self.user_id)
        b.write(b'\x00')  # offset: пустая строка
        b.write(self.limit.to_bytes(4, 'little', signed=True))
        return b.getvalue()

# === Команда /start ===
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    welcome = (
        f"Привет, {user.first_name}!\n\n"
        "Я проверю, есть ли у тебя 6 подарков Jack-in-the-Box модели Knockout.\n"
        "Нажми кнопку ниже:"
    )
    await event.respond(welcome, buttons=[Button.inline("🔍 Проверить подарки", b"check")])

# === Проверка подарков ===
@client.on(events.CallbackQuery)
async def check(event):
    if event.data != b"check":
        return

    user_id = event.sender_id

    try:
        input_user = InputUserSelf()
        request = GetUserStarGiftsRequest(input_user, "", 100)
        result = await client._invoke(request)
    except Exception as e:
        print(f"Ошибка при получении подарков: {e}")
        await event.respond("Ошибка при проверке подарков. Возможно, они скрыты.")
        return

    try:
        raw = result.getvalue()
        raw_text = raw.decode('utf-8', errors='ignore').lower()
    except Exception:
        await event.respond("❌ Не удалось разобрать ответ.")
        return

    count = raw_text.count("jack") if "knockout" in raw_text else 0

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
            print(f"Ошибка ссылки: {e}")
            await event.respond("✅ Подарки найдены, но не удалось создать ссылку.")
    else:
        await event.respond("❌ Подарков недостаточно или они скрыты. Попробуй позже или купи на @mrkt.")

print("Бот запущен.")
client.run_until_disconnected()
