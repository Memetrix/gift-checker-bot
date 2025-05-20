Пример userbot на `Telethon`, который использует нестандартный метод
`payments.getUserStarGifts` для проверки подарков у пользователя.

Запуск:

```
API_ID=123 API_HASH=abc python main.py <username>
```

Если у указанного пользователя есть не меньше шести подарков со `slug`,
содержащим `jack` и `knockout`, бот выведет сообщение об успехе.
