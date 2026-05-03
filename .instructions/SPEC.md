# SPEC.md — Spesifikasi Teknis Pramana AI

> **Proyek:** Pramana AI — Smart-Claim Co-Pilot  
> **Dikembangkan oleh:** Siena Clinical  
> **Domain:** Verifikasi Klaim BPJS Kesehatan  
> **Target Deployment:** Rumah Sakit Tipe B + Kantor Cabang BPJS

---

## 1. Stack Teknologi

### Backend Services
| Layer | Teknologi | Versi | Keterangan |
|---|---|---|---|
| Runtime | Python | 3.11 | Wajib, untuk kompatibilitas library ML |
| Web Framework | FastAPI | 0.111+ | Semua service backend |
| ASGI Server | Uvicorn | 0.29+ | Dengan Gunicorn untuk production |
| Task Queue | Celery | 5.3+ | Background jobs (scanning RME, retraining) |
| Message Broker | Redis | 7.2 | Broker Celery + caching response API |
| ORM | SQLAlchemy | 2.0 | Async mode |
| DB Migrations | Alembic | 1.13+ | |

### Database
| Tujuan | Teknologi | Versi | Keterangan |
|---|---|---|---|
| Primary DB | PostgreSQL | 16 | Data klaim, audit log, user |
| Cache & Queue | Redis | 7.2 | Session, rate limit, task queue |
| Vector Store | pgvector (extension) | 0.7+ | Similarity search untuk NLP/ICD matching |

### Machine Learning
| Komponen | Library | Versi | Keterangan |
|---|---|---|---|
| ML Pipeline | scikit-learn | 1.4+ | Preprocessing, Random Forest |
| Gradient Boosting | XGBoost | 2.0+ | Model utama risk scoring |
| Explainability | SHAP | 0.45+ | Penjelasan prediksi per klaim |
| Data Processing | pandas | 2.2+ | |
| Numerical | numpy | 1.26+ | |
| Model Serialization | joblib | 1.3+ | Simpan/load model |
| Experiment Tracking | MLflow | 2.12+ | Versioning model, metrik training |

### NLP
| Komponen | Library | Versi | Keterangan |
|---|---|---|---|
| Base Framework | transformers (HuggingFace) | 4.40+ | |
| Base Model | IndoBERT (`indobenchmark/indobert-base-p1`) | - | Fine-tune untuk domain medis |
| NER Pipeline | spaCy | 3.7+ | Entitas medis (diagnosa, obat, prosedur) |
| Text Processing | re, string (stdlib) | - | |
| Fuzzy Matching | rapidfuzz | 3.9+ | ICD code lookup dengan toleransi typo |

### Frontend Dashboard
| Komponen | Teknologi | Keterangan |
|---|---|---|
| Framework | React 18 + TypeScript | |
| Build Tool | Vite 5 | |
| UI Library | shadcn/ui + Tailwind CSS | |
| State Management | Zustand | |
| Data Fetching | TanStack Query (React Query) | |
| Charting | Recharts | Visualisasi risk score, statistik |
| Table | TanStack Table | Tabel klaim dengan sorting/filter |

### Infrastruktur & DevOps
| Komponen | Teknologi | Keterangan |
|---|---|---|
| Containerization | Docker + Docker Compose | Single-host deployment |
| Reverse Proxy | Nginx | SSL termination, static files |
| Monitoring | Prometheus + Grafana | Metrik sistem dan model |
| Logging | structlog + Loki | Structured logging |
| Secret Management | python-dotenv + `.env` | Development; Vault untuk production |

---

## 2. Arsitektur Layanan (Microservices)

```
┌─────────────────────────────────────────────────────────┐
│                    NGINX (Port 80/443)                   │
└──────┬──────────────┬───────────────┬───────────────────┘
       │              │               │
       ▼              ▼               ▼
┌──────────┐  ┌──────────────┐  ┌──────────────┐
│ Frontend │  │ API Gateway  │  │  Mock VClaim │
│  :3000   │  │   :8000      │  │    :8001     │
│  React   │  │  FastAPI     │  │   FastAPI    │
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
        │ PostgreSQL  │     │ Redis │
        │   :5432     │     │ :6379 │
        └─────────────┘     └───────┘
```

### Deskripsi Setiap Service

#### `api-gateway` (Port 8000)
- Entry point utama seluruh request dari frontend
- Routing ke service yang sesuai
- Authentication & authorization (JWT)
- Rate limiting
- Request/response logging

