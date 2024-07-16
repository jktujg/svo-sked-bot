import argparse
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin

from pydantic import SecretStr, model_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


argument_parser = argparse.ArgumentParser()
argument_parser.add_argument('--update-method', default='long-polling', choices=['long-polling', 'webhook'])
cmd_args, _ = argument_parser.parse_known_args()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parents[1] / '.env',
        extra='ignore',
    )
    BOT_NAME: str
    BOT_TOKEN: SecretStr
    DB_HOST: str
    DB_PORT: int
    DB_USERNAME: SecretStr
    DB_PASSWORD: SecretStr
    UPDATE_METHOD: Literal['long-polling', 'webhook'] = cmd_args.update_method
    WEBHOOK_SECRET: SecretStr | None = None
    WEBHOOK_ENDPOINT: str | None = None
    WEBHOOK_BASE: str | None = None
    WEB_SERVER_HOST: str | None = None
    WEB_SERVER_PORT: int | None = None

    @computed_field
    @property
    def WEBHOOK_URL(self) -> str | None:
        if None not in (self.WEBHOOK_BASE, self.WEBHOOK_ENDPOINT):
            return urljoin(self.WEBHOOK_BASE, self.WEBHOOK_ENDPOINT)

    @model_validator(mode='after')
    def check_webhook_variables(self) -> 'Settings':
        if self.UPDATE_METHOD == 'webhook':
            mandatory_unset = list(filter(lambda x: getattr(self, x) is None, [
                'WEBHOOK_ENDPOINT',
                'WEBHOOK_BASE',
                'WEB_SERVER_HOST',
                'WEB_SERVER_PORT'
            ]))
            if mandatory_unset:
                raise ValueError(f'If `UPDATE_METHOD` is `webhook` then {", ".join(mandatory_unset)} must be set')
        return self
