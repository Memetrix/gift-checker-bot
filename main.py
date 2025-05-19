import asyncio
import json
import os
import requests
from io import BytesIO

from telethon import TelegramClient, events, Button

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

# === Полная ручная сериализация InputUserSelf ===
def serialize_input_user_self():
    b = BytesIO()
    b.write(int(0xb98886cf).to_bytes(4, 'little', signed=False))  # Constructor ID of InputUserSelf
    return b.getvalue()

# === Сборка запроса к payments.getUserStarGifts ===
async def get_star_gifts_raw():
    buf = BytesIO()
    method_id = 0xf8b036af
    buf.write(method_id.to_bytes(4, 'little', signed=False))  # method ID

    buf.write(serialize_input_user_self())  # user_id
    buf.write(b'\x00')  # offset (empty string)
    buf.write((100).to_bytes(4, 'little'))  # limit

    await client._sender.send(buf.getvalue())
    return await client._sender.receive()

# === Обработка команды /start ===
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    welcome = (
        f"Привет, {user.first_name}!\n\n"
        "Я проверю, есть ли у тебя 6 подарков Jack-in-the-Box модели Knockout.\n"
        "Нажми кнопку ниже:"
    )
    await event.respond(welcome, buttons=[Button.inline("🔍 Проверить подарки", b"check")])

# === Обработка кнопки ===
@client.on(events.CallbackQuery)
async def check(event):
    if event.data != b"check":
        return

    user_id = event.sender_id

    try:
        result = await get_star_gifts_raw()
    except Exception as e:
        print(f"Ошибка при получении подарков: {e}")
        await event.respond("Ошибка при проверке подарков. Возможно, они скрыты.")
        return

    raw = result.getvalue()
    raw_text = raw.decode('utf-8', errors='ignore').lower()

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
            print(f"Ошибка создания ссылки: {e}")
            await event.respond("✅ Подарки найдены, но не удалось создать ссылку.")
    else:
        await event.respond("❌ Подарков недостаточно или они скрыты. Попробуй позже или купи на @mrkt.")

print("Бот запущен.")
client.run_until_disconnected()