#### `mock-vclaim` (Port 8001)
- Simulasi lengkap VClaim 2.0 BPJS Kesehatan
- Mensimulasikan auth (Signature HMAC-SHA256)
- Menyimpan state transaksi di Redis
- Lihat `MOCK_API_SPEC.md` untuk detail endpoint

#### `nlp-engine` (Port 8002)
- NER pada resume medis bahasa Indonesia
- Mapping teks → kode ICD-10 / ICD-9-CM
- Confidence scoring per kode
- Input: plain text resume medis
- Output: structured JSON dengan kode + skor

#### `ml-engine` (Port 8003)
- Risk scoring per berkas klaim (0–100)
- Model: XGBoost + Random Forest ensemble
- SHAP values untuk explainability
- Input: fitur klaim terstruktur
- Output: risk score + feature contribution

#### `auth-service` (Port 8004)
- JWT issuance & validation
- User management (verifikator, admin RS, admin BPJS)
- Role-based access control (RBAC)

---

## 3. Struktur Direktori Project

```
pramana-ai/
├── .claude/                    # Konteks untuk Claude Code
│   ├── SKILL.md
│   ├── SPEC.md
│   ├── ENV.md
│   ├── TASK.md
│   └── MOCK_API_SPEC.md
│
├── services/
│   ├── api-gateway/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   ├── middleware/
│   │   │   └── schemas/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── mock-vclaim/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── sep.py
│   │   │   │   ├── peserta.py
│   │   │   │   ├── referensi.py
│   │   │   │   ├── rujukan.py
│   │   │   │   └── rencana_kontrol.py
│   │   │   ├── auth/
│   │   │   │   └── signature.py     # HMAC-SHA256 validator
│   │   │   ├── data/
│   │   │   │   ├── icd10.json       # Master kode ICD-10
│   │   │   │   ├── icd9.json        # Master kode ICD-9-CM
│   │   │   │   ├── faskes.json      # Data faskes dummy
│   │   │   │   └── peserta.json     # Data peserta dummy
│   │   │   └── schemas/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── nlp-engine/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── pipeline/
│   │   │   │   ├── ner.py           # Named Entity Recognition
│   │   │   │   ├── icd_mapper.py    # Text → ICD code
│   │   │   │   └── confidence.py    # Scoring logic
│   │   │   └── models/              # Saved model files (gitignored)
│   │   ├── notebooks/               # Eksperimen & training
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── ml-engine/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── features/
│   │   │   │   ├── extractor.py     # Feature engineering
│   │   │   │   └── preprocessor.py
│   │   │   ├── models/
│   │   │   │   ├── risk_scorer.py   # Ensemble inference
│   │   │   │   └── explainer.py     # SHAP wrapper
│   │   │   └── saved_models/        # Serialized models (gitignored)
│   │   ├── notebooks/               # Training experiments
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── auth-service/
│       ├── app/
│       │   ├── main.py
│       │   ├── routers/
│       │   └── models/
│       ├── Dockerfile
│       └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        # Triage overview
│   │   │   ├── ClaimDetail.tsx      # Detail klaim + risk score
│   │   │   └── Login.tsx
│   │   ├── components/
│   │   │   ├── ClaimTable.tsx
│   │   │   ├── RiskBadge.tsx
│   │   │   └── ShapChart.tsx
│   │   └── lib/
│   ├── package.json
│   └── Dockerfile
│
├── database/
│   ├── migrations/                  # Alembic migration files
│   └── seeds/                       # Data dummy untuk development
│
├── shared/
│   ├── schemas/                     # Pydantic schemas shared antar service
│   └── constants/                   # INA-CBGs tariff, ICD version, dll
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/                    # Data klaim sintetis untuk testing
│
├── docker-compose.yml               # Full stack untuk development
├── docker-compose.prod.yml          # Production config
└── Makefile                         # Shortcut commands
```

---

## 4. Schema Database

### Tabel Utama

