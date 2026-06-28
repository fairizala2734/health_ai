from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


OUT = Path("docs/struktur_data_mcu_rekomendasi_ai.xlsx")


SHEETS = {
    "Profil_Tetap": [
        ["variabel", "kategori", "tipe_data", "satuan", "contoh", "catatan"],
        ["id_karyawan", "identitas", "text", "-", "EMP001", "Primary key/ID unik karyawan."],
        ["nama_karyawan", "identitas", "text", "-", "Budi Santoso", "Data pribadi, perlu kontrol akses."],
        ["jenis_kelamin", "relatif_tetap", "kategori", "-", "Laki-laki", "Umumnya tetap untuk kebutuhan kalkulasi risiko."],
        ["tanggal_lahir", "tetap", "date", "-", "1988-05-12", "Lebih baik dari menyimpan usia statis."],
        ["usia_saat_mcu", "turunan", "integer", "tahun", "38", "Dihitung dari tanggal_lahir dan tanggal MCU."],
        ["tinggi_badan", "relatif_tetap", "number", "cm", "170", "Relatif tetap pada orang dewasa."],
        ["unit_kerja", "konteks_pekerjaan", "text", "-", "Refinery Unit", "Bisa berubah karena mutasi, tapi bukan parameter klinis."],
        ["jabatan", "konteks_pekerjaan", "text", "-", "Operator", "Berguna untuk konteks aktivitas kerja."],
        ["lokasi_kerja", "konteks_pekerjaan", "text", "-", "Balikpapan", "Berguna untuk program intervensi lokal."],
    ],
    "Monitoring_Rutin": [
        ["variabel", "kategori", "tipe_data", "satuan", "contoh", "frekuensi_saran", "catatan"],
        ["tanggal_input", "waktu", "date", "-", "2026-06-27", "setiap input", "Tanggal pencatatan rutin."],
        ["berat_badan", "mudah_berubah", "number", "kg", "82.5", "mingguan/bulanan", "Input utama untuk progres IMT."],
        ["BMI", "turunan", "number", "kg/m2", "28.5", "otomatis", "Dihitung dari berat dan tinggi badan."],
        ["lingkar_perut", "mudah_berubah", "number", "cm", "96", "bulanan", "Indikator risiko metabolik."],
        ["sistolik", "mudah_berubah", "number", "mmHg", "135", "mingguan/bulanan", "Tekanan darah sistolik."],
        ["diastolik", "mudah_berubah", "number", "mmHg", "88", "mingguan/bulanan", "Tekanan darah diastolik."],
        ["nadi", "mudah_berubah", "number", "x/menit", "78", "opsional", "Dipengaruhi aktivitas, stres, kafein, obat."],
        ["suhu", "mudah_berubah", "number", "C", "36.7", "opsional", "Lebih relevan untuk kondisi akut."],
        ["frekuensi_napas", "mudah_berubah", "number", "x/menit", "18", "opsional", "Tanda vital."],
        ["SpO2", "mudah_berubah", "number", "%", "98", "opsional", "Saturasi oksigen."],
    ],
    "MCU_Periodik": [
        ["variabel", "kelompok", "kategori_perubahan", "tipe_data", "satuan", "contoh", "catatan"],
        ["Hb", "darah_lengkap", "berubah_periodik", "number", "g/dL", "14.2", "Hemoglobin."],
        ["Hct", "darah_lengkap", "berubah_periodik", "number", "%", "43", "Hematokrit."],
        ["RBC", "darah_lengkap", "berubah_periodik", "number", "juta/uL", "4.9", "Sel darah merah."],
        ["WBC", "darah_lengkap", "berubah_periodik", "number", "ribu/uL", "7.1", "Sel darah putih."],
        ["trombosit", "darah_lengkap", "berubah_periodik", "number", "ribu/uL", "260", "Platelet."],
        ["MCV", "indeks_eritrosit", "berubah_periodik", "number", "fL", "88", "Ukuran rerata eritrosit."],
        ["MCH", "indeks_eritrosit", "berubah_periodik", "number", "pg", "29", "Hb per eritrosit."],
        ["MCHC", "indeks_eritrosit", "berubah_periodik", "number", "g/dL", "33", "Konsentrasi Hb eritrosit."],
        ["RDW", "indeks_eritrosit", "berubah_periodik", "number", "%", "13.1", "Variasi ukuran eritrosit."],
        ["neutrofil", "diferensial_leukosit", "berubah_periodik", "number", "%", "58", "Komposisi leukosit."],
        ["limfosit", "diferensial_leukosit", "berubah_periodik", "number", "%", "32", "Komposisi leukosit."],
        ["monosit", "diferensial_leukosit", "berubah_periodik", "number", "%", "6", "Komposisi leukosit."],
        ["eosinofil", "diferensial_leukosit", "berubah_periodik", "number", "%", "3", "Komposisi leukosit."],
        ["basofil", "diferensial_leukosit", "berubah_periodik", "number", "%", "1", "Komposisi leukosit."],
        ["gula_darah_puasa", "metabolik_gula", "mudah_berubah", "number", "mg/dL", "104", "Dipengaruhi puasa, pola makan, obat."],
        ["gula_darah_sewaktu", "metabolik_gula", "mudah_berubah", "number", "mg/dL", "142", "Sangat tergantung waktu makan."],
        ["HbA1c", "metabolik_gula", "berubah_periodik", "number", "%", "5.8", "Gambaran kontrol gula beberapa bulan."],
        ["kolesterol_total", "lipid", "berubah_periodik", "number", "mg/dL", "215", "Profil lipid."],
        ["HDL", "lipid", "berubah_periodik", "number", "mg/dL", "42", "Kolesterol baik."],
        ["LDL", "lipid", "berubah_periodik", "number", "mg/dL", "145", "Kolesterol aterogenik."],
        ["trigliserida", "lipid", "berubah_periodik", "number", "mg/dL", "180", "Dipengaruhi pola makan dan metabolik."],
        ["SGOT", "fungsi_hati", "berubah_periodik", "number", "U/L", "28", "AST."],
        ["SGPT", "fungsi_hati", "berubah_periodik", "number", "U/L", "35", "ALT."],
        ["ALP", "fungsi_hati", "berubah_periodik", "number", "U/L", "82", "Alkaline phosphatase."],
        ["GGT", "fungsi_hati", "berubah_periodik", "number", "U/L", "45", "Gamma GT."],
        ["bilirubin_total", "fungsi_hati", "berubah_periodik", "number", "mg/dL", "0.8", "Bilirubin total."],
        ["albumin", "fungsi_hati/nutrisi", "berubah_periodik", "number", "g/dL", "4.4", "Status protein/nutrisi dan hati."],
        ["total_protein", "fungsi_hati/nutrisi", "berubah_periodik", "number", "g/dL", "7.1", "Protein total."],
        ["ureum", "fungsi_ginjal", "berubah_periodik", "number", "mg/dL", "32", "Terkait fungsi ginjal/hidrasi/protein."],
        ["BUN", "fungsi_ginjal", "berubah_periodik", "number", "mg/dL", "15", "Berhubungan dengan ureum; tergantung format lab."],
        ["kreatinin", "fungsi_ginjal", "berubah_periodik", "number", "mg/dL", "1.0", "Fungsi ginjal/massa otot."],
        ["eGFR", "fungsi_ginjal", "berubah_periodik", "number", "mL/min/1.73m2", "92", "Estimasi filtrasi ginjal."],
        ["asam_urat", "metabolik", "mudah_berubah", "number", "mg/dL", "7.4", "Dipengaruhi makanan, ginjal, obat."],
        ["natrium", "elektrolit", "berubah_periodik", "number", "mmol/L", "140", "Elektrolit."],
        ["kalium", "elektrolit", "berubah_periodik", "number", "mmol/L", "4.2", "Elektrolit penting untuk jantung/otot."],
        ["klorida", "elektrolit", "berubah_periodik", "number", "mmol/L", "102", "Elektrolit."],
        ["kalsium", "elektrolit", "berubah_periodik", "number", "mg/dL", "9.3", "Elektrolit/mineral."],
    ],
    "Urinalisis": [
        ["variabel", "kategori_perubahan", "tipe_data", "satuan", "contoh", "catatan"],
        ["warna_urin", "mudah_berubah", "kategori/text", "-", "kuning muda", "Dipengaruhi hidrasi dan kondisi akut."],
        ["kejernihan_urin", "mudah_berubah", "kategori/text", "-", "jernih", "Bagian pemeriksaan fisik urin."],
        ["pH_urin", "mudah_berubah", "number", "-", "6.0", "Dipengaruhi diet dan kondisi metabolik."],
        ["berat_jenis_urin", "mudah_berubah", "number", "-", "1.020", "Konsentrasi urin/hidrasi."],
        ["protein_urin", "mudah_berubah", "kategori/number", "-", "negatif", "Bisa dibuat negatif/trace/+/++."],
        ["glukosa_urin", "mudah_berubah", "kategori/number", "-", "negatif", "Terkait gula darah/gangguan ginjal."],
        ["keton_urin", "mudah_berubah", "kategori/number", "-", "negatif", "Terkait puasa, diabetes, diet tertentu."],
        ["nitrit_urin", "mudah_berubah", "kategori", "-", "negatif", "Skrining infeksi saluran kemih."],
        ["leukosit_urin", "mudah_berubah", "kategori/number", "-", "negatif", "Inflamasi/infeksi."],
        ["eritrosit_urin", "mudah_berubah", "kategori/number", "-", "negatif", "Darah dalam urin."],
    ],
    "Penunjang": [
        ["variabel", "kategori_perubahan", "tipe_data", "contoh", "catatan"],
        ["hasil_EKG", "berubah_periodik", "kategori + text", "normal", "Sebaiknya simpan status ringkas dan catatan detail."],
        ["status_EKG", "berubah_periodik", "kategori", "normal/abnormal/perlu_follow_up", "Field tambahan yang disarankan."],
        ["hasil_rontgen_thorax", "berubah_periodik", "kategori + text", "normal", "Sebaiknya simpan status ringkas dan catatan radiologi."],
        ["status_rontgen_thorax", "berubah_periodik", "kategori", "normal/abnormal/perlu_follow_up", "Field tambahan yang disarankan."],
        ["hasil_spirometri", "berubah_periodik", "kategori + text", "normal", "Relevan untuk fungsi paru, terutama pekerja paparan tertentu."],
        ["status_spirometri", "berubah_periodik", "kategori", "normal/restriktif/obstruktif/perlu_follow_up", "Field tambahan yang disarankan."],
    ],
    "Riwayat_Kesehatan": [
        ["variabel", "apakah_umum_di_MCU", "tipe_data", "contoh", "kegunaan_untuk_AI"],
        ["riwayat_penyakit_pribadi", "sering_ada", "multi-select/text", "hipertensi, diabetes", "Mencegah rekomendasi yang tidak aman."],
        ["riwayat_penyakit_keluarga", "sering_ada", "multi-select/text", "diabetes keluarga", "Menilai risiko metabolik/kardiovaskular."],
        ["riwayat_operasi", "kadang_ada", "text", "appendectomy 2015", "Konteks medis tambahan."],
        ["riwayat_rawat_inap", "kadang_ada", "text", "DBD 2020", "Konteks kondisi besar sebelumnya."],
        ["obat_rutin", "sering_ada", "text", "amlodipine", "Interaksi dengan olahraga/diet dan interpretasi hasil."],
        ["alergi_obat", "sering_ada", "text", "penicillin", "Keselamatan medis."],
        ["alergi_makanan", "kadang_ada", "text", "seafood", "Personalisasi rekomendasi makanan."],
        ["status_merokok", "sering_ada", "kategori", "tidak/pernah/aktif", "Risiko paru dan kardiovaskular."],
        ["konsumsi_alkohol", "kadang_ada", "kategori", "tidak/jarang/rutin", "Relevan untuk hati, berat badan, lipid."],
        ["aktivitas_fisik", "sering_ada", "kategori/text", "rendah/sedang/tinggi", "Menentukan level workout awal."],
        ["pola_tidur", "kadang_ada", "text/number", "6 jam/hari", "Berpengaruh pada berat badan dan metabolik."],
        ["pola_makan", "kadang_ada", "text", "sering gorengan", "Input penting untuk rekomendasi nutrisi."],
        ["keluhan_saat_ini", "sering_ada", "text", "mudah lelah", "Konteks klinis saat MCU."],
        ["cedera_atau_batasan_olahraga", "jarang_tapi_disarankan", "text", "nyeri lutut", "Sangat penting agar workout aman."],
        ["shift_kerja", "jarang_tapi_disarankan", "kategori", "non-shift/shift malam", "Relevan untuk tidur, makan, dan aktivitas."],
    ],
    "Kamus_Kategori": [
        ["kategori", "arti", "contoh_variabel"],
        ["tetap", "Tidak berubah secara alami setelah dicatat.", "tanggal_lahir"],
        ["relatif_tetap", "Jarang berubah pada orang dewasa.", "tinggi_badan, jenis_kelamin"],
        ["mudah_berubah", "Bisa berubah harian/mingguan/bulanan.", "berat_badan, tekanan darah, gula sewaktu"],
        ["berubah_periodik", "Berubah, tapi lazimnya diperiksa saat MCU/lab periodik.", "HbA1c, lipid, fungsi hati, fungsi ginjal"],
        ["turunan", "Sebaiknya dihitung sistem, bukan diinput manual.", "usia_saat_mcu, BMI"],
        ["konteks_pekerjaan", "Bukan parameter klinis, tapi memengaruhi rekomendasi.", "unit_kerja, shift_kerja"],
    ],
}


def col_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def sheet_xml(rows: list[list[str]]) -> str:
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
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        '</worksheet>'
    )


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sheet_names = list(SHEETS)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for i in range(1, len(sheet_names) + 1)
            )
            + "</Types>",
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
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            "<dc:creator>Codex</dc:creator>"
            "<cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
            "</cp:coreProperties>",
        )
        z.writestr(
            "docProps/app.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            "<Application>Codex</Application>"
            "</Properties>",
        )
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<sheets>"
            + "".join(
                f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
                for i, name in enumerate(sheet_names, start=1)
            )
            + "</sheets></workbook>",
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(
                f'<Relationship Id="rId{i}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{i}.xml"/>'
                for i in range(1, len(sheet_names) + 1)
            )
            + "</Relationships>",
        )
        for i, name in enumerate(sheet_names, start=1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(SHEETS[name]))


if __name__ == "__main__":
    build()
    print(OUT.resolve())
