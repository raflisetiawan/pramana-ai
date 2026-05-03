# TASK.md — Rencana Pelaksanaan MVP (8 Minggu)

> **Prinsip:** Bangun secara vertikal (end-to-end per fitur), bukan horizontal (semua layer sekaligus).  
> Setiap fase menghasilkan sesuatu yang **bisa didemonstrasikan** dan **diuji**.

---

## Status Legenda
```
[ ] = Belum dikerjakan
[~] = Sedang dikerjakan
[x] = Selesai
[!] = Blocked / ada masalah
```

---

## Phase 1 — Fondasi & Mock VClaim API (Minggu 1–2)

**Tujuan:** Di akhir fase ini, tim bisa mensimulasikan seluruh alur pengajuan SEP dari SIMRS ke Mock VClaim, dan data tersimpan di database lokal.

---

### Minggu 1 — Project Setup & Mock VClaim

#### 1.1 Project Bootstrap
- [x] **1.1.1** Buat struktur direktori sesuai `SPEC.md` (bagian 3)
- [x] **1.1.2** Setup `docker-compose.yml` dengan service: `postgres`, `redis`, `mock-vclaim`
- [x] **1.1.3** Buat `.env.example` sesuai `ENV.md`
- [x] **1.1.4** Setup `Makefile` dengan shortcut: `make dev`, `make test`, `make migrate`
- [x] **1.1.5** Inisialisasi repo git, buat `.gitignore` sesuai `ENV.md` bagian 6

#### 1.2 Database Setup
- [x] **1.2.1** Setup FastAPI project di `services/api-gateway/`
- [x] **1.2.2** Konfigurasi SQLAlchemy async + Alembic
- [x] **1.2.3** Buat semua tabel sesuai schema di `SPEC.md` bagian 4:
  - [x] `hospitals`
  - [x] `users`
  - [x] `claims`
  - [x] `risk_scores`
  - [x] `nlp_coding_results`
  - [x] `audit_logs`
- [x] **1.2.4** Buat migrasi Alembic pertama (`initial_schema`)
- [x] **1.2.5** Buat seed data: 3 RS dummy, 5 user dummy (admin, verifikator), 10 klaim dummy

#### 1.3 Mock VClaim — Setup & Auth
- [ ] **1.3.1** Buat FastAPI project di `services/mock-vclaim/`
- [ ] **1.3.2** Implementasi HMAC-SHA256 signature validator (middleware)
  - Input: `X-cons-id`, `X-timestamp`, `X-signature` header
  - Validasi: signature cocok + timestamp tidak lebih dari 5 menit lalu (anti-replay)
- [ ] **1.3.3** Buat response envelope helper:
  ```python
  def ok_response(data): return {"metaData": {"code": "200", "message": "OK"}, "response": data}
  def error_response(code, msg): return {"metaData": {"code": code, "message": msg}, "response": None}
  ```
- [ ] **1.3.4** Load data dummy dari JSON files:
  - `peserta.json` (4 peserta dari `MOCK_API_SPEC.md` bagian 10)
  - `icd10.json` (minimal 15 kode dari `MOCK_API_SPEC.md` bagian 10)
  - `icd9.json` (minimal 10 kode prosedur)
  - `faskes.json` (5 faskes dummy)
  - `dokter.json` (5 dokter dummy)

---

### Minggu 2 — Mock VClaim Endpoint & Integrasi Awal

#### 1.4 Mock VClaim — Endpoint Peserta & Referensi
- [ ] **1.4.1** `GET /Peserta/nokartu/{noKartu}/tglSEP/{tgl}` dengan semua skenario:
  - Peserta aktif
  - Peserta non-aktif
  - Tidak ditemukan
- [ ] **1.4.2** `GET /referensi/diagnosa/{keyword}` — search by keyword
- [ ] **1.4.3** `GET /referensi/dokter/pelayanan/{kdPoli}/tglPelayanan/{tgl}/Spesialis/{kdSpes}`
- [ ] **1.4.4** `GET /referensi/poli/{keyword}`
- [ ] **1.4.5** `GET /referensi/faskes/{tipe}/{keyword}`
- [ ] **1.4.6** `GET /referensi/procedure/{keyword}`

