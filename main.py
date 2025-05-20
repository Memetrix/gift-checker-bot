import asyncio
import os
import sys

from telethon import TelegramClient

from gifts import GetUserStarGiftsRequest

"""Simple script to check a user's gifts using a custom request."""

# === Environment ===
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "bot_session")

# Username or phone of the target user
target = sys.argv[1] if len(sys.argv) > 1 else "me"

if not api_id or not api_hash:
    print("❌ Ошибка: переменные окружения API_ID и API_HASH обязательны.")
    sys.exit(1)

try:
    api_id_int = int(api_id)
except ValueError:
    print("❌ Ошибка: API_ID должен быть числом.")
    sys.exit(1)


async def main() -> None:
    async with TelegramClient(session_name, api_id_int, api_hash) as client:
        me = await client.get_me()
        print(f"👤 Авторизован как {me.first_name} (@{me.username or 'нет username'})")

        try:
            entity = await client.get_input_entity(target)
            result = await client(
                GetUserStarGiftsRequest(user_id=entity, offset="", limit=100)
            )
        except Exception as e:
            print(f"❌ Ошибка при получении подарков: {e}")
            return

        gifts = getattr(result, "gifts", [])
        matching = [
            g
            for g in gifts
            if "jack" in getattr(g, "slug", "").lower()
            and "knockout" in getattr(g, "slug", "").lower()
        ]
        print(f"Найдено {len(matching)} подходящих подарков")

        if len(matching) >= 6:
            print("✅ У пользователя есть нужные подарки")
        else:
            print("❌ Недостаточно подарков")


if __name__ == "__main__":
    asyncio.run(main())
