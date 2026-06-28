from __future__ import annotations

import pandas as pd
import streamlit as st

from health_data import build_health_profile, has_history, load_data, row_fingerprint
from llm_client import build_prompt, call_openrouter, estimate_message_tokens, local_recommendation
from settings import APP_TITLE, DEFAULT_MODEL, RAW_HEADERS
from ui import (
    apply_styles,
    bmi_tone,
    get_secret,
    h,
    manual_input_row,
    render_chip,
    render_data_grid,
    render_list,
    render_metric_card,
    render_section_title,
    render_token_usage,
    risk_tone,
    uploaded_data,
)


DISPLAY_COLS = [
    "usia",
    "jenis_kelamin",
    "jenis_pekerjaan",
    "tinggi_badan_cm",
    "berat_badan_kg",
    "lingkar_perut_cm",
    "gula_darah_puasa",
    "HbA1c",
    "kolesterol_total",
    "LDL",
    "trigliserida",
    "eGFR",
    "asam_urat",
    "status_EKG",
    "status_spirometri",
]


def select_source_data(dummy_raw: pd.DataFrame) -> tuple[pd.DataFrame, str, str, bool]:
    render_section_title("Sumber Data", "Pilih data yang ingin dianalisis. Semua input ada di halaman utama.")
    with st.container(border=True):
        data_source = st.radio(
            "Mode input",
            ["Data dummy", "Upload CSV", "Input manual"],
            horizontal=True,
            label_visibility="collapsed",
        )

        show_internal = False
        if data_source == "Data dummy":
            raw = dummy_raw
            selector_cols = st.columns([1.1, 1.6, 0.9])
            with selector_cols[0]:
                search = st.text_input("Cari karyawan", placeholder="Contoh: EMP030")
            filtered = raw
            if search:
                needle = search.lower()
                filtered = raw[
                    raw["id_karyawan"].str.lower().str.contains(needle)
                    | raw["nama_dummy"].str.lower().str.contains(needle)
                ]
            if filtered.empty:
                st.warning("Karyawan tidak ditemukan. Menampilkan data pertama.")
                filtered = raw.iloc[[0]]
            with selector_cols[1]:
                selected_id = st.selectbox(
                    "Pilih karyawan",
                    filtered["id_karyawan"].tolist(),
                    format_func=lambda emp_id: f"{emp_id} - {raw.loc[raw['id_karyawan'] == emp_id, 'nama_dummy'].iloc[0]}",
                )
            with selector_cols[2]:
                show_internal = st.toggle("Label testing", value=False)
        elif data_source == "Upload CSV":
            upload_cols = st.columns([1.25, 1])
            with upload_cols[0]:
                uploaded = uploaded_data()
            if uploaded is None:
                raw = dummy_raw.iloc[[0]].copy()
                selected_id = raw["id_karyawan"].iloc[0]
                with upload_cols[1]:
                    st.info("Belum ada file. Sementara ditampilkan satu data dummy agar dashboard tetap terlihat.")
            else:
                raw = uploaded
                with upload_cols[1]:
                    selected_id = st.selectbox(
                        "Pilih baris/karyawan",
                        raw["id_karyawan"].tolist(),
                        format_func=lambda emp_id: f"{emp_id} - {raw.loc[raw['id_karyawan'] == emp_id, 'nama_dummy'].iloc[0]}",
                    )
        else:
            raw = manual_input_row()
            selected_id = raw["id_karyawan"].iloc[0]

    return raw, selected_id, data_source, show_internal