#### 1.5 Mock VClaim — Endpoint SEP
- [ ] **1.5.1** `POST /SEP/2.0/insert` dengan validasi:
  - DPJP tidak boleh kosong
  - Tanggal SEP tidak boleh lebih dari hari ini
  - Tanggal rujukan tidak boleh lebih dari tgl SEP
  - Backdate > 1 hari harus pengajuan dulu
  - Simpan SEP ke Redis (state management)
- [ ] **1.5.2** `GET /SEP/{noSep}` — ambil SEP by nomor
- [ ] **1.5.3** `PUT /SEP/2.0/update` — update SEP (validasi: belum FPK)
- [ ] **1.5.4** `DELETE /SEP/2.0/delete` — hapus SEP (validasi: belum dirujuk)

#### 1.6 Mock VClaim — Endpoint Rujukan & Kontrol
- [ ] **1.6.1** `GET /Rujukan/Peserta/{noKartu}` — cari rujukan aktif by nomor kartu
- [ ] **1.6.2** `GET /Rujukan/{noRujukan}` — get rujukan by nomor
- [ ] **1.6.3** `POST /Rujukan/2.0/insert` — buat rujukan antar RS
- [ ] **1.6.4** `POST /RencanaKontrol/insert` — buat surat kontrol
- [ ] **1.6.5** `POST /RencanaKontrol/InsertSPRI` — buat SPRI
- [ ] **1.6.6** `GET /Monitoring/Kunjungan/Tanggal/{tgl}/JnsPelayanan/{jnsPel}` — monitoring harian

#### 1.7 Mock VClaim — Mock Control Endpoints
- [ ] **1.7.1** `POST /_mock/config` — set error rate, delay, force error on noka tertentu
- [ ] **1.7.2** `GET /_mock/status` — lihat konfigurasi saat ini
- [ ] **1.7.3** `POST /_mock/reset` — reset ke default

#### 1.8 Testing Phase 1
- [ ] **1.8.1** Unit test: signature validator (benar / salah / expired)
- [ ] **1.8.2** Unit test: semua endpoint peserta (5 skenario)
- [ ] **1.8.3** Integration test: alur lengkap cari peserta → cari rujukan → buat SEP → cek monitoring
- [ ] **1.8.4** Pastikan Swagger UI (`/docs`) berjalan dan semua endpoint terdokumentasi

**✅ Deliverable Phase 1:** Mock VClaim berjalan, seluruh alur pembuatan SEP bisa disimulasikan, data tersimpan.

---

## Phase 2 — ML Engine: Risk Scoring (Minggu 3–4)

**Tujuan:** Setiap klaim yang masuk mendapat risk score 0–100 secara otomatis, dengan penjelasan fitur mana yang berkontribusi.

---

### Minggu 3 — Data Pipeline & Feature Engineering

#### 2.1 Data Sintetis untuk Training
- [ ] **2.1.1** Buat script generator data sintetis klaim BPJS:
  - Target: 10.000 sampel (80% "wajar", 20% "anomali")
  - Fitur yang di-generate sesuai `SPEC.md` bagian 7 (`FEATURE_GROUPS`)
  - Simpan ke `tests/fixtures/synthetic_claims.csv`
- [ ] **2.1.2** Definisi rule untuk labeling anomali (gunakan untuk generate):
  - `rasio_terhadap_ina_cbgs > 1.5` → anomali
  - `tagihan_per_hari > percentile_95` untuk diagnosa yang sama → anomali
  - `los < 1` untuk diagnosa berat (CHF, AMI) → anomali
  - kombinasi diagnosa + prosedur yang tidak lazim → anomali

#### 2.2 Feature Engineering Pipeline
- [ ] **2.2.1** Buat `services/ml-engine/app/features/extractor.py`:
  - Fungsi `extract_features(claim: dict) -> pd.DataFrame`
  - Handle missing values (median imputation untuk numerik, mode untuk kategori)
  - Encoding: ordinal untuk `tipe_rs`, target encoding untuk `diagnosa_utama`
- [ ] **2.2.2** Buat `services/ml-engine/app/features/preprocessor.py`:
  - `StandardScaler` untuk fitur numerik
  - Simpan scaler yang sudah fit ke file (untuk digunakan saat inferensi)
- [ ] **2.2.3** Notebook eksplorasi di `services/ml-engine/notebooks/01_eda.ipynb`:
  - Distribusi setiap fitur
  - Korelasi fitur dengan label
  - Class imbalance analysis

### Minggu 4 — Model Training & API

