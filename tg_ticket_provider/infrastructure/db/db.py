from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from tg_ticket_provider.config.settings import get_settings

_settings = get_settings()

_connect_args: dict = {}
if "asyncpg" in _settings.SQLALCHEMY_DATABASE_URL:
    _connect_args = {
        "ssl": not _settings.LOCAL_RUN,
        "server_settings": {"application_name": "tg_ticket_provider"},
    }

engine = create_async_engine(
    _settings.SQLALCHEMY_DATABASE_URL,
    echo=_settings.ECHO_SQLALCHEMY,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=_connect_args,
)

AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
)


def get_engine():
    return engine
