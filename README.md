# 🤖 TensorNex Health-Check Slack Bot

> Automated infrastructure and AI/ML pipeline health monitoring bot with real-time Slack alerting — powered by Python, Docker, and Slack Bolt in Socket Mode.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-Bolt_Socket_Mode-4A154B?logo=slack&logoColor=white)
![GPU](https://img.shields.io/badge/GPU-NVIDIA_RTX_A6000-76B900?logo=nvidia&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 📌 Overview

**TensorNex Health Bot** is a production-grade observability and alerting agent engineered for high-availability AI/ML infrastructure. It continuously tracks the operational status of GPU hardware, deep learning engines, and distributed backend services, streaming formatted status updates and instant incident notifications directly to Slack engineering channels.

Operating via **Slack Socket Mode**, the bot requires **no public inbound endpoints, open ports, or reverse proxies**, making it exceptionally secure and turnkey to deploy behind enterprise firewalls or within private VPCs.

---

## ✨ Key Features

- **⚡ Zero Inbound Footprint:** Runs over WebSockets (Slack Socket Mode); no need for public IP addresses or webhook tunneling (e.g., ngrok).
- **🔕 Intelligent Noise Suppression:** Does not spam channels when services are operational. Alerts are emitted **only on state transitions** (when a service goes DOWN or RECOVERS).
- **🎮 GPU Hardware Telemetry:** Real-time VRAM allocation, hardware status, and active compute task monitoring for enterprise accelerators (e.g., NVIDIA RTX A6000).
- **🧠 AI/ML Engine Auditing:** Continuous probing of natural language processing and embedding inference endpoints (bge-m3, minilm, spacy, docling, rerankers).
- **📦 Distributed Services Monitoring:** Health aggregation across databases, message brokers, and vector stores (Kafka, Elasticsearch, Redis, Qdrant, Neo4j, MinIO).
- **💬 Interactive Operations:** On-demand full health audits via `/healthcheck` slash command, `@bot` mentions, or 1-on-1 Direct Messages.

---

## 🏗️ Architecture

```
                                  Private VPC / Infrastructure Host
┌──────────────────────┐        ┌──────────────────────────────────────────────────┐
│                      │        │                                                  │
│   Slack Workspace    │◄───────┼────────┐         ┌────────────────────────────┐  │
│                      │Socket  │        │         │   Target Infrastructure    │  │
│  • #server-ops       │Mode    │        ▼         │                            │  │
│  • Slash Commands    │(WSS)   │ ┌──────────────┐ │ • GPU Metrics (NVML)       │  │
│  • Bot Mentions      │───────►│ │  Health Bot  │─┼─► • AI/ML Engine Endpoints  │  │
│                      │        │ │ (Dockerized) │ │ • Vector DBs & Caches      │  │
└──────────────────────┘        │ └──────────────┘ │ • Message Brokers (Kafka)  │  │
                                │                  │                            │  │
                                │                  └────────────────────────────┘  │
                                └──────────────────────────────────────────────────┘
```

---

## 📊 Monitored Service Fleet

| Category | Targets & Services |
| :--- | :--- |
| **GPU Compute** | NVIDIA RTX A6000 (VRAM allocation, thermal load, active task capacity) |
| **AI & ML Engines** | `docling`, `embeddings (bge-m3)`, `embeddings (minilm)`, `nlp (spacy)`, `reranker (bge-m3)` |
| **Core Infrastructure** | `elasticsearch`, `kafka`, `minio`, `neo4j`, `qdrant`, `redis`, `searxng`, `vane`, `lightpanda` |

---

## 📸 Message Showcase

### 1. Full Production Health Audit
```text
🏥 TensorNex Health Report
─────────────────────────────────────────────

✅ GPU Server — HEALTHY
  ├ 🎮 NVIDIA RTX A6000
  ├ 💾 VRAM: 2.37 / 51.16 GB
  └ ⚡ Active tasks: 0 / 2

🧠 AI & ML Engines (5/5 healthy)
  ✅ docling
  ✅ embeddings (bge-m3)
  ✅ embeddings (minilm)
  ✅ nlp (spacy)
  ✅ reranker (bge-m3)

📦 Infrastructure Services (9/9 healthy)
  ✅ elasticsearch
  ✅ kafka
  ✅ lightpanda
  ✅ minio
  ✅ neo4j
  ✅ qdrant
  ✅ redis
  ✅ searxng
  ✅ vane

⏰ 2026-10-31 18:53:00 UTC
```

### 2. Instant Service Down Incident Alert
```text
🚨 ALERT — Service Down
─────────────────────────────────────────────
❌ neo4j — Connection refused (HTTP 503)

⏰ Detected: 2026-10-31 03:25:00 UTC • Status: Critical
```

### 3. Recovery Confirmation
```text
✅ Service Recovered
─────────────────────────────────────────────
✅ neo4j — Back online & passing health probes

⏰ Recovered: 2026-10-31 03:30:00 UTC • Outage Duration: 5m
```

---

## ⚙️ Configuration & Environment Variables

Copy the provided template and define your environment secrets:

```bash
cp .env.example .env
```

| Variable | Description |
| :--- | :--- |
| `SLACK_BOT_TOKEN` | Bot User OAuth Token (`xoxb-...`) with write permissions. |
| `SLACK_APP_TOKEN` | App-Level Token (`xapp-...`) with `connections:write` scope for Socket Mode. |
| `SLACK_SIGNING_SECRET` | Secret from Slack Basic Information to verify payload authenticity. |
| `SLACK_ALERT_CHANNEL` | Slack channel ID (e.g., `C0BELBY2F3R`) dedicated for operations alerts. |
| `TENSORNEX_BASE_URL` | Base endpoint URL of the target host or cluster. |
| `TENSORNEX_API_KEY` | Bearer/Internal API key for protected health endpoints. |
| `CHECK_INTERVAL_MINUTES`| Background polling frequency (default: `5` minutes). |
| `REQUEST_TIMEOUT` | Timeout limit for outbound HTTP health probes in seconds. |

---

## 🚀 Quickstart & Deployment

### Method 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/edwanannnn/health-bot.git
cd health-bot

# Set up your environment variables
cp .env.example .env
# nano .env

# Launch container in detached mode
docker compose up -d

# Inspect live container logs
docker compose logs -f
```

### Method 2: Standalone Python 3.11

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run daemon
python bot.py
```

---

## 🔒 Security Best Practices

- **Strict Secret Isolation:** `.env` files and production tokens are strictly ignored by `.gitignore` and never committed into version control.
- **Least-Privilege Scopes:** Bot only requests necessary read/write scopes for direct messaging and channel alerts.
- **Isolated Network Architecture:** Docker container leverages internal container networks, minimizing attack surfaces.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