#### 2.3 Model Training
- [ ] **2.3.1** Notebook training di `services/ml-engine/notebooks/02_training.ipynb`:
  - Baseline: Random Forest
  - Main model: XGBoost
  - Ensemble: weighted average RF + XGBoost
- [ ] **2.3.2** Cross-validation 5-fold, catat metrik sesuai `SPEC.md` bagian 8
- [ ] **2.3.3** Threshold tuning: cari threshold yang memenuhi `false_positive_rate < 0.10`
- [ ] **2.3.4** SHAP analysis: feature importance global + contoh individual
- [ ] **2.3.5** Simpan model ke `saved_models/ensemble_v1.pkl`
- [ ] **2.3.6** Log experiment ke MLflow

#### 2.4 ML Engine API
- [ ] **2.4.1** Buat FastAPI project di `services/ml-engine/`
- [ ] **2.4.2** Load model saat startup (singleton, lazy load)
- [ ] **2.4.3** `POST /ml/score-claim` — sesuai contract di `SPEC.md` bagian 5
  - Extract features dari input
  - Run inference
  - Hitung SHAP values
  - Return risk score + top 5 contributing features
- [ ] **2.4.4** `GET /ml/health` — health check + model version
- [ ] **2.4.5** `GET /ml/model-info` — info model yang sedang dipakai
- [ ] **2.4.6** Integrasi ke API Gateway: setelah klaim masuk, otomatis panggil ML Engine

#### 2.5 Testing Phase 2
- [ ] **2.5.1** Unit test: feature extractor (termasuk edge case missing values)
- [ ] **2.5.2** Unit test: API endpoint scoring dengan klaim dummy
- [ ] **2.5.3** Performance test: single prediction < 100ms, batch 100 klaim < 5 detik

**✅ Deliverable Phase 2:** Setiap klaim yang masuk otomatis mendapat risk score + penjelasan. Dashboard bisa menampilkan badge Hijau/Merah.

---

## Phase 3 — NLP Engine: ICD Coding (Minggu 5–6)

**Tujuan:** Resume medis teks → saran kode ICD-10 + ICD-9 otomatis dengan confidence score.

---

### Minggu 5 — NLP Pipeline Dasar

#### 3.1 Setup Model NLP
- [ ] **3.1.1** Download base model IndoBERT:
  ```bash
  # Di dalam service nlp-engine
  python -c "from transformers import AutoTokenizer, AutoModel; \
    AutoTokenizer.from_pretrained('indobenchmark/indobert-base-p1', cache_dir='./app/models'); \
    AutoModel.from_pretrained('indobenchmark/indobert-base-p1', cache_dir='./app/models')"
  ```
- [ ] **3.1.2** Setup spaCy untuk Indonesian:
  ```bash
  python -m spacy download xx_ent_wiki_sm  # Multilingual model sebagai base
  ```
- [ ] **3.1.3** Buat `services/nlp-engine/app/pipeline/ner.py`:
  - Input: resume medis (plain text)
  - Output: list entitas (`DIAGNOSA`, `PROSEDUR`, `OBAT`, `DURASI`)
  - Gunakan rule-based NER dulu (regex + keyword matching) sebelum model

#### 3.2 ICD Mapper dengan Fuzzy Search
- [ ] **3.2.1** Load ICD-10 dan ICD-9 master data ke memory saat startup
- [ ] **3.2.2** Buat `services/nlp-engine/app/pipeline/icd_mapper.py`:
  - Input: nama diagnosa (string)
  - Output: list kandidat `[{kode, nama, score}]`
  - Gunakan `rapidfuzz` untuk fuzzy matching nama diagnosa
  - Kombinasikan dengan embedding similarity (IndoBERT) untuk re-ranking
- [ ] **3.2.3** Buat mapping manual untuk diagnosa Indonesia yang umum:
  ```python
  COMMON_MAPPINGS = {
    "gagal jantung": "I50.0",
    "hipertensi": "I10",
    "diabetes melitus tipe 2": "E11.9",
    "pneumonia": "J18.9",
    "gagal ginjal kronis": "N18.5",
    "serangan jantung": "I21.9",
    # dst...
  }
  ```

### Minggu 6 — NLP Engine API & Audit

