from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests

from health_data import HealthProfile, employee_payload, split_history
from settings import APP_TITLE, OPENROUTER_URL


@dataclass(frozen=True)
class TokenUsage:
    estimated_input_tokens: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


def estimate_tokens_from_text(text: str) -> int:
    # Estimasi praktis lintas model: bahasa Indonesia biasanya sekitar 3-4 karakter per token.
    return max(1, round(len(text) / 3.6))


def estimate_message_tokens(messages: list[dict[str, str]]) -> int:
    text = "\n".join(f"{message.get('role', '')}: {message.get('content', '')}" for message in messages)
    return estimate_tokens_from_text(text)


def build_prompt(row: pd.Series, profile: HealthProfile) -> list[dict[str, str]]:
    payload = employee_payload(row)
    system = """
Anda adalah asisten rekomendasi kesehatan karyawan perusahaan.
Tugas Anda: pahami sendiri data MCU mentah, identifikasi pola risiko yang paling masuk akal, lalu buat rekomendasi gaya hidup yang personal, aman, praktis, dan mudah dipahami orang awam.
Jangan menyalin template generik. Bedakan rekomendasi antar karyawan berdasarkan IMT, tekanan darah, gula, lipid, fungsi ginjal/hati, asam urat, EKG/spirometri, riwayat, obat, pekerjaan, dan kebiasaan merokok.
Jangan memberi diagnosis final, jangan mengganti dokter, jangan menyarankan diet ekstrem, obat, suplemen dosis, atau aktivitas berbahaya.
Gunakan guardrail keselamatan hanya sebagai pagar minimum, bukan sebagai jawaban segmentasi. Jika data menunjukkan risiko tinggi, sarankan konsultasi tenaga kesehatan.
Jawab hanya JSON valid tanpa markdown.
""".strip()
    user = {
        "data_mcu_mentah": payload,
        "instruksi_analisis": [
            "Tentukan sendiri kategori IMT, faktor risiko utama, faktor pendukung, dan batasan aktivitas dari data.",
            "Jika dua karyawan berbeda kondisi, rekomendasinya harus berbeda secara nyata.",
            "Buat task yang realistis untuk karyawan perusahaan, bukan atlet.",
            "Jelaskan alasan rekomendasi dalam bahasa awam.",
        ],
        "guardrail_keselamatan": {
            "catatan": "Guardrail ini dibuat otomatis untuk mencegah saran berisiko. Jangan anggap ini sebagai label kasus final.",
            "larangan_minimum": profile.constraints,
            "red_flags": profile.red_flags,
        },
        "format_output": {
            "segmentasi_ai": "segmentasi kondisi menurut analisis Anda",
            "ringkasan_kondisi": "2-4 kalimat sederhana",
            "faktor_risiko_utama": ["faktor paling penting dari data"],
            "prioritas": ["maksimal 4 prioritas yang spesifik"],
            "target_4_minggu": ["target realistis dan terukur"],
            "rekomendasi_workout": ["jenis, durasi, frekuensi, intensitas, dan alasan"],
            "rekomendasi_makanan": ["saran makan praktis yang sesuai kondisi"],
            "rekomendasi_lifestyle": ["tidur, rokok, hidrasi, kebiasaan kerja bila relevan"],
            "task_harian": [
                {
                    "nama": "task singkat",
                    "durasi": "contoh 20 menit / sepanjang hari",
                    "level": "ringan/sedang",
                    "alasan": "kenapa task ini cocok untuk data karyawan",
                }
            ],
            "monitoring": ["apa yang dicek harian/mingguan"],
            "peringatan": ["kapan harus berhenti dan konsultasi"],
        },
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def call_openrouter(messages: list[dict[str, str]], model: str, api_key: str) -> tuple[dict[str, Any], TokenUsage]:
    estimated = estimate_message_tokens(messages)
    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": APP_TITLE,
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage") or {}
    return json.loads(content), TokenUsage(
        estimated_input_tokens=estimated,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )


def local_recommendation(row: pd.Series, profile: HealthProfile) -> dict[str, Any]:
    histories = split_history(row.get("riwayat_penyakit_pribadi"))
    workout = "Jalan kaki santai 20 menit, 4 kali per minggu."
    if profile.bmi_category in {"Obesitas I", "Obesitas II"}:
        workout = "Jalan kaki low impact 15-25 menit, 4 kali per minggu, naikkan durasi perlahan."
    if "cedera_lutut" in histories:
        workout = "Sepeda statis ringan atau jalan datar 15-20 menit; hindari lari dan lompat."
    if "asma" in histories:
        workout = "Jalan santai bertahap 10-20 menit, pemanasan lebih lama, hindari pemicu sesak."
    if "penyakit_jantung" in histories:
        workout = "Aktivitas ringan saja dan ikuti arahan tenaga kesehatan sebelum menaikkan intensitas."

    nutrition = [
        "Gunakan pola piring seimbang: sayur, protein, karbohidrat secukupnya.",
        "Kurangi minuman manis, gorengan, dan camilan tinggi kalori.",
        "Pilih protein rendah lemak dan tambah serat dari sayur/buah.",
    ]
    if "diabetes" in histories or "prediabetes" in histories:
        nutrition.append("Sebarkan asupan karbohidrat lebih merata dan hindari gula sederhana.")
    if "hipertensi" in histories:
        nutrition.append("Batasi makanan tinggi garam dan makanan olahan.")
    if "asam_urat" in histories:
        nutrition.append("Batasi makanan tinggi purin dan cukup minum air.")

    return {
        "ringkasan_kondisi": (
            f"IMT karyawan masuk kategori {profile.bmi_category} dengan risiko {profile.risk_level.lower()}. "
            f"Fokus awal adalah {profile.main_focus.lower()}"
        ),
        "prioritas": [
            profile.main_focus,
            "Membangun kebiasaan yang mudah dilakukan setiap hari.",
            "Memantau gejala dan progres secara berkala.",
        ],
        "target_4_minggu": [
            "Konsisten menyelesaikan minimal 70% task harian.",
            "Melakukan aktivitas fisik ringan-sedang minimal 4 kali per minggu.",
            "Melakukan check-in berat badan dan keluhan setiap minggu.",
        ],
        "rekomendasi_workout": [workout],
        "rekomendasi_makanan": nutrition,
        "rekomendasi_lifestyle": ["Tidur cukup, batasi rokok bila ada, dan kurangi duduk terlalu lama."],
        "task_harian": [
            {"nama": "Aktivitas fisik sesuai rekomendasi", "durasi": "15-25 menit", "level": "ringan"},
            {"nama": "Minum air cukup", "durasi": "sepanjang hari", "level": "ringan"},
            {"nama": "Hindari minuman manis hari ini", "durasi": "sepanjang hari", "level": "ringan"},
        ],
        "monitoring": [
            "Harian: task selesai/tidak, energi, dan keluhan.",
            "Mingguan: berat badan, lingkar perut, dan tekanan darah bila tersedia.",
        ],
        "peringatan": [f"Hentikan aktivitas dan hubungi tenaga kesehatan jika muncul {flag}." for flag in profile.red_flags],
    }
