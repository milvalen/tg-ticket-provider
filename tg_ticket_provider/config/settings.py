from functools import lru_cache
import json
import os
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DepartmentConfig:
    __slots__ = ("name", "thread_id")

    def __init__(self, name: str, thread_id: int) -> None:
        self.name = name
        self.thread_id = thread_id


def _load_departments(path: str | None, json_env: str | None) -> list[DepartmentConfig]:
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        items = raw.get("departments", raw) if isinstance(raw, dict) else raw
    elif json_env:
        data = json.loads(json_env)
        items = data.get("departments", data) if isinstance(data, dict) else data
    else:
        return []

    out: list[DepartmentConfig] = []
    for row in items or []:
        out.append(DepartmentConfig(name=row["name"], thread_id=int(row["thread_id"])))
    return out


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.getenv("ENV_FILE", ".env")),
        extra="ignore",
    )

    BOT_TOKEN: str
    STAFF_GROUP_CHAT_ID: int
    ADMIN_USER_IDS: str = ""
    DEPARTMENTS_FILE: str | None = None
    DEPARTMENTS_JSON: str | None = None

    SQLALCHEMY_DATABASE_URL: str
    SQLALCHEMY_DATABASE_URL_SYNC_DRIVER: str
    ECHO_SQLALCHEMY: bool = False
    LOCAL_RUN: bool = False

    @field_validator("ADMIN_USER_IDS", mode="before")
    @classmethod
    def strip_admin_ids(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    def parsed_admin_ids(self) -> set[int]:
        if not self.ADMIN_USER_IDS:
            return set()
        return {int(x.strip()) for x in self.ADMIN_USER_IDS.split(",") if x.strip()}

    def departments(self) -> list[DepartmentConfig]:
        return _load_departments(self.DEPARTMENTS_FILE, self.DEPARTMENTS_JSON)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
