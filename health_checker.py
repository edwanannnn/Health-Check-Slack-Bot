"""
Health Checker — hits TensorNex API endpoints and tracks state changes
so the bot only alerts when something actually goes down or recovers.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

logger = logging.getLogger("tensornex-bot.checker")


class HealthChecker:
    def __init__(self, config):
        self.base_url = config.TENSORNEX_BASE_URL.rstrip("/")
        self.api_key = config.TENSORNEX_API_KEY
        self.timeout = config.REQUEST_TIMEOUT

        # Previous service states — populated after first check
        self._previous: Dict[str, str] = {}
        self._first_run = True

    # ── individual probes ────────────────────────────────────────────

    def check_gpu(self) -> Dict[str, Any]:
        """GET /health — GPU status (no auth required)."""
        try:
            with httpx.Client(timeout=self.timeout) as c:
                r = c.get(f"{self.base_url}/health")
                r.raise_for_status()
                return {"reachable": True, **r.json()}
        except Exception as e:
            logger.error("GPU health check failed: %s", e)
            return {
                "reachable": False,
                "error": str(e),
                "status": "unreachable",
            }

    def check_services(self) -> Dict[str, str]:
        """GET /internal/service-health — all backend services (auth required)."""
        try:
            with httpx.Client(timeout=self.timeout) as c:
                r = c.get(
                    f"{self.base_url}/internal/service-health",
                    headers={"X-Internal-Key": self.api_key},
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("Service health check failed: %s", e)
            return {"_api_error": str(e)}

    def _post_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        json_payload: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> httpx.Response:
        """
        Sends an HTTP POST with retry logic to avoid false alarms from transient
        socket drops or keep-alive race conditions (e.g. RemoteProtocolError).
        """
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(
                        url,
                        headers={**headers, "Connection": "close"},
                        json=json_payload,
                    )
                    return resp
            except (
                httpx.RemoteProtocolError,
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteError,
            ) as exc:
                last_exc = exc
                if attempt < max_retries:
                    logger.warning(
                        "Probe %s failed (attempt %d/%d): %s — retrying in %.1fs",
                        url,
                        attempt,
                        max_retries,
                        exc,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
            except Exception as exc:
                last_exc = exc
                break
        raise last_exc

    # ── AI & ML models probes ────────────────────────────────────────

    def check_models(self) -> Dict[str, str]:
        """Probe TensorNex internal AI/ML pipelines (Docling, BGE-M3, Reranker, spaCy)."""
        models: Dict[str, str] = {}
        headers = {"X-Internal-Key": self.api_key}

        # 1. Docling document & VLM engine
        try:
            r = self._post_with_retry(
                f"{self.base_url}/internal/docling/convert",
                headers=headers,
                json_payload={"url": f"{self.base_url}/openapi.json", "output_format": "json"},
            )
            if (
                r.status_code == 200
                or "File format not allowed" in r.text
                or "Conversion failed" in r.text
            ):
                models["docling"] = "healthy"
            elif r.status_code == 401:
                models["docling"] = "Unauthorized (Invalid Key)"
            else:
                models["docling"] = f"HTTP {r.status_code}"
        except Exception as e:
            models["docling"] = str(e)

        # 2. Embedding engine (BGE-M3)
        try:
            r = self._post_with_retry(
                f"{self.base_url}/internal/embed",
                headers=headers,
                json_payload={"texts": ["ping"], "model": "bge_m3"},
            )
            if r.status_code == 200 and "data" in r.json():
                models["embeddings (bge-m3)"] = "healthy"
            elif r.status_code == 401:
                models["embeddings (bge-m3)"] = "Unauthorized (Invalid Key)"
            else:
                models["embeddings (bge-m3)"] = f"HTTP {r.status_code}"
        except Exception as e:
            models["embeddings (bge-m3)"] = str(e)

        # 3. Embedding engine (MiniLM)
        try:
            r = self._post_with_retry(
                f"{self.base_url}/internal/embed",
                headers=headers,
                json_payload={"texts": ["ping"], "model": "minilm"},
            )
            if r.status_code == 200 and "data" in r.json():
                models["embeddings (minilm)"] = "healthy"
            elif r.status_code == 401:
                models["embeddings (minilm)"] = "Unauthorized (Invalid Key)"
            else:
                models["embeddings (minilm)"] = f"HTTP {r.status_code}"
        except Exception as e:
            models["embeddings (minilm)"] = str(e)

        # 4. Reranker engine (BGE-Reranker-v2-M3)
        try:
            r = self._post_with_retry(
                f"{self.base_url}/internal/rerank",
                headers=headers,
                json_payload={"query": "ping", "passages": ["pong"]},
            )
            if r.status_code == 200 and "results" in r.json():
                models["reranker (bge-m3)"] = "healthy"
            elif r.status_code == 401:
                models["reranker (bge-m3)"] = "Unauthorized (Invalid Key)"
            else:
                models["reranker (bge-m3)"] = f"HTTP {r.status_code}"
        except Exception as e:
            models["reranker (bge-m3)"] = str(e)

        # 5. NLP engine (spaCy)
        try:
            r = self._post_with_retry(
                f"{self.base_url}/internal/nlp",
                headers=headers,
                json_payload={"text": "TensorNex system"},
            )
            if r.status_code == 200 and "data" in r.json():
                models["nlp (spacy)"] = "healthy"
            elif r.status_code == 401:
                models["nlp (spacy)"] = "Unauthorized (Invalid Key)"
            else:
                models["nlp (spacy)"] = f"HTTP {r.status_code}"
        except Exception as e:
            models["nlp (spacy)"] = str(e)

        return models

    # ── combined check ───────────────────────────────────────────────

    def check_all(self) -> Dict[str, Any]:
        """Run every probe and return a combined snapshot."""
        return {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "gpu": self.check_gpu(),
            "models": self.check_models(),
            "services": self.check_services(),
        }

    # ── state-change detection ───────────────────────────────────────

    def detect_changes(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare *result* with the last-known state.

        Returns
        -------
        dict with keys:
            newly_down       — services that just went from healthy → error
            newly_recovered  — services that just went from error → healthy
            all_states       — full current state map
        """
        current: Dict[str, str] = {}

        # GPU / API reachability
        if result["gpu"].get("reachable"):
            current["GPU / API Server"] = "healthy"
        else:
            current["GPU / API Server"] = result["gpu"].get("error", "unreachable")

        # Individual services
        for svc, status in result.get("services", {}).items():
            if svc.startswith("_"):
                continue
            current[svc] = status

        # AI & ML models
        for mdl, status in result.get("models", {}).items():
            if mdl.startswith("_"):
                continue
            current[mdl] = status

        newly_down: List[Dict[str, str]] = []
        newly_recovered: List[Dict[str, str]] = []

        if not self._first_run:
            for svc, status in current.items():
                prev = self._previous.get(svc)
                if prev is None:
                    # New service appeared — treat as initial, skip
                    continue
                if prev == "healthy" and status != "healthy":
                    newly_down.append({"service": svc, "error": status})
                elif prev != "healthy" and status == "healthy":
                    newly_recovered.append({"service": svc})

            # Also check services that disappeared (might mean container died)
            for svc, prev_status in self._previous.items():
                if svc not in current and prev_status == "healthy":
                    newly_down.append({"service": svc, "error": "service disappeared from health response"})

        self._previous = current
        self._first_run = False

        return {
            "newly_down": newly_down,
            "newly_recovered": newly_recovered,
            "all_states": current,
        }