```sql
-- Tabel klaim yang masuk dari RS
CREATE TABLE claims (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    no_sep          VARCHAR(20) UNIQUE NOT NULL,
    rs_id           UUID REFERENCES hospitals(id),
    
    -- Data pasien (di-hash, bukan plaintext)
    noka_hash       VARCHAR(64) NOT NULL,  -- SHA-256 dari nomor kartu
    
    -- Data klinis
    diagnosa_utama  VARCHAR(10),           -- Kode ICD-10
    diagnosa_sekunder VARCHAR(10)[],       -- Array kode ICD-10
    prosedur        VARCHAR(10)[],         -- Array kode ICD-9-CM
    los             INTEGER,               -- Length of Stay (hari)
    
    -- Data finansial
    total_tagihan   NUMERIC(15, 2),
    tarif_ina_cbgs  NUMERIC(15, 2),
    
    -- Data waktu
    tgl_masuk       DATE,
    tgl_pulang      DATE,
    tgl_pengajuan   TIMESTAMP,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'pending',
    -- Values: pending | in_review | approved | rejected | returned
    
    -- Timestamps
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Hasil risk scoring per klaim
CREATE TABLE risk_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id        UUID REFERENCES claims(id),
    
    score           NUMERIC(5, 2),          -- 0.00 - 100.00
    risk_level      VARCHAR(10),            -- low | medium | high
    
    -- SHAP values (JSON)
    shap_values     JSONB,
    top_features    JSONB,                  -- Top 5 contributing features
    
    model_version   VARCHAR(20),
    scored_at       TIMESTAMP DEFAULT NOW()
);

-- Hasil NLP coding dari resume medis
CREATE TABLE nlp_coding_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id        UUID REFERENCES claims(id),
    
    -- Kode yang disarankan AI
    suggested_primary_icd   VARCHAR(10),
    suggested_primary_conf  NUMERIC(4, 3),  -- 0.000 - 1.000
    
    suggested_secondary     JSONB,          -- [{code, confidence}]
    suggested_procedures    JSONB,
    
    -- Apakah sama dengan yang diklaim RS?
    has_mismatch    BOOLEAN DEFAULT FALSE,
    mismatch_detail JSONB,
    
    processed_at    TIMESTAMP DEFAULT NOW()
);

-- Log audit semua tindakan verifikator
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id        UUID REFERENCES claims(id),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(50),            -- approve | reject | return | flag
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Data rumah sakit
CREATE TABLE hospitals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kode_rs         VARCHAR(20) UNIQUE NOT NULL,
    nama_rs         VARCHAR(200),
    tipe_rs         VARCHAR(5),             -- A | B | C | D
    provinsi        VARCHAR(100),
    kabupaten       VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE
);

-- User (verifikator BPJS, admin RS, admin sistem)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(200) UNIQUE NOT NULL,
    password_hash   VARCHAR(200) NOT NULL,
    role            VARCHAR(30),
    -- Values: verifikator_bpjs | admin_rs | superadmin
    hospital_id     UUID REFERENCES hospitals(id),  -- NULL jika BPJS
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 5. API Contract (Internal Services)

### NLP Engine — `/nlp/extract-coding`

**Request:**
```json
POST /nlp/extract-coding
{
  "claim_id": "uuid",
  "resume_medis": "Pasien datang dengan keluhan sesak napas progresif...",
  "context": {
    "tgl_masuk": "2024-01-15",
    "tgl_pulang": "2024-01-20"
  }
}
```

**Response:**
```json
{
  "claim_id": "uuid",
  "diagnosa_utama": {
    "kode": "I50.0",
    "deskripsi": "Congestive Heart Failure",
    "confidence": 0.92,
    "flagged": false
  },
  "diagnosa_sekunder": [
    {
      "kode": "J18.9",
      "deskripsi": "Pneumonia, tidak spesifik",
      "confidence": 0.67,
      "flagged": true,
      "flag_reason": "Confidence di bawah threshold 0.75"
    }
  ],
  "prosedur": [
    {
      "kode": "99.04",
      "deskripsi": "Transfusi Whole Blood",
      "confidence": 0.88,
      "flagged": false
    }
  ],
  "has_mismatch": false,
  "processing_time_ms": 342
}
```

### ML Engine — `/ml/score-claim`

**Request:**
```json
POST /ml/score-claim
{
  "claim_id": "uuid",
  "features": {
    "total_tagihan": 12500000,
    "los": 5,
    "diagnosa_utama": "I50.0",
    "tipe_rs": "B",
    "provinsi": "Jawa Timur",
    "bulan_pengajuan": 1,
    "tagihan_per_hari": 2500000,
    "rasio_terhadap_ina_cbgs": 1.15,
    "jumlah_diagnosa_sekunder": 2
  }
}
```

**Response:**
```json
{
  "claim_id": "uuid",
  "risk_score": 72.4,
  "risk_level": "high",
  "shap_values": {
    "rasio_terhadap_ina_cbgs": 0.28,
    "tagihan_per_hari": 0.19,
    "los": -0.05,
    "...": "..."
  },
  "top_risk_factors": [
    "Tagihan 15% di atas tarif INA-CBGs untuk diagnosa ini",
    "Tagihan per hari lebih tinggi dari RS setipe di wilayah yang sama"
  ],
  "model_version": "rf_xgb_ensemble_v1.2",
  "processing_time_ms": 28
}
```

---

## 6. Security Requirements

### Enkripsi Data
- Semua komunikasi antar service menggunakan HTTPS (mTLS di production)
- Nomor kartu peserta **wajib** di-hash SHA-256 sebelum disimpan
- Data resume medis dienkripsi AES-256 saat at-rest
- JWT token expire 8 jam, refresh token 7 hari

### Validasi Input
- Setiap endpoint wajib validasi dengan Pydantic schema
- Nomor kartu: tepat 13 digit numerik
- Kode ICD-10: format `[A-Z][0-9]{2}\.?[0-9]{0,4}`
- Tanggal: format ISO 8601 (YYYY-MM-DD)
- Request rate limit: 100 req/menit per user

### Audit Trail
- Setiap perubahan status klaim dicatat di `audit_logs`
- Log tidak bisa dihapus (append-only)
- Log disimpan minimum 5 tahun (regulasi)

---

## 7. Feature Engineering untuk ML Model

### Kelompok Fitur

```python
FEATURE_GROUPS = {
    "biaya": [
        "total_tagihan",
        "tagihan_per_hari",           # total_tagihan / los
        "tagihan_obat_ratio",         # biaya_obat / total_tagihan
        "tagihan_tindakan_ratio",     # biaya_tindakan / total_tagihan
        "rasio_terhadap_ina_cbgs",    # total_tagihan / tarif_ina_cbgs
    ],
    "klinis": [
        "los",                        # Length of Stay
        "diagnosa_utama_encoded",     # Ordinal encoding ICD chapter
        "jumlah_diagnosa_sekunder",
        "jumlah_prosedur",
        "severity_score",             # Derived dari ICD chapter
    ],
    "geografis": [
        "tipe_rs_encoded",            # A=4, B=3, C=2, D=1
        "provinsi_encoded",           # Regional cost index
        "is_regional_outlier",        # Apakah tagihan outlier di wilayahnya
    ],
    "temporal": [
        "bulan_pengajuan",
        "hari_pengajuan_dalam_bulan",
        "is_end_of_month",            # Batch submission pattern
    ],
    "komparatif": [
        "percentile_tagihan_per_diagnosa",   # vs RS setipe, diagnosa sama
        "percentile_los_per_diagnosa",
        "z_score_tagihan",                    # Zscore dalam cluster RS
    ],
    "historis_rs": [
        "rs_avg_risk_score_30d",      # Track record RS
        "rs_pending_rate_30d",        # % klaim RS yg di-pending sebelumnya
        "rs_total_claims_30d",
    ]
}

