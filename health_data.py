from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd
import streamlit as st

from settings import LABEL_DATA_PATH, RAW_DATA_PATH, RAW_HEADERS


@dataclass(frozen=True)
class HealthProfile:
    bmi_category: str
    risk_level: str
    main_focus: str
    constraints: list[str]
    red_flags: list[str]


def clean_text(value: Any, default: str = "tidak_ada") -> str:
    if pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def clean_number(value: Any, default: float = 0) -> float:
    if pd.isna(value) or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = normalize_raw_data(pd.read_csv(RAW_DATA_PATH))
    labels = pd.read_csv(LABEL_DATA_PATH) if LABEL_DATA_PATH.exists() else pd.DataFrame()
    return raw, labels


def normalize_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for col in RAW_HEADERS:
        if col not in normalized.columns:
            normalized[col] = "tidak_ada"

    number_defaults = {
        "usia": 35,
        "tinggi_badan_cm": 170,
        "berat_badan_kg": 70,
        "BMI": 0,
        "lingkar_perut_cm": 85,
        "sistolik": 120,
        "diastolik": 80,
        "nadi": 76,
        "SpO2": 98,
        "gula_darah_puasa": 90,
        "HbA1c": 5.3,
        "kolesterol_total": 180,
        "HDL": 50,
        "LDL": 110,
        "trigliserida": 120,
        "SGOT": 25,
        "SGPT": 30,
        "kreatinin": 1.0,
        "eGFR": 100,
        "asam_urat": 5.5,
    }
    for col, default in number_defaults.items():
        normalized[col] = pd.to_numeric(normalized[col], errors="coerce").fillna(default)

    missing_bmi = normalized["BMI"].le(0)
    height_m = normalized["tinggi_badan_cm"] / 100
    normalized.loc[missing_bmi, "BMI"] = (
        normalized.loc[missing_bmi, "berat_badan_kg"] / (height_m.loc[missing_bmi] ** 2)
    ).round(1)

    for col in set(RAW_HEADERS) - set(number_defaults):
        normalized[col] = normalized[col].apply(clean_text)

    return normalized[RAW_HEADERS]


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 23:
        return "Normal"
    if bmi < 25:
        return "Overweight"
    if bmi < 30:
        return "Obesitas I"
    return "Obesitas II"


def has_history(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return bool(text and text != "tidak_ada")


def split_history(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text or text == "tidak_ada":
        return []
    return [item.strip() for item in text.split(";") if item.strip()]


def build_health_profile(row: pd.Series) -> HealthProfile:
    bmi_category = classify_bmi(float(row["BMI"]))
    histories = split_history(row.get("riwayat_penyakit_pribadi"))
    constraints: list[str] = []
    red_flags: list[str] = []

    if "hipertensi" in histories:
        constraints.append("Mulai dari intensitas ringan-sedang dan pantau tekanan darah.")
    if "diabetes" in histories or "prediabetes" in histories:
        constraints.append("Hindari pola makan ekstrem dan perhatikan waktu makan sebelum aktivitas.")
    if "penyakit_jantung" in histories:
        constraints.append("Aktivitas perlu sangat konservatif dan sebaiknya mengikuti arahan tenaga kesehatan.")
        red_flags.append("nyeri dada")
    if "penyakit_ginjal" in histories:
        constraints.append("Hindari rekomendasi protein berlebih dan pantau fungsi ginjal.")
    if "asma" in histories:
        constraints.append("Pilih aktivitas bertahap dan hindari pemicu sesak.")
        red_flags.append("sesak napas berat")
    if "cedera_lutut" in histories:
        constraints.append("Hindari lari, lompat, dan squat berat; pilih low impact.")
    if "asam_urat" in histories:
        constraints.append("Batasi makanan tinggi purin dan jaga hidrasi.")
    if "anemia" in histories:
        constraints.append("Mulai olahraga ringan dan pantau keluhan mudah lelah.")

    if int(row["sistolik"]) >= 140 or int(row["diastolik"]) >= 90:
        constraints.append("Tekanan darah tinggi, hindari peningkatan intensitas mendadak.")
    if float(row["eGFR"]) < 60:
        constraints.append("eGFR rendah, rekomendasi nutrisi perlu lebih konservatif.")
    if float(row["HbA1c"]) >= 6.5:
        constraints.append("HbA1c tinggi, prioritaskan kontrol gula darah.")
    if float(row["LDL"]) >= 160:
        constraints.append("LDL tinggi, prioritaskan pengurangan lemak jenuh dan aktivitas aerobik aman.")

    if bmi_category in {"Overweight", "Obesitas I", "Obesitas II"}:
        main_focus = "Menurunkan berat badan secara bertahap dan memperbaiki kebiasaan harian."
    elif bmi_category == "Underweight":
        main_focus = "Menaikkan berat badan secara sehat dan membangun massa otot ringan."
    else:
        main_focus = "Mempertahankan IMT normal dan meningkatkan kebugaran."

    if "penyakit_jantung" in histories or float(row["eGFR"]) < 60 or bmi_category == "Obesitas II":
        risk_level = "Tinggi"
    elif histories or bmi_category in {"Obesitas I", "Overweight"}:
        risk_level = "Sedang"
    else:
        risk_level = "Rendah"

    default_red_flags = ["pusing berat", "pingsan", "nyeri dada", "sesak berat"]
    return HealthProfile(bmi_category, risk_level, main_focus, constraints, sorted(set(red_flags + default_red_flags)))


def employee_payload(row: pd.Series) -> dict[str, Any]:
    keys = [key for key in RAW_HEADERS if key not in {"id_karyawan", "nama_dummy"}]
    return {key: row[key].item() if hasattr(row[key], "item") else row[key] for key in keys}


def row_fingerprint(row: pd.Series) -> str:
    serialized = json.dumps(employee_payload(row), ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
