import os
from pathlib import Path
from dotenv import load_dotenv
import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"


def load_config():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    yaml_path = CONFIG_DIR / "settings.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return _render_placeholders(raw)


def _render_placeholders(obj):
    if isinstance(obj, dict):
        return {k: _render_placeholders(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_render_placeholders(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        env_key = obj[2:-1]
        return os.environ.get(env_key, "")
    return obj


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_config()
        return cls._instance

    @property
    def dashboard(self):
        return self._config.get("dashboard", {})

    @property
    def monitoring(self):
        return self._config.get("monitoring", {})

    @property
    def rules(self):
        return self._config.get("rules", {})

    @property
    def notification(self):
        return self._config.get("notification", {})

    @property
    def scheduler(self):
        return self._config.get("scheduler", {})

    @property
    def state_store(self):
        return self._config.get("state_store", {})

    @property
    def identity_mapping(self):
        return self._config.get("identity_mapping", {})

    @property
    def logging_config(self):
        return self._config.get("logging", {})

    def get_fengshu_api_base(self):
        return os.environ.get("FENGSHU_API_BASE", "https://data.bytedance.net/api")

    def get_fengshu_api_token(self):
        return os.environ.get("FENGSHU_API_TOKEN", "")

    def get_feishu_app_id(self):
        return os.environ.get("FEISHU_APP_ID", "")

    def get_feishu_app_secret(self):
        return os.environ.get("FEISHU_APP_SECRET", "")

    def get_feishu_bot_token(self):
        return os.environ.get("FEISHU_BOT_TOKEN", "")
