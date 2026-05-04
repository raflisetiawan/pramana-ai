# Panduan Teknis Pramana AI (Fase 2: ML Engine & Risk Scoring)

*Disusun khusus untuk mempermudah transisi dari ekosistem JavaScript (Node.js) dan PHP (Laravel) ke ekosistem Python & Machine Learning.*

---

## 🌟 Pengantar

Di Fase 1, kita telah membangun fondasi server dan "Mock VClaim" (tiruan server BPJS). Sekarang di **Fase 2**, kita masuk ke inti dari kecerdasan buatan aplikasi ini: **ML Engine (Machine Learning Engine)**.

Tujuan utama dari fase ini adalah: **Menganalisis setiap klaim rumah sakit yang masuk secara otomatis, memberikan skor risiko (0-100), dan menjelaskan *kenapa* skor tersebut tinggi atau rendah (dalam bahasa manusia).**

Dokumen ini membedah teknis **Task 2.1 hingga Task 2.5**, agar Anda yang terbiasa dengan CRUD (Create, Read, Update, Delete) di Web Development bisa memahami konsep Machine Learning (Prediksi/Inference).

---

## 1. Data Sintetis & Feature Engineering (Task 2.1 & 2.2)

Machine Learning membutuhkan data masa lalu untuk "belajar". Karena data medis asli bersifat rahasia, kita membuat **Data Sintetis** (data buatan yang mirip aslinya).

### Feature Engineering (Ekstraksi Fitur)

Di web backend (Laravel/Express), Anda biasa mengambil data mentah dari *database* (misal: JSON klaim berisi `total_tagihan` dan `los` / lama rawat).
Bagi sebuah algoritma ML, angka mentah tersebut kurang bermakna tanpa konteks. **Feature Engineering** adalah proses mengubah/menambah atribut agar algoritma "lebih pintar".

Contoh di kode kita (`services/ml-engine/app/features/extractor.py`):

- **Derived Features (Fitur Turunan):** Kita membuat kolom baru seperti `tagihan_per_hari` (total_tagihan / los) dan `rasio_terhadap_ina_cbgs`.
  *Analogi:* Sama seperti membuat *Accessor/Mutator* di Eloquent Laravel, atau *computed properties* di Vue/React.
- **Handling Missing Values (Imputasi):** Jika ada form yang kosong (`null`), kita tidak membuangnya. Kita mengisinya dengan nilai median/modus masa lalu.
- **Encoding:** Algoritma ML (seperti XGBoost) hanya mengerti **angka matematis**, bukan teks (String). Jadi, teks seperti "Jawa Timur" atau tipe RS "B" harus diubah menjadi angka. Inilah tugas *Target Encoding* dan *Ordinal Encoding*.

### Preprocessor (Standard Scaler)

Angka tarif (jutaan) dan angka hari (satuan) memiliki skala yang jauh berbeda. `StandardScaler` (`app/features/preprocessor.py`) meratakan semuanya ke skala yang sama (misal antara -1 sampai 1) agar algoritma tidak "bias" pada angka yang nominalnya besar.

---

## 2. Model Training (Task 2.3)

Proses *Training* (Pelatihan) adalah fase di mana algoritma mempelajari pola dari data sintetis yang sudah kita proses. Proses ini dijalankan lewat script `train.py`.

### Pemilihan Algoritma

Kita menggunakan dua algoritma utama, dan menggabungkannya menjadi **Ensemble** (kerja tim):

1. **Random Forest:** Seperti namanya, ini adalah kumpulan "Pohon Keputusan" (*Decision Trees*) yang menebak secara acak lalu mengambil voting terbanyak. Bagus untuk menemukan pola stabil.
2. **XGBoost:** Mirip Random Forest, tapi alih-alih acak, setiap pohon baru akan belajar dari *kesalahan* pohon sebelumnya. Algoritma ini sangat akurat dan menjadi standar industri saat ini.
3. **Ensemble:** Kita mengambil rata-rata probabilitas dari Random Forest (40%) dan XGBoost (60%).
   *Analogi:* Seperti bertanya pada dua dokter spesialis yang berbeda untuk mendiagnosa satu pasien, lalu menggabungkan kesimpulan mereka.

### SHAP Analysis (Interpretability)