def render_header(model: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-title">Pertamina Health AI</div>
          <div class="hero-subtitle">
            Sistem demo untuk membaca data MCU, memahami kondisi karyawan, dan menyusun rekomendasi
            kesehatan yang personal, aman, dan mudah dijalankan.
          </div>
          <div>
            {render_chip("MCU baseline", "neutral")}
            {render_chip("AI recommendation", "success")}
            {render_chip(model, "neutral")}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_source_status(data_source: str, model: str, has_api_key: bool) -> None:
    st.markdown(
        f"""
        <div class="source-row">
          {render_chip(f"Sumber: {data_source}", "neutral")}
          {render_chip(f"Model: {model}", "neutral")}
          {render_chip("OpenRouter siap" if has_api_key else "Fallback lokal aktif", "success" if has_api_key else "warning")}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_employee_summary(row: pd.Series, profile) -> None:
    render_section_title("Ringkasan Karyawan", f"{row['id_karyawan']} - {row['nama_dummy']}")
    top_cols = st.columns(4)
    with top_cols[0]:
        render_metric_card("Kategori IMT", profile.bmi_category, f"BMI {float(row['BMI']):.1f}", bmi_tone(profile.bmi_category))
    with top_cols[1]:
        render_metric_card("Level Risiko", profile.risk_level, "Guardrail keselamatan", risk_tone(profile.risk_level))
    with top_cols[2]:
        render_metric_card("Tekanan Darah", f"{row['sistolik']}/{row['diastolik']}", "mmHg", "info")
    with top_cols[3]:
        history_label = "Ada" if has_history(row["riwayat_penyakit_pribadi"]) else "Tidak ada"
        render_metric_card("Riwayat Penyakit", history_label, str(row["riwayat_penyakit_pribadi"]), "warning" if history_label == "Ada" else "success")

    st.markdown(
        f"""
        <div class="source-row">
          {render_chip(f"IMT {profile.bmi_category}", bmi_tone(profile.bmi_category))}
          {render_chip(f"Risiko {profile.risk_level}", risk_tone(profile.risk_level))}
          {render_chip(str(row["jenis_pekerjaan"]), "neutral")}
          {render_chip(str(row["unit_kerja"]), "neutral")}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mcu_tabs(row: pd.Series, profile) -> None:
    data_tab, guardrail_tab, raw_tab = st.tabs(["MCU Utama", "Guardrail", "Data Lengkap"])
    with data_tab:
        with st.container(border=True):
            render_section_title("Data MCU Mentah", "Parameter utama yang digunakan AI untuk memahami kondisi.")
            render_data_grid(row, DISPLAY_COLS)
    with guardrail_tab:
        with st.container(border=True):
            render_section_title("Guardrail Keselamatan", "Pagar minimum, bukan jawaban final untuk AI.")
            if profile.constraints:
                for item in profile.constraints:
                    st.markdown(f'<div class="rec-item">{h(item)}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="ok-box">Tidak ada constraint khusus dari rule engine awal.</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="notice">Rekomendasi AI bersifat pendamping gaya hidup, bukan diagnosis atau pengganti dokter.</div>',
                unsafe_allow_html=True,
            )
    with raw_tab:
        st.dataframe(row[RAW_HEADERS].to_frame("nilai"), use_container_width=True, height=520)


def render_recommendation_panel(row: pd.Series, profile, model: str, api_key: str) -> None:
    messages = build_prompt(row, profile)
    render_section_title("Rekomendasi AI", "Klik tombol untuk membuat rekomendasi personal dari data yang sedang dipilih.")
    st.caption(f"Estimasi input sebelum dikirim ke OpenRouter: sekitar {estimate_message_tokens(messages)} token.")

    generate = st.button("Buat Rekomendasi", use_container_width=True)
    if generate:
        with st.spinner("Menyusun rekomendasi yang aman dan mudah dipahami..."):
            source = "local"
            token_usage = None
            try:
                if api_key:
                    recommendation, token_usage = call_openrouter(messages, model, api_key)
                    source = "openrouter"
                else:
                    recommendation = local_recommendation(row, profile)
            except Exception as exc:
                recommendation = local_recommendation(row, profile)
                st.warning(f"OpenRouter belum berhasil dipakai, jadi ditampilkan rekomendasi lokal. Detail: {exc}")

        st.session_state["recommendation"] = recommendation
        st.session_state["recommendation_source"] = source
        st.session_state["token_usage"] = token_usage

    recommendation = st.session_state.get("recommendation")
    if not recommendation:
        return

    source = st.session_state.get("recommendation_source", "local")
    if source == "openrouter":
        st.success("Rekomendasi dibuat oleh LLM via OpenRouter.")
    else:
        st.info("Rekomendasi lokal ditampilkan sebagai fallback sementara.")

    render_token_usage(st.session_state.get("token_usage"))
    if recommendation.get("segmentasi_ai"):
        st.markdown(
            f'{render_chip("Segmentasi AI", "neutral")} <span style="font-weight:750;color:#17202f;">{h(recommendation.get("segmentasi_ai"))}</span>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f"""
        <div class="rec-item" style="border-left-color:#0e7490;">
          <div class="rec-item-title">Ringkasan kondisi</div>
          <div class="rec-item-reason" style="font-size:13px;color:#334155;">{h(recommendation.get('ringkasan_kondisi', '-'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tab_overview, tab_plan, tab_safety = st.tabs(["Prioritas", "Rencana Harian", "Monitoring"])
    with tab_overview:
        render_list("Faktor Risiko Utama", recommendation.get("faktor_risiko_utama", []))
        render_list("Prioritas", recommendation.get("prioritas", []))
        render_list("Target 4 Minggu", recommendation.get("target_4_minggu", []))
    with tab_plan:
        render_list("Workout", recommendation.get("rekomendasi_workout", []))
        render_list("Makanan", recommendation.get("rekomendasi_makanan", []))
        render_list("Lifestyle", recommendation.get("rekomendasi_lifestyle", []))
        render_list("Task Harian", recommendation.get("task_harian", []))
    with tab_safety:
        render_list("Monitoring", recommendation.get("monitoring", []))
        render_list("Peringatan", recommendation.get("peringatan", []))


def reset_recommendation_if_needed(rec_key: str) -> None:
    if st.session_state.get("active_rec_key") == rec_key:
        return
    st.session_state.pop("recommendation", None)
    st.session_state.pop("recommendation_source", None)
    st.session_state.pop("token_usage", None)
    st.session_state["active_rec_key"] = rec_key


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":material/health_and_safety:", layout="wide")
    apply_styles()

    dummy_raw, labels = load_data()
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("OPENROUTER_MODEL", DEFAULT_MODEL)

    render_header(model)
    raw, selected_id, data_source, show_internal = select_source_data(dummy_raw)
    render_source_status(data_source, model, bool(api_key))

    row = raw.loc[raw["id_karyawan"] == selected_id].iloc[0]
    profile = build_health_profile(row)
    reset_recommendation_if_needed(f"{data_source}:{selected_id}:{row_fingerprint(row)}")

    render_employee_summary(row, profile)
    render_mcu_tabs(row, profile)

    if data_source == "Data dummy" and show_internal and not labels.empty:
        render_section_title("Label Internal Testing", "Hanya untuk developer, tidak dikirim ke LLM.")
        label_row = labels.loc[labels["id_karyawan"] == selected_id]
        if not label_row.empty:
            st.dataframe(label_row.T.rename(columns={label_row.index[0]: "nilai"}), use_container_width=True)

    render_recommendation_panel(row, profile, model, api_key)


if __name__ == "__main__":
    main()
