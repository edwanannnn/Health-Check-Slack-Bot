"""
Configuration — loaded from environment variables (.env file supported).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Slack Credentials ──
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN: str = os.getenv("SLACK_APP_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")

    # Channel to send automated alerts to
    ALERT_CHANNEL: str = os.getenv("SLACK_ALERT_CHANNEL", "C0BELBY2F3R")

    # ── TensorNex API ──
    TENSORNEX_BASE_URL: str = os.getenv(
        "TENSORNEX_BASE_URL", "http://localhost:8000"
    )
    TENSORNEX_API_KEY: str = os.getenv("TENSORNEX_API_KEY", "")

    # ── Health-check schedule ──
    CHECK_INTERVAL_MINUTES: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "5"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