#### 3.3 Confidence Scoring
- [ ] **3.3.1** Buat `services/nlp-engine/app/pipeline/confidence.py`:
  - Skor berdasarkan: fuzzy match score + embedding similarity + frekuensi kode di training data
  - Normalisasi ke range 0.0–1.0
  - Flag otomatis jika confidence < `NLP_CONFIDENCE_THRESHOLD` (default 0.75)

#### 3.4 NLP Engine API
- [ ] **3.4.1** Buat FastAPI project di `services/nlp-engine/`
- [ ] **3.4.2** `POST /nlp/extract-coding` — sesuai contract di `SPEC.md` bagian 5
  - Input: resume medis teks + context (tanggal, dll)
  - Output: kode ICD-10 utama + sekunder + prosedur + confidence + flag
- [ ] **3.4.3** `POST /nlp/audit-consistency` — audit kode yang sudah ada:
  - Input: resume medis + kode yang diklaim RS
  - Output: apakah kode sesuai dengan resume? mismatch detail?
- [ ] **3.4.4** `GET /nlp/health`
- [ ] **3.4.5** Integrasi ke API Gateway: setelah klaim masuk, otomatis panggil NLP Engine

#### 3.5 Testing Phase 3
- [ ] **3.5.1** Buat 10 resume medis sintetis (fiktif) sebagai test fixtures
- [ ] **3.5.2** Unit test: ICD mapper dengan berbagai ejaan (typo, singkatan)
- [ ] **3.5.3** Unit test: confidence scorer
- [ ] **3.5.4** Integration test: resume medis → kode ICD lengkap
- [ ] **3.5.5** Performance test: single extraction < 2 detik (CPU-only)

**✅ Deliverable Phase 3:** Resume medis bisa dianalisis otomatis. Klaim dengan mismatch antara resume dan kode yang diajukan RS akan di-flag.

---

## Phase 4 — Dashboard & Integrasi End-to-End (Minggu 7–8)

**Tujuan:** Verifikator BPJS bisa login, melihat daftar klaim terfilter by risk, dan melihat detail analisis AI per klaim.

---

### Minggu 7 — Frontend Dashboard

#### 4.1 Auth Flow
- [ ] **4.1.1** Setup React + TypeScript + Vite di `frontend/`
- [ ] **4.1.2** Halaman Login — form + panggil `POST /api/v1/auth/login`
- [ ] **4.1.3** JWT storage di memory (bukan localStorage) + auto-refresh
- [ ] **4.1.4** Protected routes — redirect ke login jika tidak ada token

#### 4.2 Dashboard Triage (Halaman Utama)
- [ ] **4.2.1** Komponen `ClaimTable` dengan kolom:
  - No SEP, Nama Pasien (disamarkan), RS, Diagnosa, Total Tagihan, Risk Score, Status
- [ ] **4.2.2** Filter bar: by risk level (Hijau/Kuning/Merah), by RS, by tanggal
- [ ] **4.2.3** Komponen `RiskBadge` — badge berwarna berdasarkan risk level
- [ ] **4.2.4** Sorting by risk score (default: descending)
- [ ] **4.2.5** Statistik ringkas di header: total klaim, % per risk level

#### 4.3 Halaman Detail Klaim
- [ ] **4.3.1** `ClaimDetailPage` — layout dua kolom: info klaim (kiri) + analisis AI (kanan)
- [ ] **4.3.2** Panel "Saran Koding NLP": tampilkan kode yang disarankan AI vs yang diklaim RS, highlight mismatch
- [ ] **4.3.3** Panel "Risk Score": tampilkan skor + bar chart SHAP values (top 5 faktor)
- [ ] **4.3.4** Panel "Aksi Verifikator": tombol Setujui / Kembalikan / Eskalasi + form catatan
- [ ] **4.3.5** History aksi klaim (dari `audit_logs`)

### Minggu 8 — API Gateway, Integrasi, & Pilot Simulation

#### 4.4 API Gateway Lengkap
- [ ] **4.4.1** Auth endpoints:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
- [ ] **4.4.2** Claim endpoints:
  - `GET /api/v1/claims` — list dengan filter (risk, rs, tgl, status) + pagination
  - `GET /api/v1/claims/{id}` — detail klaim lengkap (termasuk risk score + NLP result)
  - `POST /api/v1/claims/{id}/approve` — setujui klaim
  - `POST /api/v1/claims/{id}/return` — kembalikan ke RS + catatan
  - `POST /api/v1/claims/{id}/escalate` — eskalasi ke supervisor
