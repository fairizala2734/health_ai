# Health AI Prototype

Prototype Streamlit untuk membaca data MCU dummy, membuat profil risiko awal, dan menghasilkan rekomendasi kesehatan menggunakan LLM via OpenRouter.

## Menjalankan

1. Install dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Buat file `.streamlit/secrets.toml` dari `.streamlit/secrets.example.toml`, lalu isi `OPENROUTER_API_KEY`.
   Model default yang dipakai adalah `openai/gpt-oss-120b`.

3. Jalankan aplikasi:

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
