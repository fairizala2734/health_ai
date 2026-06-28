from pathlib import Path


APP_TITLE = "Pertamina Health AI"
RAW_DATA_PATH = Path("data/raw/dummy_mcu_raw_for_llm.csv")
LABEL_DATA_PATH = Path("data/internal/dummy_mcu_internal_labels.csv")
DEFAULT_MODEL = "openai/gpt-oss-120b"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

RAW_HEADERS = [
    "id_karyawan",
    "nama_dummy",
    "usia",
    "jenis_kelamin",
    "unit_kerja",
    "jenis_pekerjaan",
    "tanggal_mcu",
    "tinggi_badan_cm",
    "berat_badan_kg",
    "BMI",
    "lingkar_perut_cm",
    "sistolik",
    "diastolik",
    "nadi",
    "SpO2",
    "gula_darah_puasa",
    "HbA1c",
    "kolesterol_total",
    "HDL",
    "LDL",
    "trigliserida",
    "SGOT",
    "SGPT",
    "kreatinin",
    "eGFR",
    "asam_urat",
    "status_EKG",
    "status_rontgen_thorax",
    "status_spirometri",
    "riwayat_penyakit_pribadi",
    "riwayat_penyakit_keluarga",
    "obat_rutin",
    "alergi_makanan",
    "status_merokok",
]
