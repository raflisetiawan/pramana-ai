# Panduan Teknis Pramana AI (Fase 1: Fondasi & Mock VClaim)
*Disusun khusus untuk mempermudah transisi dari ekosistem JavaScript (Node.js) dan PHP (Laravel) ke ekosistem Python.*

---

## 🌟 Pengantar

Fase 1 dari proyek **Pramana AI (Smart-Claim Co-Pilot)** bertujuan membangun fondasi dasar, mengatur struktur *database*, dan membangun **Mock VClaim** (server tiruan BPJS) agar aplikasi utama memiliki tempat tujuan untuk berkomunikasi.

Dokumen ini akan membedah teknis dari **Task 1.1 hingga Task 1.8** secara lebih mendalam, disertai komparasi kode agar Anda yang terbiasa dengan Node.js (Express) atau PHP (Laravel) dapat lebih cepat beradaptasi.

---

## 1. Project Bootstrap & Containerization (Task 1.1)

Langkah paling awal adalah menyiapkan ekosistem agar aplikasi dapat berjalan di mesin manapun dengan konfigurasi yang konsisten.

### Docker & Docker Compose
Di dunia PHP tradisional, Anda mungkin menggunakan XAMPP atau Laragon. Di Pramana AI, kita menggunakan **Docker**. 
Melalui file `docker-compose.yml`, kita mendefinisikan *services*:
1. **PostgreSQL**: *Database* relasional utama.
2. **Redis**: Penyimpanan *in-memory* yang sangat cepat (digunakan untuk *state management* Mock VClaim).
3. **Mock VClaim**: Server API tiruan kita.

> **Kenapa Docker?** Anda tidak perlu repot men-*download* installer PostgreSQL atau Redis. Cukup jalankan satu perintah, seluruh *server* akan menyala secara instan dan saling terhubung.

### Makefile (Perintah Singkat)
File `Makefile` berfungsi menyimpan *shortcut* perintah terminal yang sering digunakan.
- Di Node.js, Anda mengenal bagian `scripts` pada `package.json` (misal: `npm run start`).
- Di sini, alih-alih mengetik perintah *docker* yang panjang, Anda cukup menjalankan:
  - `make dev`: Menjalankan server aplikasi di mode *development*.
  - `make test`: Menjalankan seluruh pengujian otomatis (Testing).
  - `make migrate`: Menjalankan sinkronisasi struktur *database* terbaru.

---

## 2. API Gateway & Database Setup (Task 1.2)

API Gateway akan menjadi server utama Pramana AI yang kelak mengelola klaim asli dan meneruskannya ke mesin kecerdasan buatan (Machine Learning / NLP).

### Framework: FastAPI
Kita menggunakan **FastAPI**. Sesuai namanya, framework ini difokuskan pada kecepatan dan kemudahan pembuatan API.
- **Analogi JS:** Sama seperti **Express.js**, **Koa**, atau **NestJS**.
- **Analogi PHP:** Sama seperti **Lumen**, **Laravel**, atau **Slim**.

**Kelebihan utama FastAPI:**
Setiap kali Anda membuat satu rute API (misal `GET /users`), FastAPI **otomatis** membuatkan dokumentasi UI interaktif menggunakan *Swagger* di halaman `/docs`. Anda tidak perlu lagi repot menulis dokumentasi Postman!

### Validasi Data: Pydantic
Di FastAPI, untuk memvalidasi *request body* yang dikirim *client*, kita menggunakan *library* bernama **Pydantic**.
- **Analogi JS:** Seperti menggunakan **Joi**, **Zod**, atau **Yup**.
- **Analogi PHP:** Seperti **FormRequest Validation** (`$request->validate([...])`) di Laravel.

### Database ORM: SQLAlchemy Async
Untuk berinteraksi dengan database tanpa menulis sintaks SQL manual, kita menggunakan **SQLAlchemy**. Kita mengaturnya agar berjalan secara *Async* (`async/await`) sehingga performa server tidak terblokir (*non-blocking*).
- **Analogi JS:** Sangat mirip dengan **Sequelize**, **Prisma**, atau **TypeORM**.
- **Analogi PHP:** Sangat mirip dengan **Eloquent ORM** di Laravel.

### Migrasi Database: Alembic
Alembic mendampingi SQLAlchemy untuk mengelola versi perubahan tabel (migrasi).
- **Analogi JS:** `npx sequelize-cli db:migrate` atau `npx prisma migrate`.
- **Analogi PHP:** `php artisan migrate`.
Pada fase ini kita sudah men-*generate* migrasi tabel seperti `users`, `hospitals`, dan `claims`.

---

## 3. Mock VClaim & Keamanan (Task 1.3)

Agar kita bisa menguji aplikasi tanpa benar-benar menembak server BPJS (VClaim) asli yang terbatas dan ketat, kita membuat server tiruannya (Mock VClaim) menggunakan FastAPI.

