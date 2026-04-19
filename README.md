# tg-ticket-provider

Telegram bot for internal tickets: admins post to department forum topics; staff accept in the group and continue in DMs with the bot.

## Quick start

1. Copy [.env.example](.env.example) to `.env` and fill in variables.
2. Configure departments: set `DEPARTMENTS_JSON`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Run: `python main.py`
