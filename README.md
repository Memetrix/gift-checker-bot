# Telegram Gift Checker Bot

This bot checks whether a user owns at least six **Jack-in-the-Box Knockout** gifts. When the requirement is met the bot sends an invite link to a private group. Otherwise, it asks the user to acquire the missing gifts.

## Configuration

The bot requires the following environment variables:

- `API_ID` and `API_HASH` – credentials for the Telegram API.
- `BOT_TOKEN` – token of your bot obtained from [@BotFather](https://t.me/BotFather).
- `GROUP_ID` – identifier of the private group to invite users to.
- `CHECK_INTERVAL` – interval in seconds for periodic rechecks (default: `3600`).

## Usage

Install dependencies and run the bot:

```bash
pip install -r requirements.txt
python main.py
```

