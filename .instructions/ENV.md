# ENV.md — Panduan Konfigurasi Environment

> File ini menjelaskan semua environment variable yang digunakan di proyek Pramana AI,  
> cara setup untuk development, dan constraint infrastruktur target deployment.

---

## 1. Constraint Infrastruktur Target

### Server Rumah Sakit (Production Target)
```
CPU:     Minimum 4 core (Intel/AMD x86_64)
RAM:     16 GB (target RS Tipe B)
Storage: 500 GB SSD
OS:      Ubuntu 22.04 LTS
GPU:     TIDAK ADA — semua inferensi harus CPU-only
Network: Bisa offline (intermittent internet)
```

### Konsekuensi Teknis dari Constraint Ini
- **Tidak ada GPU** → Model NLP harus ringan, gunakan `indobert-lite` atau distilled model. Batch size kecil. Inferensi async agar tidak blocking.
- **RAM 16GB** → Semua service total tidak boleh melebihi 12GB RAM (sisakan 4GB untuk OS). Gunakan lazy loading untuk model.
- **Offline-capable** → Mock VClaim harus bisa serve data lokal. Sistem harus tetap berjalan tanpa koneksi ke server pusat BPJS.
- **Single host** → Docker Compose (bukan Kubernetes). Semua service di satu mesin.

### Estimasi Kebutuhan RAM per Service
| Service | RAM Estimasi |
|---|---|
| PostgreSQL | 2 GB |
| Redis | 512 MB |
| API Gateway | 512 MB |
| Mock VClaim | 256 MB |
| NLP Engine (model loaded) | 3–4 GB |
| ML Engine (model loaded) | 512 MB |
| Auth Service | 256 MB |
| Frontend (Nginx) | 128 MB |
| **Total** | **~8–9 GB** |

---

## 2. File `.env` untuk Development

Buat file `.env` di root direktori project. **JANGAN commit ke git.**

