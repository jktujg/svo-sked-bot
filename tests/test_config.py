from unittest import TestCase

from bot.config import Settings


valid_payload = dict(
    BOT_NAME='bot_name',
    BOT_TOKEN='token',
    DB_HOST='mongodb://mongodb',
    DB_PORT=27017,
    DB_USERNAME='db_username',
    DB_PASSWORD='db_password',
    UPDATE_METHOD='long-polling',
    WEBHOOK_SECRET='webhook_secret',
    WEBHOOK_ENDPOINT='my-bot/webhook',
    WEBHOOK_BASE='https://example.com',
    WEBHOOK_URL='https://example.com/my-bot/webhook',
    WEB_SERVER_HOST='127.0.0.1',
    WEB_SERVER_PORT=9898,
)


class TestSettings(TestCase):
    def test_valid_config(self):
        Settings(**valid_payload)

    def test_webhook_mandatory_unset_raises(self):
        with self.assertRaisesRegex(ValueError, expected_regex='.*WEBHOOK_ENDPOINT, WEBHOOK_BASE must be set'):
            Settings(**(valid_payload | dict(
                UPDATE_METHOD='webhook',
                WEBHOOK_ENDPOINT=None,
                WEBHOOK_BASE=None,
            )))
