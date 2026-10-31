
"""
Script to delete bot's old messages in channel server-ops.
"""

import os
import sys
from config import Config
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def main():
    if not Config.SLACK_BOT_TOKEN:
        print("[ERROR] SLACK_BOT_TOKEN is not set.")
        return

    client = WebClient(token=Config.SLACK_BOT_TOKEN)

    # 1. Identify bot user ID
    try:
        auth_resp = client.auth_test()
        bot_user_id = auth_resp.get("user_id")
        bot_name = auth_resp.get("user")
        print(f"[INFO] Connected as Bot: {bot_name} (ID: {bot_user_id})")
    except Exception as e:
        print(f"[ERROR] auth_test failed: {e}")
        return

    # 2. Find channel ID for server-ops (or use Config.ALERT_CHANNEL)
    target_channel_id = None
    target_name = "server-ops"

    try:
        # Check private and public channels the bot is in
        conv_resp = client.conversations_list(types="public_channel,private_channel")
        for ch in conv_resp.get("channels", []):
            if ch.get("name") == target_name:
                target_channel_id = ch.get("id")
                print(f"[INFO] Found channel #{target_name} with ID: {target_channel_id}")
                break
    except Exception as e:
        print(f"[WARN] conversations_list failed ({e}), falling back to ALERT_CHANNEL: {Config.ALERT_CHANNEL}")

    if not target_channel_id:
        target_channel_id = Config.ALERT_CHANNEL
        print(f"[INFO] Using channel ID: {target_channel_id}")

    # 3. Fetch recent messages in the channel
    try:
        history = client.conversations_history(channel=target_channel_id, limit=30)
        messages = history.get("messages", [])
        print(f"[INFO] Found {len(messages)} recent messages in channel.")

        deleted_count = 0
        for msg in messages:
            ts = msg.get("ts")
            msg_user = msg.get("user")
            msg_bot = msg.get("bot_id")
            subtype = msg.get("subtype")

            # Check if this message was sent by our bot
            is_our_bot = (msg_user == bot_user_id) or (msg_bot is not None) or (subtype == "bot_message")

            if is_our_bot and ts:
                text_preview = msg.get("text", "")[:40] or "Blocks report"
                try:
                    client.chat_delete(channel=target_channel_id, ts=ts)
                    print(f"  [DELETED] Message ts={ts} ({text_preview})")
                    deleted_count += 1
                except SlackApiError as err:
                    print(f"  [FAIL] Failed to delete ts={ts}: {err.response.get('error')}")

        print(f"[DONE] Total deleted messages: {deleted_count}")

    except SlackApiError as e:
        err_msg = e.response.get("error")
        print(f"[ERROR] conversations_history failed: {err_msg}")
        if err_msg in ("missing_scope", "not_in_channel"):
            print(f"[HINT] If missing_scope, Slack requires 'groups:history' or 'channels:history' scope for reading.")
            print(f"       Or you can right-click the message in Slack -> 'Copy link', paste it here, and the bot will delete it directly.")

if __name__ == "__main__":
    main()
