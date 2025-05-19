import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.tl.functions.payments import GetUserStarGiftsRequest

# === Получаем переменные окружения ===
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "bot_session")

# === Проверка ===
if not api_id or not api_hash:
    print("❌ Ошибка: переменные окружения API_ID и API_HASH обязательны.")
    sys.exit(1)

try:
    api_id = int(api_id)
except ValueError:
    print("❌ Ошибка: API_ID должен быть числом.")
    sys.exit(1)

# === Основная асинхронная функция ===
async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        me = await client.get_me()
        print(f"👤 Авторизован как {me.first_name} (@{me.username or 'нет username'})")

        # Запрос на получение подарков
        try:
            result = await client(GetUserStarGiftsRequest(
                user_id=await client.get_input_entity("me"),
                offset='',
                limit=100
            ))
        except Exception as e:
            print(f"❌ Ошибка при получении подарков: {e}")
            return

        if not result.gifts:
            print("🙁 У вас нет подарков.")
            return

        print(f"🎁 Найдено {len(result.gifts)} подарков:\n")
        for gift in result.gifts:
            try:
                print(f"🎁 {gift.gift.title} — {gift.stars} ⭐")
            except Exception as e:
                print("🔍 Не удалось прочитать один из подарков:", e)

# === Запуск ===
if __name__ == "__main__":
    asyncio.run(main())
