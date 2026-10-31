# TensorNex Health-Check Slack Bot 🤖

Bot Slack yang memonitor semua service TensorNex GPU Server dan mengirim alert otomatis ke Slack.

## Fitur

| Fitur | Deskripsi |
|-------|-----------|
| `/healthcheck` | Ketik di Slack → langsung dapat full report semua service |
| `@bot` mention | Mention bot di channel → sama seperti `/healthcheck` |
| DM ke bot | Kirim pesan apapun ke bot → dapat health report |
| 🚨 Auto Alert | Cek berkala, **hanya kirim alert kalau ada service yang DOWN** |
| ✅ Recovery Alert | Kirim notifikasi kalau service yang mati sudah **pulih kembali** |

> Bot **TIDAK** spam — diam kalau semua sehat. Hanya bicara saat ada perubahan status.

---

## Setup Slack App

### 1. Aktifkan Socket Mode

1. Buka **Slack App Settings** → klik app TensorNex
2. Sidebar kiri → **Socket Mode**
3. Toggle **Enable Socket Mode** → ON
4. Klik **Generate Token** → beri nama (misal `bot-socket`) → tambahkan scope `connections:write`
5. **Copy token** yang dimulai dengan `xapp-...` → ini `SLACK_APP_TOKEN`

### 2. Ambil Bot Token

1. Sidebar kiri → **OAuth & Permissions**
2. Scroll ke **Bot User OAuth Token** → copy token `xoxb-...` → ini `SLACK_BOT_TOKEN`
3. Scroll ke **Scopes** → pastikan ada:
   - `chat:write` — kirim pesan
   - `commands` — handle slash commands
   - `app_mentions:read` — baca @mentions
   - `im:history` — baca DMs
   - `im:read` — akses DM channel
   - `im:write` — balas DMs

### 3. Ambil Signing Secret

1. Sidebar kiri → **Basic Information**
2. Scroll ke **App Credentials** → **Signing Secret** → klik Show → copy → ini `SLACK_SIGNING_SECRET`

### 4. Buat Slash Command

1. Sidebar kiri → **Slash Commands**
2. Klik **Create New Command**
   - Command: `/healthcheck`
   - Short Description: `Check TensorNex service health`
   - Usage Hint: _(kosongkan)_
3. Save

### 5. Subscribe Events

1. Sidebar kiri → **Event Subscriptions**
2. Toggle ON
3. Di **Subscribe to bot events**, tambahkan:
   - `app_mention`
   - `message.im`
4. Save

### 6. Invite Bot ke Channel

Di Slack, buka channel `#monitoring` (atau channel alertnya), lalu ketik:
```
/invite @NamaBotmu
```

---

## Konfigurasi

```bash
cd slack-bot
cp .env.example .env
```

Edit `.env` dan isi semua value:

```env
SLACK_BOT_TOKEN=xoxb-xxxx-xxxx-xxxx
SLACK_APP_TOKEN=xapp-xxxx-xxxx
SLACK_SIGNING_SECRET=abc123def456
SLACK_ALERT_CHANNEL=C0BELBY2F3R

TENSORNEX_BASE_URL=http://IP_SERVER_TENSORNEX:8000
TENSORNEX_API_KEY=your-internal-api-key

CHECK_INTERVAL_MINUTES=5
REQUEST_TIMEOUT=30
```

| Variable | Keterangan |
|----------|-----------|
| `SLACK_BOT_TOKEN` | Dari OAuth & Permissions (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Dari Socket Mode (`xapp-...`) |
| `SLACK_SIGNING_SECRET` | Dari Basic Information |
| `SLACK_ALERT_CHANNEL` | Channel ID untuk auto-alert |
| `TENSORNEX_BASE_URL` | URL server TensorNex (misal `http://123.45.67.89:8000`) |
| `TENSORNEX_API_KEY` | API key internal (sama dengan `INTERNAL_API_KEY` di server) |
| `CHECK_INTERVAL_MINUTES` | Interval cek berkala (default: 5 menit) |

---

## Jalankan

### Opsi A: Langsung Python

```bash
pip install -r requirements.txt
python bot.py
```

### Opsi B: Docker

```bash
docker compose up -d
```

### Opsi C: Docker Build Manual

```bash
docker build -t tensornex-bot .
docker run -d --name tensornex-bot --env-file .env --restart unless-stopped tensornex-bot
```

---

## Cara Pakai di Slack

### On-Demand Check
```
/healthcheck
```

### Mention Bot
```
@TensorNexBot status gimana?
```

### DM Bot
Langsung kirim pesan apapun ke bot.

---

## Contoh Output

### Full Report
```
🏥 TensorNex Health Report
─────────────────────────

✅ GPU Server — HEALTHY
├─ 🎮 NVIDIA RTX A6000
├─ 💾 VRAM: 12.5 / 48.0 GB
└─ ⚡ Active tasks: 2 / 4

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

⏰ 2026-10-23 01:00:00 UTC
```

### Auto Alert (hanya muncul kalau ada service DOWN)
```
🚨 ALERT — Service Down
─────────────────────────
❌ neo4j — Connection refused

⏰ Detected at 2026-10-13 03:25:00 UTC • Previously healthy
```

### Recovery Notification
```
✅ Service Recovered
─────────────────────────
✅ neo4j — back online

⏰ Recovered at 2026-10-13 03:30:00 UTC
```