LABEL_COLUMN = "is_anomaly"           # 0 = wajar, 1 = anomali
THRESHOLD_RISK_SCORE = {
    "low":    (0, 40),
    "medium": (40, 70),
    "high":   (70, 100),
}
```

---

## 8. Model Evaluation Metrics

Menggunakan metrik yang relevan untuk imbalanced fraud detection:

```python
EVALUATION_METRICS = {
    "primary": "f1_score",           # Balance precision-recall
    "secondary": [
        "precision",                  # Hindari false positive (RS jujur kena flag)
        "recall",                     # Pastikan fraud terdeteksi
        "roc_auc",                    # Overall discriminative ability
        "average_precision",          # Area under PR curve
    ],
    "business": {
        "false_positive_rate_target": 0.10,   # Max 10% klaim normal di-flag salah
        "recall_target": 0.85,                # Min 85% anomali terdeteksi
    }
}
```

---

## 9. Konvensi Kode

### Python (Backend & ML)
- Style: Black + isort + flake8
- Type hints: **wajib** untuk semua function signature
- Docstring: Google style
- Test: pytest, minimum 70% coverage untuk critical paths

### TypeScript (Frontend)
- ESLint + Prettier
- Strict mode TypeScript
- Komponen: functional + hooks, no class components

### Git Conventions
```
feat(nlp): tambah confidence scoring untuk ICD-9
fix(ml): handle missing value pada fitur los
docs(spec): update feature engineering detail
test(mock-vclaim): tambah test untuk SEP backdate
```

### Naming Conventions
```python
# Python — snake_case
def extract_icd_from_resume(resume_text: str) -> ICDResult: ...

# Konstanta
MAX_RETRY_ATTEMPTS = 3
ICD10_PATTERN = r"[A-Z]\d{2}\.?\d{0,4}"

# Class — PascalCase
class RiskScoringPipeline: ...

# TypeScript — camelCase untuk variabel/fungsi, PascalCase untuk komponen
const riskScore = useRiskScore(claimId);
function ClaimDetailPage() { ... }
```
