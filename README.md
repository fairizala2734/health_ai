# Health AI Prototype

Prototype Streamlit untuk membaca data MCU dummy, membuat profil risiko awal, dan menghasilkan rekomendasi kesehatan menggunakan LLM via OpenRouter.

## Menjalankan

1. Install Python 3.12.x.

   Kalau komputer belum punya Python, download dari:

   ```text
   https://www.python.org/downloads/
   ```

   Saat install di Windows, centang opsi **Add python.exe to PATH**. Setelah selesai, buka PowerShell baru lalu cek:

   ```powershell
   python --version
   ```

   Versi yang dipakai untuk project ini adalah Python `3.12.x`.

2. Masuk ke folder project:

```powershell
cd D:\Project\Noval
```

3. Buat virtual environment dan install dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Kalau di komputer ada beberapa versi Python, pakai launcher Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Setup konfigurasi `.streamlit`.

Folder `.streamlit` dipakai untuk konfigurasi Streamlit dan API key lokal. File yang boleh masuk GitHub hanya:

```text
.streamlit/config.toml
.streamlit/secrets.example.toml
```

Buat file `.streamlit/secrets.toml` dari contoh:

```powershell
New-Item -ItemType Directory -Force .streamlit
Copy-Item .streamlit\secrets.example.toml .streamlit\secrets.toml
```

Lalu isi `OPENROUTER_API_KEY` di `.streamlit/secrets.toml`:

```toml
OPENROUTER_API_KEY = "isi_api_key_openrouter_di_sini"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
```

Catatan: `.streamlit/secrets.toml` berisi API key asli, jadi jangan dipush ke GitHub. File ini sudah di-ignore lewat `.gitignore`.

5. Jalankan aplikasi:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Atau pakai runner PowerShell:

```powershell
.\tools\run_streamlit.ps1
```

Background lewat PowerShell:

```powershell
.\tools\start_streamlit_background.ps1
```

Stop server:

```powershell
.\tools\stop_streamlit.ps1
```

Data mentah untuk LLM ada di `data/raw`, sedangkan label internal/testing ada di `data/internal`.

## Struktur Utama

- `app.py`: orkestrasi halaman Streamlit.
- `settings.py`: konstanta aplikasi, path data, dan daftar kolom MCU.
- `health_data.py`: normalisasi data MCU, klasifikasi IMT, profil risiko awal.
- `llm_client.py`: prompt LLM, estimasi token, request OpenRouter, fallback lokal.
- `ui.py`: komponen UI, input manual/upload, styling, dan tampilan token.
- `data/raw`: data dummy mentah yang dikirim ke LLM.
- `data/internal`: label testing internal yang tidak dikirim ke LLM.
