import asyncio
from telethon import TelegramClient, events, functions, types, Button
import json, requests, os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
group_id = int(os.getenv("GROUP_ID"))

client = TelegramClient("bot_session", api_id, api_hash)
client.start(bot_token=bot_token)

approved_users = set()
try:
    with open("approved_users.json", "r") as f:
        approved_users = set(json.load(f))
except FileNotFoundError:
    approved_users = set()

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    welcome = (
        f"Привет, {user.first_name}!

"
        "Этот бот проверяет, есть ли у тебя 6 подарков Jack-in-the-Box модели Knockout. "
        "Нажми кнопку ниже, чтобы проверить."
    )
    await event.respond(welcome, buttons=[Button.inline("🔍 Проверить подарки", b"check")])

@client.on(events.CallbackQuery)
async def check(event):
    if event.data != b"check":
        return

    user_id = event.sender_id
    try:
        result = await client(functions.payments.GetUserStarGiftsRequest(
            user_id=await event.get_input_sender(),
            offset="",
            limit=100
        ))
    except Exception as e:
        await event.respond("Ошибка при получении данных. Возможно, вы скрыли подарки.")
        print(e)
        return

    count = 0
    for gift in result.gifts:
        try:
            title = getattr(gift.gift, "title", "").lower()
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
            r = requests.get(f"https://api.telegram.org/bot{bot_token}/createChatInviteLink",
                             params={"chat_id": group_id, "member_limit": 1})
            invite_link = r.json()["result"]["invite_link"]
            await event.respond(f"✅ У тебя есть 6 подарков! Вот ссылка: {invite_link}")
        except Exception as e:
            print(e)
            await event.respond("✅ Подарки найдены, но не удалось создать ссылку.")
    else:
        await event.respond("❌ У тебя недостаточно подарков или они скрыты. Попробуй позже или купи на @mrkt.")

async def periodic_check():
    while True:
        for user_id in list(approved_users):
            try:
                result = await client(functions.payments.GetUserStarGiftsRequest(
                    user_id=await client.get_input_entity(user_id),
                    offset="",
                    limit=100
                ))
                count = 0
                for gift in result.gifts:
                    title = getattr(gift.gift, "title", "").lower()
                    if "jack" in title and "knockout" in title:
                        count += 1
                if count < 6:
                    requests.get(f"https://api.telegram.org/bot{bot_token}/banChatMember",
                                 params={"chat_id": group_id, "user_id": user_id})
                    requests.get(f"https://api.telegram.org/bot{bot_token}/unbanChatMember",
                                 params={"chat_id": group_id, "user_id": user_id})
                    approved_users.remove(user_id)
                    with open("approved_users.json", "w") as f:
                        json.dump(list(approved_users), f)
                    await client.send_message(user_id, "🚫 У тебя больше нет нужных подарков, доступ отозван.")
            except Exception as e:
                print(f"Ошибка проверки пользователя {user_id}: {e}")
        await asyncio.sleep(86400)

client.loop.create_task(periodic_check())
print("Бот запущен.")
client.run_until_disconnected()
