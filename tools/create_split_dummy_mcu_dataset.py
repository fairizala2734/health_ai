from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

from create_dummy_mcu_dataset import build_rows


RAW_CSV = Path("data/raw/dummy_mcu_raw_for_llm.csv")
RAW_XLSX = Path("data/raw/dummy_mcu_raw_for_llm.xlsx")
LABEL_CSV = Path("data/internal/dummy_mcu_internal_labels.csv")
LABEL_XLSX = Path("data/internal/dummy_mcu_internal_labels.xlsx")

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

LABEL_HEADERS = [
    "id_karyawan",
    "kategori_IMT",
    "segmentasi_kasus",
    "riwayat_utama",
    "risk_level_expected",
    "constraint_expected",
    "fokus_ai_expected",
]


def infer_risk_level(row: dict[str, str | int | float]) -> str:
    segment = str(row["segmentasi_kasus"])
    personal_history = str(row["riwayat_penyakit_pribadi"])
    if "penyakit_jantung" in personal_history or "penyakit_ginjal" in personal_history:
        return "tinggi"
    if segment == "obesitas_dengan_riwayat":
        return "tinggi"
    if segment in {"overweight_dengan_riwayat", "obesitas_tanpa_riwayat"}:
        return "sedang"
    if segment.startswith("underweight") and personal_history != "tidak_ada":
        return "sedang"
    return "rendah"


def infer_constraints(row: dict[str, str | int | float]) -> str:
    history = str(row["riwayat_penyakit_pribadi"])
    constraints: list[str] = []
    if "hipertensi" in history:
        constraints.append("hindari_intensitas_tinggi_awal")
    if "diabetes" in history or "prediabetes" in history:
        constraints.append("perhatikan_gula_darah")
    if "penyakit_jantung" in history:
        constraints.append("perlu_supervisi_medis")
    if "penyakit_ginjal" in history:
        constraints.append("hindari_rekomendasi_protein_berlebih")
    if "asma" in history:
        constraints.append("hindari_trigger_asma")
    if "cedera_lutut" in history:
        constraints.append("hindari_lari_lompat_squat_berat")
    if "asam_urat" in history:
        constraints.append("batasi_purin_dan_pantau_nyeri_sendiri")
    if "anemia" in history:
        constraints.append("hindari_intensitas_tinggi_awal")
    return ";".join(constraints) if constraints else "tidak_ada"


def primary_history(row: dict[str, str | int | float]) -> str:
    history = str(row["riwayat_penyakit_pribadi"])
    if history == "tidak_ada":
        return "tidak_ada"
    return history.split(";")[0]


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def col_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def sheet_xml(rows: list[list[object]]) -> str:
    xml_rows = []
    for r_idx, row in enumerate(rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            ref = f"{col_name(c_idx)}{r_idx}"
            text = escape(str(value))
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        xml_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


def write_xlsx(path: Path, sheet_name: str, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    table = [headers] + [[row[h] for h in headers] for row in rows]
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
            "</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            "</Relationships>",
        )
        z.writestr(
            "docProps/core.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            "<dc:creator>Codex</dc:creator>"
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
            "</cp:coreProperties>",
        )
        z.writestr(
            "docProps/app.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
            "<Application>Codex</Application>"
            "</Properties>",
        )
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>",
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>",
        )
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml(table))


def main() -> None:
    source_rows = build_rows()
    raw_rows = [{h: row[h] for h in RAW_HEADERS} for row in source_rows]
    label_rows = [
        {
            "id_karyawan": row["id_karyawan"],
            "kategori_IMT": row["kategori_IMT"],
            "segmentasi_kasus": row["segmentasi_kasus"],
            "riwayat_utama": primary_history(row),
            "risk_level_expected": infer_risk_level(row),
            "constraint_expected": infer_constraints(row),
            "fokus_ai_expected": row["fokus_ai"],
        }
        for row in source_rows
    ]

    write_csv(RAW_CSV, RAW_HEADERS, raw_rows)
    write_csv(LABEL_CSV, LABEL_HEADERS, label_rows)
    write_xlsx(RAW_XLSX, "MCU_Raw_For_LLM", RAW_HEADERS, raw_rows)
    write_xlsx(LABEL_XLSX, "Internal_Labels", LABEL_HEADERS, label_rows)
    print(RAW_CSV.resolve())
    print(RAW_XLSX.resolve())
    print(LABEL_CSV.resolve())
    print(LABEL_XLSX.resolve())


if __name__ == "__main__":
    main()
