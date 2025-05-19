import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.types import InputUserSelf
import json, os, requests

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

# === Заглушка (не будет работать без серверной поддержки метода) ===
from telethon.tl.tlobject import TLObject

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
        gifts = await client(GetUserStarGiftsRequest(
            user_id=InputUserSelf(),
            offset="",
            limit=100
        ))
    except Exception as e:
        print(f"Ошибка при получении подарков: {e}")
        await event.respond("Ошибка при проверке подарков. Возможно, они скрыты.")
        return

    try:
        gift_list = gifts.gifts  # Проверка наличия поля
    except AttributeError:
        await event.respond("Ошибка получения списка подарков.")
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
        except:
            await event.respond("✅ Подарки найдены, но не удалось создать ссылку.")
    else:
        await event.respond("❌ Подарков недостаточно или они скрыты. Попробуй позже или купи на @mrkt.")

print("Бот запущен.")
client.run_until_disconnected()