- [ ] **4.4.3** Stats endpoint: `GET /api/v1/stats/dashboard` — angka untuk header dashboard
- [ ] **4.4.4** VClaim proxy: `POST /api/v1/vclaim/sep/create` — buat SEP via Mock VClaim

#### 4.5 End-to-End Integration Test
- [ ] **4.5.1** Test skenario lengkap (gunakan pytest):
  ```
  1. Login sebagai admin RS
  2. Cari peserta by nomor kartu → Mock VClaim
  3. Buat SEP baru → Mock VClaim
  4. Klaim otomatis masuk ke database
  5. NLP Engine analisis resume medis
  6. ML Engine hitung risk score
  7. Login sebagai verifikator BPJS
  8. Lihat klaim di dashboard (terurut by risk)
  9. Lihat detail klaim dengan analisis AI
  10. Setujui klaim → status berubah di database
  ```
- [ ] **4.5.2** Test dengan 3 skenario klaim:
  - Klaim normal (Hijau) — CHF straightforward
  - Klaim medium risk (Kuning) — tagihan sedikit tinggi
  - Klaim high risk (Merah) — tanda-tanda upcoding

#### 4.6 Pilot Simulation RS Tipe B
- [ ] **4.6.1** Generate 100 klaim sintetis untuk satu bulan operasional RS fiktif
- [ ] **4.6.2** Jalankan seluruh pipeline pada 100 klaim tersebut
- [ ] **4.6.3** Hitung metrik pilot:
  - % klaim Hijau (harusnya > 50%)
  - % klaim Merah (harusnya < 30%)
  - Waktu processing rata-rata per klaim
  - Jumlah false positive (klaim normal yang ter-flag Merah)
- [ ] **4.6.4** Buat laporan pilot 1 halaman (untuk Demo Day)

**✅ Deliverable Phase 4:** Sistem berjalan end-to-end. Verifikator bisa login, melihat triage dashboard, dan memproses klaim dengan bantuan AI.

---

## OUT OF SCOPE untuk MVP ini

Hal-hal berikut **tidak dikerjakan** dalam 8 minggu ini, untuk fokus ke core value:

```
❌ Graph Neural Networks (GNN) untuk deteksi fraud ring
   → Butuh data relasional yang cukup besar, dikerjakan setelah pilot
   
❌ Koneksi ke VClaim BPJS production
   → Butuh akses resmi (Trustmark, UAT, Consumer ID production)
   
❌ Deployment ke lebih dari 1 RS
   → Multi-tenancy dikerjakan setelah MVP stabil
   
❌ Mobile app
   
❌ Modul pelatihan / fine-tuning model secara online (active learning)
   
❌ Laporan analytics lengkap / BI dashboard
   
❌ Integrasi email/notifikasi
   
❌ Export laporan ke Excel/PDF
```

---

## Prioritas Jika Waktu Tidak Cukup

Jika ada keterlambatan, berikut urutan fitur yang boleh dipotong atau disederhanakan (dari yang paling rendah prioritasnya):

1. **Potong dulu:** Perpanjangan Rujukan Khusus di Mock VClaim (section 1.6.5+)
2. **Sederhanakan:** Dashboard cukup tabel + badge, tanpa SHAP chart (bisa diganti teks)
3. **Sederhanakan:** NLP Engine cukup rule-based (tanpa IndoBERT embedding), asal akurasi > 70%
4. **Tunda:** MLflow tracking (log ke CSV saja dulu)
5. **Jangan potong:** Mock VClaim core (SEP, peserta, referensi) — ini dependency utama

---

## Definition of Done

Sebuah task dianggap **Done** jika:
- [ ] Kode berjalan tanpa error
- [ ] Ada minimal 1 unit test yang passing
- [ ] Tidak ada secret / credential yang ter-hardcode
- [ ] Endpoint (jika ada) terdokumentasi di Swagger
- [ ] Sudah di-review dan di-commit ke branch yang sesuai

---

## Cara Menggunakan File Ini

Saat mulai session Claude Code baru, sebutkan nomor task:

> "Kerjakan task 1.5.1 — implement `POST /SEP/2.0/insert` dengan semua validasi yang disebutkan."

Atau untuk multiple task:

> "Kerjakan task 1.3.2 sampai 1.3.4 — signature validator dan helper functions untuk Mock VClaim."
