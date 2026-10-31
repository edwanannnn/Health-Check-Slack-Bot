#!/usr/bin/env python3
"""
TensorNex Health-Check Slack Bot
────────────────────────────────
• /healthcheck  →  on-demand full report
• @bot mention  →  on-demand full report
• Background    →  every N minutes, alerts ONLY on state change (down / recovered)

Runs in Socket Mode — no public URL required.
"""

import logging
import sys
import time
from threading import Thread

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config import Config
from formatter import SlackFormatter
from health_checker import HealthChecker

# ── bootstrap ────────────────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tensornex-bot")

config = Config()
checker = HealthChecker(config)
fmt = SlackFormatter()

app = App(
    token=config.SLACK_BOT_TOKEN,
    signing_secret=config.SLACK_SIGNING_SECRET,
)


# ── slash command: /healthcheck ──────────────────────────────────────

@app.command("/healthcheck")
def handle_healthcheck(ack, respond, command):
    ack("🔍 Checking TensorNex services… please wait.")
    try:
        result = checker.check_all()
        blocks = fmt.full_report(result)
        respond(blocks=blocks, response_type="in_channel")
    except Exception as exc:
        logger.error("Slash-command health check failed: %s", exc)
        respond(text=f"❌ Health check failed: {exc}")


# ── @mention trigger ─────────────────────────────────────────────────

@app.event("app_mention")
def handle_mention(event, say):
    try:
        result = checker.check_all()
        blocks = fmt.full_report(result)
        say(blocks=blocks)
    except Exception as exc:
        logger.error("Mention health check failed: %s", exc)
        say(f"❌ Health check failed: {exc}")


# ── direct message trigger ───────────────────────────────────────────

@app.event("message")
def handle_dm(event, say):
    # Only respond to DMs (channel type "im")
    if event.get("channel_type") != "im":
        return
    # Ignore bot's own messages
    if event.get("bot_id"):
        return
    try:
        result = checker.check_all()
        blocks = fmt.full_report(result)
        say(blocks=blocks)
    except Exception as exc:
        logger.error("DM health check failed: %s", exc)
        say(f"❌ Health check failed: {exc}")


# ── background monitor ───────────────────────────────────────────────

def _background_monitor():
    interval_sec = config.CHECK_INTERVAL_MINUTES * 60
    logger.info(
        "Background monitor started (every %d min, channel %s)",
        config.CHECK_INTERVAL_MINUTES,
        config.ALERT_CHANNEL,
    )

    # First run — build baseline state, no alerts yet
    try:
        baseline = checker.check_all()
        checker.detect_changes(baseline)
        logger.info("Baseline health snapshot captured")
    except Exception as exc:
        logger.error("Baseline check failed: %s", exc)

    while True:
        time.sleep(interval_sec)
        try:
            result = checker.check_all()
            changes = checker.detect_changes(result)

            if changes["newly_down"]:
                names = [s["service"] for s in changes["newly_down"]]
                logger.warning("Services DOWN: %s", names)
                blocks = fmt.alert_down(changes["newly_down"])
                app.client.chat_postMessage(
                    channel=config.ALERT_CHANNEL,
                    blocks=blocks,
                    text="🚨 Service Down Alert",
                )

            if changes["newly_recovered"]:
                names = [s["service"] for s in changes["newly_recovered"]]
                logger.info("Services RECOVERED: %s", names)
                blocks = fmt.alert_recovered(changes["newly_recovered"])
                app.client.chat_postMessage(
                    channel=config.ALERT_CHANNEL,
                    blocks=blocks,
                    text="✅ Service Recovered",
                )

        except Exception as exc:
            logger.error("Scheduled check error: %s", exc)


# ── entrypoint ───────────────────────────────────────────────────────

def main():
    # Validate required credentials
    missing = []
    if not config.SLACK_BOT_TOKEN:
        missing.append("SLACK_BOT_TOKEN")
    if not config.SLACK_APP_TOKEN:
        missing.append("SLACK_APP_TOKEN")
    if not config.SLACK_SIGNING_SECRET:
        missing.append("SLACK_SIGNING_SECRET")
    if missing:
        logger.error("Missing required env vars: %s", ", ".join(missing))
        logger.error("Copy .env.example → .env and fill in the values.")
        sys.exit(1)

    banner = (
        "\n"
        "╔══════════════════════════════════════════════╗\n"
        "║   TensorNex Health-Check Bot  🤖             ║\n"
        "╠══════════════════════════════════════════════╣\n"
        f"║  Target  : {config.TENSORNEX_BASE_URL:<34}║\n"
        f"║  Channel : {config.ALERT_CHANNEL:<34}║\n"
        f"║  Interval: every {config.CHECK_INTERVAL_MINUTES} min{' ' * (27 - len(str(config.CHECK_INTERVAL_MINUTES)))}║\n"
        "╚══════════════════════════════════════════════╝"
    )
    logger.info(banner)

    # Launch background health monitor
    Thread(target=_background_monitor, daemon=True).start()

    # Start Slack Socket Mode (blocks here)
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    logger.info("Bot connected to Slack — press Ctrl+C to stop.")
    handler.start()


if __name__ == "__main__":
    main()