Kelemahan XGBoost adalah sistemnya seperti "Kotak Hitam" (*Black Box*)—kita tahu tebakannya akurat, tapi tidak tahu alasannya.
**SHAP (SHapley Additive exPlanations)** memecahkan ini. Ia menganalisis seberapa besar peran setiap fitur terhadap skor akhir. Inilah yang memungkinkan API kita mengembalikan kalimat: *"Tagihan 463% lebih tinggi tarif INA-CBGs untuk diagnosa ini"*.

### Menyimpan Model (Pickle / Joblib)

Setelah model dilatih bermenit-menit dan menemukan pola matematisnya, model itu **disimpan** menjadi *file* biner (ekstensi `.pkl`).

- *Analogi:* Sama seperti proses `npm run build` yang menghasilkan *bundle* siap produksi. *File* `.pkl` ini tinggal di-*load* ke memori saat server berjalan, sehingga API tidak perlu belajar dari nol setiap kali ada *request*.

---

## 3. ML Engine API (Task 2.4)

Sekarang kita membungkus model biner (`.pkl`) tersebut ke dalam sebuah REST API menggunakan **FastAPI**.

### Singleton Pattern & Lazy Loading

Ukuran model ML bisa sangat besar (puluhan hingga ratusan Megabyte) dan berat untuk dimuat ke RAM.
Di `risk_scorer.py`, kita menggunakan pola **Singleton**. Artinya, model hanya di-*load* **satu kali** ke dalam memori komputer saat API dihidupkan, dan *instance* yang sama dipakai berulang-ulang untuk seluruh *request* HTTP.

- *Analogi JS:* Menyimpan objek di luar fungsi *handler* Express, atau menggunakan pola Singleton class di TypeScript.
- *Analogi PHP:* Menggunakan *Service Container* Laravel dengan fungsi `singleton()`, atau memori menetap via Laravel Octane.

### Endpoint `POST /ml/score-claim`

Alur (*Pipeline*) dari endpoint ini adalah:

1. Menerima JSON dari Gateway (divalidasi oleh Pydantic).
2. JSON dioper ke `extract_features()` dan `preprocessor.transform()`.
3. Matriks angka yang sudah bersih dioper ke `EnsembleClassifier.predict_proba()` untuk mendapatkan probabilitas 0-100%.
4. Dioper ke `ClaimExplainer` (menggunakan SHAP) untuk merangkai alasan Bahasa Indonesia.
5. Dikembalikan sebagai respons HTTP JSON.

### Integrasi API Gateway (Router `ml_scoring.py`)

Di sisi API Gateway (mirip *reverse proxy* / *router* utama), kita menambahkan logika: Setiap ada pengguna (RS) yang *submit* klaim ke `POST /api/v1/claims/submit`, Gateway akan secara **async** menembak (melakukan request HTTP internal) ke ML Engine secara tersembunyi.
Sehingga di mata RS, mereka hanya *submit*, tapi langsung mendapat laporan *"Risk Level: High"*.

---

## 4. Testing Phase 2 (Task 2.5)

Sebagai penutup, kita menulis **Automated Tests** (Pengujian Otomatis) di folder `tests/unit/test_ml_engine/` menggunakan `pytest`.

1. **Test Feature Extractor:** Memastikan fungsi matematika kita (seperti rasio, imputasi) tidak *crash* jika diberi data kosong (`null`) atau salah tipe data.
2. **Test API Scoring:** Memastikan endpoint HTTP merespons dengan struktur JSON yang benar (ada `claim_id`, `risk_score`, `risk_level`, dan `top_risk_factors`). Kita membuat simulasi klaim wajar dan klaim nakal untuk membuktikan modelnya bekerja secara akurat.
3. **Performance Test:** Model ML sangat berat secara CPU. Pengujian ini memastikan spesifikasi `SPEC.md` kita tercapai: satu prediksi butuh waktu di bawah 100 milidetik, sehingga *user* di frontend tidak merasa aplikasinya "lemot" (lambat).

---

## Penutup Fase 2

Dengan selesainya fase ini, Pramana AI sudah sah memiliki "Otak".
Arsitektur kita kini memiliki:

1. **API Gateway:** Satpam dan penghubung utama.
2. **Mock VClaim:** Simulasi BPJS.
3. **ML Engine:** Otak untuk menilai kewajaran finansial sebuah klaim.

Langkah selanjutnya (Fase 3), kita akan membangun "Otak" kedua yaitu **NLP Engine**, yang difokuskan khusus untuk menganalisis dan membaca dokumen **Teks Medis** untuk rekomendasi kode ICD.