```bash
# =============================================================
# PRAMANA AI — Environment Variables
# Development Configuration
# =============================================================
# Copy file ini ke .env dan sesuaikan nilainya
# JANGAN simpan nilai secrets di file ini saat commit
# =============================================================

# --- ENVIRONMENT ---
APP_ENV=development
# Values: development | staging | production
DEBUG=true
LOG_LEVEL=DEBUG
# Values: DEBUG | INFO | WARNING | ERROR

# --- API GATEWAY (Port 8000) ---
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000
API_GATEWAY_WORKERS=2

# --- JWT AUTH ---
JWT_SECRET_KEY=GANTI_DENGAN_STRING_RANDOM_MINIMAL_64_KARAKTER
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# --- POSTGRESQL ---
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pramana_dev
POSTGRES_USER=pramana_user
POSTGRES_PASSWORD=GANTI_PASSWORD_AMAN
DATABASE_URL=postgresql+asyncpg://pramana_user:GANTI_PASSWORD_AMAN@localhost:5432/pramana_dev
# Untuk Alembic (sync):
DATABASE_URL_SYNC=postgresql://pramana_user:GANTI_PASSWORD_AMAN@localhost:5432/pramana_dev

# --- REDIS ---
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB_CACHE=0
REDIS_DB_CELERY=1
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# --- MOCK VCLAIM SERVICE ---
MOCK_VCLAIM_HOST=0.0.0.0
MOCK_VCLAIM_PORT=8001
# Consumer ID & Key untuk development (bebas diisi)
VCLAIM_CONS_ID=pramana_dev_cons_id
VCLAIM_SECRET_KEY=pramana_dev_secret_key_32chars_min
VCLAIM_USER_KEY=pramana_dev_user_key
# Simulasi delay response (ms) — 0 untuk development
MOCK_VCLAIM_RESPONSE_DELAY_MS=0
# Simulasi error rate (0.0 - 1.0) — 0 untuk development
MOCK_VCLAIM_ERROR_RATE=0.0

# --- NLP ENGINE (Port 8002) ---
NLP_ENGINE_HOST=0.0.0.0
NLP_ENGINE_PORT=8002
NLP_ENGINE_WORKERS=1
# Path ke model yang sudah didownload/ditraining
NLP_MODEL_PATH=./services/nlp-engine/app/models/indobert-medical
# Confidence threshold — kode di bawah ini akan di-flag untuk review
NLP_CONFIDENCE_THRESHOLD=0.75
# Maksimal token input (batasi untuk hemat RAM)
NLP_MAX_TOKEN_LENGTH=512
# Jumlah kandidat ICD yang dikembalikan sebelum filtering
NLP_TOP_K_CANDIDATES=5

# --- ML ENGINE (Port 8003) ---
ML_ENGINE_HOST=0.0.0.0
ML_ENGINE_PORT=8003
ML_ENGINE_WORKERS=2
ML_MODEL_PATH=./services/ml-engine/app/saved_models/ensemble_v1.pkl
# Threshold risk score
ML_RISK_THRESHOLD_LOW=40
ML_RISK_THRESHOLD_HIGH=70

# --- AUTH SERVICE (Port 8004) ---
AUTH_SERVICE_HOST=0.0.0.0
AUTH_SERVICE_PORT=8004
# Password hashing
BCRYPT_ROUNDS=12

# --- FRONTEND ---
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=Pramana AI — Smart-Claim Co-Pilot
VITE_APP_VERSION=0.1.0

# --- MLFLOW (Experiment Tracking) ---
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=pramana-risk-scoring

# --- INTERNAL SERVICE URLs (antar container) ---
# Digunakan oleh api-gateway untuk memanggil service lain
NLP_ENGINE_INTERNAL_URL=http://nlp-engine:8002
ML_ENGINE_INTERNAL_URL=http://ml-engine:8003
AUTH_SERVICE_INTERNAL_URL=http://auth-service:8004
MOCK_VCLAIM_INTERNAL_URL=http://mock-vclaim:8001

# --- CORS ---
# Pisahkan dengan koma jika lebih dari satu origin
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# --- DATA PRIVACY ---
# Rounds untuk PBKDF2 hashing nomor kartu
NOKA_HASH_ITERATIONS=260000
NOKA_HASH_SALT=GANTI_DENGAN_SALT_UNIK_PER_DEPLOYMENT
```

---

## 3. File `.env.example` (yang di-commit ke Git)

File ini adalah versi "kosong" dari `.env`, berisi semua key tapi tanpa nilai sensitif.  
Commit file ini ke git sebagai referensi untuk developer baru.

```bash
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000
API_GATEWAY_WORKERS=2

JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pramana_dev
POSTGRES_USER=pramana_user
POSTGRES_PASSWORD=
DATABASE_URL=
DATABASE_URL_SYNC=

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB_CACHE=0
REDIS_DB_CELERY=1
REDIS_URL=
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=

MOCK_VCLAIM_HOST=0.0.0.0
MOCK_VCLAIM_PORT=8001
VCLAIM_CONS_ID=
VCLAIM_SECRET_KEY=
VCLAIM_USER_KEY=
MOCK_VCLAIM_RESPONSE_DELAY_MS=0
MOCK_VCLAIM_ERROR_RATE=0.0

NLP_ENGINE_HOST=0.0.0.0
NLP_ENGINE_PORT=8002
NLP_ENGINE_WORKERS=1
NLP_MODEL_PATH=./services/nlp-engine/app/models/indobert-medical
NLP_CONFIDENCE_THRESHOLD=0.75
NLP_MAX_TOKEN_LENGTH=512
NLP_TOP_K_CANDIDATES=5

ML_ENGINE_HOST=0.0.0.0
ML_ENGINE_PORT=8003
ML_ENGINE_WORKERS=2
ML_MODEL_PATH=./services/ml-engine/app/saved_models/ensemble_v1.pkl
ML_RISK_THRESHOLD_LOW=40
ML_RISK_THRESHOLD_HIGH=70

AUTH_SERVICE_HOST=0.0.0.0
AUTH_SERVICE_PORT=8004
BCRYPT_ROUNDS=12

VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=Pramana AI — Smart-Claim Co-Pilot
VITE_APP_VERSION=0.1.0

MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=pramana-risk-scoring

NLP_ENGINE_INTERNAL_URL=http://nlp-engine:8002
ML_ENGINE_INTERNAL_URL=http://ml-engine:8003
AUTH_SERVICE_INTERNAL_URL=http://auth-service:8004
MOCK_VCLAIM_INTERNAL_URL=http://mock-vclaim:8001

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

NOKA_HASH_ITERATIONS=260000
NOKA_HASH_SALT=
```