### HMAC-SHA256 Signature (Middleware Keamanan)
Server BPJS menggunakan keamanan yang mengharuskan *client* mengirimkan beberapa Header (`X-cons-id`, `X-timestamp`, `X-signature`). Jika tanda tangannya (*signature*) salah, *request* ditolak.

Di sistem kita, pengecekan ini diletakkan pada **Middleware**. Middleware adalah kode yang dieksekusi di tengah-tengah (antara *Request* masuk dan eksekusi fungsi *Controller*).
- **Analogi JS:** Seperti *middleware* validasi JWT Token di Express (`app.use(authMiddleware)`).
- **Analogi PHP:** Seperti *Middleware* di Laravel (`Route::middleware('auth')`).

### Helpers Response Standard
Kita juga membuat pembungkus respons standar agar format JSON API yang keluar selalu konsisten seperti milik BPJS:
```json
{
  "metaData": { "code": "200", "message": "OK" },
  "response": { "data": "..." }
}
```

---

## 4. Endpoints Mock VClaim (Task 1.4 - 1.7)

Kita membangun puluhan rute untuk meniru BPJS. Beberapa *Controller/Router* utama yang sudah selesai:

1. **Endpoint Peserta**
   - Rute: `GET /Peserta/nokartu/{noKartu}/tglSEP/{tgl}`
   - Di sini sistem mengecek file `peserta.json`. Jika `noKartu` ada, maka status dikembalikan (Aktif / Non-aktif).

2. **Endpoint Referensi**
   - Menyimulasikan pencarian data penyakit (ICD-10) atau dokter. Data diambil murni dari file `.json` karena statis.

3. **Endpoint Surat Eligibilitas Peserta (SEP)**
   - **Rute:** `POST /SEP/2.0/insert`
   - **Proses:** Sistem akan memvalidasi apakah DPJP (Dokter Penanggung Jawab) tidak kosong, lalu men-*generate* nomor SEP unik.
   - **Redis Storage:** SEP ini harus disimpan agar bisa diakses rute lain nanti (seperti `GET /SEP/{noSep}`). Alih-alih menyimpannya di file statis atau PostgreSQL, kita menggunakan **Redis** agar penyimpanannya bersifat sementara, sangat cepat, dan mensimulasikan penyimpanan *state/session*.

4. **Mock Control (`/_mock/config`)**
   - Fitur rahasia ini tidak ada di BPJS sungguhan. Kita membuatnya agar kita bisa memerintahkan Mock VClaim: *"Sengaja perlambat respons ini sebanyak 5 detik!"* atau *"Kembalikan error 500!"*. Ini sangat berguna di masa depan untuk menguji apakah aplikasi utama kita mudah *crash* atau *resilient* (tahan banting).

---

## 5. Testing Phase 1 (Task 1.8)

Langkah profesional terakhir sebelum berpindah fase adalah menulis **Automated Tests** (Pengujian Otomatis). Kita menggunakan framework Python bernama **`pytest`**.
- **Analogi JS:** Menggunakan **Jest** atau **Mocha/Chai**.
- **Analogi PHP:** Menggunakan **PHPUnit** atau **Pest**.

Pada Fase 1 kita telah melengkapi pengujian untuk:
- **Unit Test (Fungsi Tunggal):** Memastikan fungsi pembuat *signature* matematika HMAC-SHA256 berfungsi akurat dan *expired time* (anti-replay) benar-benar menolak waktu yang usang. Memastikan file `test_signature.py` menghasilkan hasil yang diharapkan (Lolos/Gagal/Kadaluwarsa).
- **Integration Test (Skenario Lengkap):** Mensimulasikan satu alur utuh (*User Journey*) di file `test_mock_vclaim_flow.py`:
  1. Mulai dengan mencari data peserta (Budi).
  2. Cari faskes dan rujukan Budi.
  3. Lakukan pengajuan (`POST`) pembuatan SEP untuk Budi.
  4. Periksa apakah SEP tersebut berhasil disimpan dan bisa dilacak dalam fitur *Monitoring Harian*.

### Keunggulan Pytest: *Fixtures*
Dalam *testing*, Anda akan sering melihat istilah `fixture`. Fixture adalah fitur dari pytest untuk menyiapkan fungsi atau *data dummy* yang bisa disuntikkan ke berbagai tes berulang kali tanpa membuat *instance* baru, sama seperti *setup / teardown / factory* di ekosistem pengujian JS/PHP.

---

## Penutup Fase 1
Dengan berakhirnya Fase 1, kita kini memiliki "Kerangka Dasar Server" dan "Lingkungan Tiruan BPJS" yang utuh. 
Selanjutnya (di Fase 2), kita akan masuk ke wilayah utama yaitu **AI (Kecerdasan Buatan)** di mana kita membuat jalur pemrosesan data (Machine Learning Pipeline) untuk memberikan *Risk Score* (Skor Risiko) secara otomatis pada klaim-klaim yang baru dibuat.
