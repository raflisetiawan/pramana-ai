# Pramana AI — Smart-Claim Co-Pilot

> **Pramana** (प्रमाण) — "alat pembuktian", "sumber pengetahuan yang benar"

Sistem AI untuk verifikasi klaim BPJS Kesehatan yang membantu verifikator dengan:
- 🧠 **NLP Engine** — Ekstraksi koding ICD-10/ICD-9 otomatis dari resume medis
- 📊 **ML Engine** — Risk scoring per berkas klaim (0–100) dengan explainability (SHAP)
- 🔗 **Mock VClaim** — Simulasi lengkap VClaim 2.0 BPJS untuk development
- 🖥️ **Dashboard** — Triage interface untuk verifikator BPJS

---

## Quick Start

### Prerequisites
- Python >= 3.11
- Docker >= 24.0
- Node.js >= 20.0

### Setup

```bash
# 1. Clone & setup environment
git clone <repo-url>
cd pramana-ai
cp .env.example .env
# Edit .env, isi semua nilai yang kosong

# 2. Jalankan semua service
make dev

# 3. Akses
# API Gateway:  http://localhost:8000/docs
# Mock VClaim:  http://localhost:8001/docs
# NLP Engine:   http://localhost:8002/docs
# ML Engine:    http://localhost:8003/docs
```

### Development (tanpa Docker)

```bash
# Jalankan infrastructure dulu
make dev-infra

# Lalu jalankan masing-masing service di terminal terpisah
cd services/mock-vclaim && uvicorn app.main:app --reload --port 8001
cd services/api-gateway && uvicorn app.main:app --reload --port 8000
```

### Makefile Commands

| Command | Deskripsi |
|---|---|
| `make dev` | Jalankan semua service |
| `make dev-infra` | Jalankan PostgreSQL & Redis saja |
| `make stop` | Hentikan semua service |
| `make test` | Jalankan semua tests |
| `make migrate` | Jalankan database migration |
| `make seed` | Isi data dummy |
| `make health` | Cek health semua service |
| `make logs` | Lihat logs semua service |
| `make help` | Tampilkan semua command |

---

## Arsitektur

```
┌──────────────────────────────────────────────────────┐
│                  NGINX (Port 80/443)                  │
└─────┬──────────────┬──────────────┬──────────────────┘
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────────┐  ┌──────────────┐
│ Frontend │  │ API Gateway  │  │  Mock VClaim │
│  :3000   │  │   :8000      │  │    :8001     │
└──────────┘  └──────┬───────┘  └──────────────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
   ┌──────────┐ ┌─────────┐ ┌──────────┐
   │NLP Engine│ │ML Engine│ │ Auth Svc │
   │  :8002   │ │  :8003  │ │  :8004   │
   └──────────┘ └─────────┘ └──────────┘
          │          │
          └────┬─────┘
               ▼
        ┌─────────────┐     ┌───────┐
        │ PostgreSQL   │     │ Redis │
        │   :5432      │     │ :6379 │
        └─────────────┘     └───────┘
```

---

## Struktur Direktori

```
pramana-ai/
├── services/
│   ├── api-gateway/       # Entry point, routing, auth
│   ├── mock-vclaim/       # Simulasi VClaim 2.0 BPJS
│   ├── nlp-engine/        # NER + ICD coding dari resume medis
│   ├── ml-engine/         # Risk scoring (XGBoost + RF ensemble)
│   └── auth-service/      # JWT auth, user management, RBAC
├── frontend/              # React + TypeScript dashboard
├── database/              # Migrations & seeds
├── shared/                # Shared schemas & constants
├── tests/                 # Unit & integration tests
├── docker-compose.yml     # Development
├── docker-compose.prod.yml # Production
├── Makefile               # Shortcut commands
└── .env.example           # Template environment variables
```

---

## Dokumentasi

- [SPEC.md](.instructions/SPEC.md) — Spesifikasi teknis lengkap
- [TASK.md](.instructions/TASK.md) — Rencana pelaksanaan MVP
- [ENV.md](.instructions/ENV.md) — Panduan konfigurasi environment
- [MOCK_API_SPEC.md](.instructions/MOCK_API_SPEC.md) — Spesifikasi Mock VClaim API

---

## Tim

**Dikembangkan oleh:** Siena Clinical  
**Domain:** Verifikasi Klaim BPJS Kesehatan  
**Target Deployment:** Rumah Sakit Tipe B + Kantor Cabang BPJS

---

## Lisensi

Proprietary — Siena Clinical © 2024