---

## 4. Docker Compose Environment

Variabel yang berbeda antara `docker-compose.yml` (dev) dan `docker-compose.prod.yml`.  
Saat menggunakan Docker Compose, service menggunakan **nama service** sebagai hostname, bukan `localhost`.

```yaml
# Perbedaan penting di docker-compose.yml:
# - POSTGRES_HOST=postgres       (bukan localhost)
# - REDIS_HOST=redis             (bukan localhost)
# - NLP_ENGINE_INTERNAL_URL=http://nlp-engine:8002
# dst.

# Contoh environment di docker-compose.yml:
services:
  api-gateway:
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
      - NLP_ENGINE_INTERNAL_URL=http://nlp-engine:8002
      - ML_ENGINE_INTERNAL_URL=http://ml-engine:8003
```

---

## 5. Cara Setup Development Environment

### Prerequisite
```bash
# Cek versi yang dibutuhkan
python --version   # >= 3.11
docker --version   # >= 24.0
node --version     # >= 20.0
npm --version      # >= 10.0
```

### Langkah 1 — Clone & Setup
```bash
git clone <repo-url>
cd pramana-ai
cp .env.example .env
# Edit .env, isi semua nilai yang kosong
```

### Langkah 2 — Jalankan Infrastructure Services
```bash
# Jalankan hanya PostgreSQL & Redis dulu
docker compose up -d postgres redis
# Tunggu sampai healthy (~10 detik)
docker compose ps
```

### Langkah 3 — Setup Database
```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Jalankan migrations
alembic upgrade head
# Seed data dummy
python -m app.seeds.run
```

### Langkah 4 — Jalankan Service Satu per Satu
```bash
# Terminal 1: Mock VClaim
cd services/mock-vclaim
uvicorn app.main:app --reload --port 8001

# Terminal 2: NLP Engine
cd services/nlp-engine
uvicorn app.main:app --reload --port 8002

# Terminal 3: ML Engine
cd services/ml-engine
uvicorn app.main:app --reload --port 8003

# Terminal 4: API Gateway
cd services/api-gateway
uvicorn app.main:app --reload --port 8000

# Terminal 5: Frontend
cd frontend
npm install
npm run dev      # Berjalan di port 5173
```

### Atau — Jalankan Semua dengan Docker Compose
```bash
docker compose up --build
# Akses:
# Frontend:    http://localhost:3000
# API Gateway: http://localhost:8000/docs
# Mock VClaim: http://localhost:8001/docs
# MLflow:      http://localhost:5000
```

---

## 6. `.gitignore` Penting

Pastikan ini ada di `.gitignore`:

```gitignore
# Environment
.env
.env.local
.env.*.local

# Model files (terlalu besar untuk git)
services/*/app/models/*.pkl
services/*/app/models/*.bin
services/*/app/saved_models/

# Python
__pycache__/
*.pyc
.venv/
venv/

# Node
node_modules/
dist/

# Database local
*.db
*.sqlite

# Logs
*.log
logs/
```

---

## 7. Variabel yang Berbeda per Environment

| Variable | Development | Staging | Production |
|---|---|---|---|
| `DEBUG` | `true` | `false` | `false` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| `BCRYPT_ROUNDS` | `10` | `12` | `14` |
| `MOCK_VCLAIM_RESPONSE_DELAY_MS` | `0` | `100` | N/A (gunakan VClaim asli) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | `480` | `60` |
| `NLP_ENGINE_WORKERS` | `1` | `2` | `4` |
| `API_GATEWAY_WORKERS` | `2` | `4` | `8` |
