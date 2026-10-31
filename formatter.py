"""
Slack Block Kit Formatter — turns raw health-check data into
beautiful, structured Slack messages.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


class SlackFormatter:
    """Build Slack Block Kit payloads for every notification type."""

    # ── block primitives ─────────────────────────────────────────────

    @staticmethod
    def _header(text: str) -> Dict:
        return {
            "type": "header",
            "text": {"type": "plain_text", "text": text, "emoji": True},
        }

    @staticmethod
    def _divider() -> Dict:
        return {"type": "divider"}

    @staticmethod
    def _section(mrkdwn: str) -> Dict:
        return {"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn}}

    @staticmethod
    def _context(mrkdwn: str) -> Dict:
        return {"type": "context", "elements": [{"type": "mrkdwn", "text": mrkdwn}]}

    @staticmethod
    def _svc_emoji(status: str) -> str:
        return "✅" if status == "healthy" else "❌"

    # ── full report (for /healthcheck) ───────────────────────────────

    def full_report(self, result: Dict[str, Any]) -> List[Dict]:
        blocks: List[Dict] = []

        blocks.append(self._header("🏥 TensorNex Health Report"))
        blocks.append(self._divider())

        # ── GPU / API server ──
        gpu = result.get("gpu", {})
        if gpu.get("reachable"):
            status = gpu.get("status", "unknown")
            emoji = {"healthy": "✅", "saturated": "⚠️"}.get(status, "❓")
            gpu_info = gpu.get("gpu", {})
            concurrency = gpu.get("concurrency", {})

            lines = [f"*{emoji} GPU Server — {status.upper()}*"]
            if gpu_info:
                lines.append(f"├─ 🎮 `{gpu_info.get('name', 'N/A')}`")
                used = gpu_info.get("vram_used_gb", "?")
                total = gpu_info.get("vram_total_gb", "?")
                lines.append(f"├─ 💾 VRAM: `{used} / {total} GB`")
            if concurrency:
                active = concurrency.get("active", "?")
                mx = concurrency.get("max_concurrent", concurrency.get("max", "?"))
                lines.append(f"└─ ⚡ Active tasks: `{active} / {mx}`")

            blocks.append(self._section("\n".join(lines)))
        else:
            err = gpu.get("error", "unknown error")
            blocks.append(
                self._section(f"*🔴 GPU Server — UNREACHABLE*\n└─ `{err}`")
            )

        blocks.append(self._divider())

        # ── AI & ML models matrix ──
        models = result.get("models", {})
        if models:
            healthy_m = sum(1 for v in models.values() if v == "healthy")
            total_m = len(models)
            blocks.append(
                self._section(f"*🧠 AI & ML Engines  ({healthy_m}/{total_m} healthy)*")
            )
            ordered_m = sorted(
                models.items(), key=lambda kv: (kv[1] == "healthy", kv[0])
            )
            m_lines = []
            for mdl, st in ordered_m:
                e = self._svc_emoji(st)
                if st == "healthy":
                    m_lines.append(f"{e}  *{mdl}*")
                else:
                    short = st if len(st) < 80 else st[:77] + "…"
                    m_lines.append(f"{e}  *{mdl}* — `{short}`")
            blocks.append(self._section("\n".join(m_lines)))
            blocks.append(self._divider())

        # ── service matrix ──
        services = result.get("services", {})

        if "_api_error" in services:
            blocks.append(
                self._section(
                    f"*❌ Cannot fetch service health*\n└─ `{services['_api_error']}`"
                )
            )
        elif services:
            healthy = sum(1 for v in services.values() if v == "healthy")
            total = len(services)

            blocks.append(
                self._section(f"*📦 Infrastructure Services  ({healthy}/{total} healthy)*")
            )

            # unhealthy first, then alphabetical
            ordered = sorted(
                services.items(), key=lambda kv: (kv[1] == "healthy", kv[0])
            )
            lines = []
            for svc, st in ordered:
                e = self._svc_emoji(st)
                if st == "healthy":
                    lines.append(f"{e}  *{svc}*")
                else:
                    short = st if len(st) < 80 else st[:77] + "…"
                    lines.append(f"{e}  *{svc}* — `{short}`")

            blocks.append(self._section("\n".join(lines)))
        else:
            blocks.append(self._section("_No service data available._"))

        # ── footer ──
        ts = result.get("timestamp", datetime.now(timezone.utc).isoformat())
        blocks.append(self._divider())
        blocks.append(self._context(f"⏰  {ts}"))

        return blocks

    # ── alert: services went DOWN ────────────────────────────────────

    def alert_down(self, down: List[Dict[str, str]]) -> List[Dict]:
        blocks: List[Dict] = []

        blocks.append(self._header("🚨 ALERT — Service Down"))
        blocks.append(self._divider())

        lines = []
        for d in down:
            err = d["error"]
            short = err if len(err) < 80 else err[:77] + "…"
            lines.append(f"❌  *{d['service']}* — `{short}`")

        blocks.append(self._section("\n".join(lines)))
        blocks.append(self._divider())

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        blocks.append(
            self._context(f"⏰  Detected at {ts}  •  Previously healthy")
        )
        return blocks

    # ── alert: services RECOVERED ────────────────────────────────────

    def alert_recovered(self, recovered: List[Dict[str, str]]) -> List[Dict]:
        blocks: List[Dict] = []

        blocks.append(self._header("✅ Service Recovered"))
        blocks.append(self._divider())

        lines = [f"✅  *{r['service']}* — back online" for r in recovered]
        blocks.append(self._section("\n".join(lines)))
        blocks.append(self._divider())

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        blocks.append(self._context(f"⏰  Recovered at {ts}"))
        return blocks

    # ── alert: entire API unreachable ────────────────────────────────

    def alert_api_unreachable(self, error: str) -> List[Dict]:
        blocks: List[Dict] = []

        blocks.append(self._header("🔴 TensorNex API Unreachable"))
        blocks.append(self._divider())
        blocks.append(
            self._section(
                "*The GPU server is not responding.*\n\n"
                f"Error: `{error}`\n\n"
                "Possible causes:\n"
                "•  Server is down or restarting\n"
                "•  Network issue between bot ↔ server\n"
                "•  Firewall blocking the connection"
            )
        )
        blocks.append(self._divider())

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        blocks.append(self._context(f"⏰  Detected at {ts}"))
        return blocks
