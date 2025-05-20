# Gift Checker Userbot

Пример userbot на [Telethon](https://github.com/LonamiWebs/Telethon), 
который использует нестандартный метод `payments.getUserStarGifts` для 
проверки подарков у пользователя.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
API_ID=<id> API_HASH=<hash> python main.py <username>
```

`<username>` — ник или телефон пользователя, у которого нужно проверить 
количество подарков. Если аргумент не указан, скрипт проверит ваш профиль.

Если у найдено шесть или больше подарков со `slug`, содержащим 
`jack` и `knockout`, выводится сообщение об успехе.
