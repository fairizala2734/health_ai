from __future__ import annotations

import html
import os
from typing import Any

import pandas as pd
import streamlit as st

from health_data import normalize_raw_data
from llm_client import TokenUsage


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default) or default)


def h(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_chip(label: str, tone: str = "neutral") -> str:
    return f'<span class="chip chip-{tone}">{h(label)}</span>'


def risk_tone(risk_level: str) -> str:
    if risk_level.lower() == "tinggi":
        return "danger"
    if risk_level.lower() == "sedang":
        return "warning"
    return "success"


def bmi_tone(category: str) -> str:
    if category == "Normal":
        return "success"
    if category in {"Underweight", "Overweight"}:
        return "warning"
    return "danger"


def format_field_name(name: str) -> str:
    label = name.replace("_", " ")
    label = label.replace("cm", "(cm)").replace("kg", "(kg)")
    return label.title()


def render_metric_card(label: str, value: str, helper: str = "", tone: str = "neutral") -> None:
    st.markdown(
        f"""
        <div class="metric-card metric-{tone}">
          <div class="metric-label">{h(label)}</div>
          <div class="metric-value">{h(value)}</div>
          <div class="metric-helper">{h(helper)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_token_usage(usage: TokenUsage | None) -> None:
    if usage is None:
        st.caption("Token LLM belum tersedia karena rekomendasi belum dikirim ke OpenRouter.")
        return
    prompt = usage.prompt_tokens if usage.prompt_tokens is not None else f"estimasi {usage.estimated_input_tokens}"
    completion = usage.completion_tokens if usage.completion_tokens is not None else "-"
    total = usage.total_tokens if usage.total_tokens is not None else "-"
    cols = st.columns(3)
    with cols[0]:
        render_metric_card("Input Token", str(prompt), "prompt yang dikirim", "info")
    with cols[1]:
        render_metric_card("Output Token", str(completion), "jawaban model", "success")
    with cols[2]:
        render_metric_card("Total Token", str(total), "dari OpenRouter", "warning")
    if usage.total_tokens is None:
        st.caption("OpenRouter belum mengembalikan usage detail, jadi input token ditampilkan sebagai estimasi.")


def render_data_grid(row: pd.Series, fields: list[str]) -> None:
    for start in range(0, len(fields), 3):
        cols = st.columns(3)
        for col, field in zip(cols, fields[start : start + 3]):
            with col:
                render_metric_card(format_field_name(field), str(row[field]), "")


def render_section_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="section-title">{h(title)}</div>
        {f'<div class="section-subtitle">{h(subtitle)}</div>' if subtitle else ''}
        """,
        unsafe_allow_html=True,
    )


def render_list(title: str, items: list[Any]) -> None:
    st.markdown(f'<div class="list-title">{h(title)}</div>', unsafe_allow_html=True)
    if not items:
        st.caption("Belum ada data.")
        return
    for item in items:
        if isinstance(item, dict):
            name = item.get("nama") or item.get("task") or str(item)
            meta = " - ".join(str(item.get(key)) for key in ("durasi", "level") if item.get(key))
            reason = item.get("alasan")
            st.markdown(
                f"""
                <div class="rec-item">
                  <div class="rec-item-title">{h(name)}</div>
                  {f'<div class="rec-item-meta">{h(meta)}</div>' if meta else ''}
                  {f'<div class="rec-item-reason">{h(reason)}</div>' if reason else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f'<div class="rec-item">{h(item)}</div>', unsafe_allow_html=True)


def manual_input_row() -> pd.DataFrame:
    st.subheader("Input Data MCU")
    profile_cols = st.columns(3)
    with profile_cols[0]:
        usia = st.number_input("Usia", min_value=18, max_value=70, value=35)
        jenis_kelamin = st.selectbox("Jenis kelamin", ["L", "P"])
        jenis_pekerjaan = st.selectbox("Jenis pekerjaan", ["Kantor", "Lapangan", "Shift"])
    with profile_cols[1]:
        unit_kerja = st.text_input("Unit kerja", value="Demo Unit")
        tinggi = st.number_input("Tinggi badan (cm)", min_value=130.0, max_value=210.0, value=170.0, step=0.5)
        berat = st.number_input("Berat badan (kg)", min_value=35.0, max_value=180.0, value=75.0, step=0.5)
    with profile_cols[2]:
        lingkar = st.number_input("Lingkar perut (cm)", min_value=50.0, max_value=160.0, value=90.0, step=0.5)
        sistolik = st.number_input("Sistolik", min_value=80, max_value=220, value=125)
        diastolik = st.number_input("Diastolik", min_value=50, max_value=140, value=80)

    with st.expander("Lab utama, riwayat, dan kebiasaan", expanded=True):
        lab_cols = st.columns(3)
        with lab_cols[0]:
            gula = st.number_input("Gula darah puasa", min_value=50, max_value=350, value=95)
            hba1c = st.number_input("HbA1c (%)", min_value=3.5, max_value=14.0, value=5.5, step=0.1)
            asam_urat = st.number_input("Asam urat", min_value=2.0, max_value=14.0, value=6.0, step=0.1)
        with lab_cols[1]:
            kolesterol = st.number_input("Kolesterol total", min_value=80, max_value=400, value=190)
            hdl = st.number_input("HDL", min_value=20, max_value=120, value=50)
            ldl = st.number_input("LDL", min_value=40, max_value=300, value=120)
            trigliserida = st.number_input("Trigliserida", min_value=40, max_value=500, value=140)
        with lab_cols[2]:
            egfr = st.number_input("eGFR", min_value=10, max_value=140, value=100)
            riwayat_options = [
                "hipertensi",
                "diabetes",
                "prediabetes",
                "kolesterol_tinggi",
                "asam_urat",
                "asma",
                "penyakit_jantung",
                "penyakit_ginjal",
                "penyakit_hati",
                "cedera_lutut",
                "anemia",
            ]
            riwayat = st.multiselect("Riwayat penyakit pribadi", riwayat_options)
            keluarga = st.multiselect("Riwayat keluarga", ["hipertensi", "diabetes", "jantung", "stroke", "tidak_ada"])
            merokok = st.selectbox("Status merokok", ["tidak", "pernah", "aktif"])
    note_cols = st.columns(2)
    with note_cols[0]:
        obat = st.text_input("Obat rutin", value="tidak_ada")
    with note_cols[1]:
        alergi = st.text_input("Alergi makanan", value="tidak_ada")

    bmi = round(berat / ((tinggi / 100) ** 2), 1)
    row = {
        "id_karyawan": "MANUAL001",
        "nama_dummy": "Input Manual",
        "usia": usia,
        "jenis_kelamin": jenis_kelamin,
        "unit_kerja": unit_kerja,
        "jenis_pekerjaan": jenis_pekerjaan,
        "tanggal_mcu": "input_manual",
        "tinggi_badan_cm": tinggi,
        "berat_badan_kg": berat,
        "BMI": bmi,
        "lingkar_perut_cm": lingkar,
        "sistolik": sistolik,
        "diastolik": diastolik,
        "nadi": 76,
        "SpO2": 98,
        "gula_darah_puasa": gula,
        "HbA1c": hba1c,
        "kolesterol_total": kolesterol,
        "HDL": hdl,
        "LDL": ldl,
        "trigliserida": trigliserida,
        "SGOT": 25,
        "SGPT": 30,
        "kreatinin": 1.0,
        "eGFR": egfr,
        "asam_urat": asam_urat,
        "status_EKG": "tidak_ada",
        "status_rontgen_thorax": "tidak_ada",
        "status_spirometri": "tidak_ada",
        "riwayat_penyakit_pribadi": ";".join(riwayat) if riwayat else "tidak_ada",
        "riwayat_penyakit_keluarga": ";".join([x for x in keluarga if x != "tidak_ada"]) if keluarga and keluarga != ["tidak_ada"] else "tidak_ada",
        "obat_rutin": obat or "tidak_ada",
        "alergi_makanan": alergi or "tidak_ada",
        "status_merokok": merokok,
    }
    return normalize_raw_data(pd.DataFrame([row]))


def uploaded_data() -> pd.DataFrame | None:
    uploaded_file = st.file_uploader("Upload CSV data MCU mentah", type=["csv"])
    if uploaded_file is None:
        st.caption("Gunakan kolom seperti file dummy raw. Kolom yang belum ada akan diisi default.")
        return None
    try:
        return normalize_raw_data(pd.read_csv(uploaded_file))
    except Exception as exc:
        st.error(f"File belum bisa dibaca: {exc}")
        return None


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #142033;
            --muted: #65758b;
            --line: #d8e5ea;
            --panel: #ffffff;
            --bg: #eef6f4;
            --green: #087f6f;
            --green-soft: #e0f4ee;
            --blue: #205fa8;
            --blue-soft: #e7f1ff;
            --cyan: #0e7490;
            --cyan-soft: #e3f7fb;
            --amber: #b65f05;
            --amber-soft: #fff5e6;
            --red: #b9382f;
            --red-soft: #fff0ed;
            --violet: #6554c0;
            --violet-soft: #f1edff;
        }
        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(8, 127, 111, 0.16), transparent 26%),
                radial-gradient(circle at 88% 5%, rgba(32, 95, 168, 0.14), transparent 30%),
                linear-gradient(180deg, #fbfefd 0%, var(--bg) 54%, #f6fafc 100%);
            color: var(--ink);
        }
        .block-container { padding-top: 1.15rem; padding-bottom: 2.5rem; max-width: 1280px; }
        h1, h2, h3 { letter-spacing: 0; color: var(--ink); }
        div[data-testid="stMarkdownContainer"] p { line-height: 1.55; }
        .hero {
            background:
                linear-gradient(135deg, rgba(255,255,255,0.97) 0%, rgba(237, 249, 245, 0.97) 46%, rgba(232, 243, 255, 0.98) 100%);
            border: 1px solid rgba(196, 216, 226, 0.95);
            border-radius: 8px;
            padding: 28px 30px;
            margin-bottom: 18px;
            box-shadow: 0 18px 42px rgba(24, 50, 74, 0.11);
            position: relative;
            overflow: hidden;
        }
        .hero:before {
            content: "";
            position: absolute;
            right: 0;
            top: 0;
            width: 9px;
            height: 100%;
            background: linear-gradient(180deg, var(--green), var(--blue));
        }
        .hero-title {
            font-size: 31px;
            font-weight: 850;
            color: #0f2a3e;
            margin-bottom: 7px;
        }
        .hero-subtitle {
            color: #52657a;
            font-size: 15px;
            line-height: 1.55;
            max-width: 860px;
        }
        .section-title {
            font-size: 18px;
            font-weight: 850;
            color: #13263a;
            margin: 8px 0 4px;
        }
        .section-subtitle {
            font-size: 13px;
            color: #6d7b8d;
            margin-bottom: 12px;
        }
        .source-row {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            margin: 6px 0 12px;
        }
        .metric-card {
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
            border: 1px solid rgba(216, 229, 234, 0.98);
            border-radius: 8px;
            padding: 16px 17px;
            min-height: 116px;
            box-shadow: 0 12px 28px rgba(24, 50, 74, 0.075);
            position: relative;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .metric-card:after {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, var(--green), var(--cyan));
        }
        .metric-info:after { background: linear-gradient(180deg, var(--blue), var(--cyan)); }
        .metric-success:after { background: linear-gradient(180deg, var(--green), #23a06f); }
        .metric-warning:after { background: linear-gradient(180deg, var(--amber), #d89722); }
        .metric-danger:after { background: linear-gradient(180deg, var(--red), #d45b51); }
        .metric-label {
            color: #6b7a90;
            font-size: 12px;
            text-transform: uppercase;
            font-weight: 750;
            margin-bottom: 8px;
        }
        .metric-value {
            color: #13263a;
            font-size: 25px;
            font-weight: 850;
            line-height: 1.1;
        }
        .metric-helper {
            color: var(--muted);
            font-size: 12px;
            margin-top: 8px;
            word-break: break-word;
        }
        .chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 750;
            border: 1px solid rgba(217, 228, 238, 0.95);
            margin-right: 8px;
            margin-top: 10px;
        }
        .chip-neutral { background: #f7fafc; color: #334155; border-color: #d8e2ed; }
        .chip-success { background: var(--green-soft); color: #08685d; border-color: #addfd5; }
        .chip-warning { background: var(--amber-soft); color: var(--amber); border-color: #f3c891; }
        .chip-danger { background: var(--red-soft); color: var(--red); border-color: #f1b7ae; }
        .notice {
            background: var(--amber-soft);
            border: 1px solid #f3c891;
            border-radius: 8px;
            padding: 12px 14px;
            color: #7c2d12;
            margin: 12px 0;
        }
        .ok-box {
            background: var(--green-soft);
            border: 1px solid #addfd5;
            border-radius: 8px;
            padding: 12px 14px;
            color: #064e3b;
        }
        .list-title {
            font-size: 14px;
            font-weight: 850;
            color: #1f334b;
            margin: 12px 0 8px;
        }
        .rec-item {
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
            border: 1px solid rgba(217, 228, 238, 0.95);
            border-left: 4px solid var(--blue);
            border-radius: 8px;
            padding: 12px 13px;
            margin-bottom: 9px;
            color: #26364b;
            box-shadow: 0 8px 18px rgba(24, 50, 74, 0.055);
        }
        .rec-item-title {
            font-size: 14px;
            font-weight: 800;
            color: var(--ink);
        }
        .rec-item-meta {
            font-size: 12px;
            color: var(--cyan);
            font-weight: 750;
            margin-top: 3px;
        }
        .rec-item-reason {
            font-size: 12px;
            color: #6b7888;
            margin-top: 6px;
            line-height: 1.45;
        }
        div[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(216, 229, 234, 0.98);
            box-shadow: 0 8px 24px rgba(24, 50, 74, 0.045);
        }
        .stButton > button {
            border-radius: 8px;
            border: 1px solid #0f766e;
            background: linear-gradient(135deg, #087f6f 0%, #0e7490 100%);
            color: #ffffff;
            font-weight: 700;
            min-height: 46px;
            box-shadow: 0 12px 24px rgba(8, 127, 111, 0.24);
        }
        .stButton > button:hover {
            border-color: #075f54;
            background: linear-gradient(135deg, #076d60 0%, #0b6680 100%);
            color: #ffffff;
        }
        div[data-testid="stTabs"] button {
            font-weight: 750;
            color: #43576e;
        }
        div[data-testid="stTabs"] [aria-selected="true"] {
            color: var(--green);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }
        @media (max-width: 900px) {
            .hero-title { font-size: 25px; }
        }
        @media (max-width: 640px) {
            .metric-card { min-height: auto; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
