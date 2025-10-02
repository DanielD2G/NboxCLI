import pathlib
from typing import Optional

import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict

config_path = pathlib.Path().home() / ".config" / "nboxcli" / "credentials"
config_path.parent.mkdir(exist_ok=True, parents=True)


class NboxConfig(BaseSettings):
    nbox_url: str = pydantic.Field(
        pattern=r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
                r'([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    )
    nbox_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=config_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def save(self):
        with open(config_path, "w") as f:
            for key, value in self.model_dump().items():
                if value is not None:
                    f.write(f"{key.upper()}={value}\n")


def load_config() -> NboxConfig:
    return NboxConfig()