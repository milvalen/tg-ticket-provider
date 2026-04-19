# tg-ticket-provider

Telegram bot for internal tickets: admins post to department forum topics; staff accept in the group and continue in DMs with the bot.

## Quick start

1. Copy [.env.example](.env.example) to `.env` and fill in variables.
2. Configure departments: copy [config/departments.example.yaml](config/departments.example.yaml) to `config/departments.yaml` (or set `DEPARTMENTS_JSON`).
3. Run migrations: `alembic upgrade head`
4. Install: `pip install -e .`
5. Run: `python -m tg_ticket_provider`
