"""Mesin penguji inti — Bank 16 Soal (4 Paket Simulasi × 4 Soal = 80 Kasus Uji)."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import pathlib
import re
import subprocess
import sys
import time

PAKET_INFO: dict[int, tuple[str, list[int]]] = {
    1: ("Paket 1 — Dasar & Teknik Kepramukaan Inti", [1, 2, 3, 4]),
    2: ("Paket 2 — Sandi, Menaksir, Peta & Logistik", [5, 6, 7, 8]),
    3: ("Paket 3 — Semboyan, Sandi Lanjutan & Penilaian", [9, 10, 11, 12]),
    4: ("Paket 4 — Berpikir Komputasional & Simulasi Final", [13, 14, 15, 16]),
}

SOAL_TITLES: dict[int, str] = {
    1: "Kompas, Azimuth & Back Azimuth",
    2: "Logistik Tenda & Air Perkemahan",
    3: "Penerjemah Sandi Morse Internasional",
    4: "Klasemen Lomba Tingkat Penggalang",
    5: "Penerjemah Sandi AN & Sandi AZ",
    6: "Menaksir Tinggi Pohon (Metode Bayangan)",
    7: "Peta Perjalanan & Estimasi Waktu Tiba Pos",
    8: "Inventaris & Kekurangan Peralatan Regu",
    9: "Penerjemah Sandi Angka Pramuka",
    10: "Sandi Geser (Caesar) Multi-Baris",
    11: "Penjadwalan Piket & Jaga Malam Perkemahan",
    12: "Rekap Juara Umum (Penalti & Diskualifikasi)",
    13: "Simulasi Tali Pionering (Potongan & Sisa)",
    14: "Jejak Langkah Penjelajahan (Koordinat & Jarak)",
    15: "Penerjemah Posisi Bendera Semaphore Resmi",
    16: "Optimasi Isi Ransel Perkemahan (Greedy)",
}

TEST_CASES: dict[int, list[tuple[str, str]]] = {
    # === PAKET 1 ===
    1: [
        ("10\n3\nKANAN 90\nKIRI 120\nKIRI 10\n", "Azimuth: 330 (Barat Laut)\nBack Azimuth: 150"),
        ("0\n0\n", "Azimuth: 0 (Utara)\nBack Azimuth: 180"),
        ("350\n2\nKANAN 25\nKANAN 35\n", "Azimuth: 50 (Timur Laut)\nBack Azimuth: 230"),
        ("180\n1\nKANAN 720\n", "Azimuth: 180 (Selatan)\nBack Azimuth: 0"),
        ("90\n2\nKANAN 45\nKANAN 90\n", "Azimuth: 225 (Barat Daya)\nBack Azimuth: 45"),
    ],
    2: [
        ("17 6 3 100\n", "Tenda: 3\nAir: 127.50 L\nStatus: KURANG 27.50 L"),
        ("12 6 2 60\n", "Tenda: 2\nAir: 60.00 L\nStatus: CUKUP"),
        ("1 5 1 10.5\n", "Tenda: 1\nAir: 2.50 L\nStatus: CUKUP"),
        ("25 4 4 200.25\n", "Tenda: 7\nAir: 250.00 L\nStatus: KURANG 49.75 L"),
        ("8 8 1 20\n", "Tenda: 1\nAir: 20.00 L\nStatus: CUKUP"),
    ],
    3: [
        (".--. .-. .- -- ..- -.- .- / .----\n", "PRAMUKA 1"),
        ("... --- ...\n", "SOS"),
        ("... .- - -.-- .- / -.. .- .-. -- .-\n", "SATYA DARMA"),
        (".-.. - / .....\n", "LT 5"),
        (".- ...... -...\n", "A?B"),
    ],
    4: [
        (
            "4\nGARUDA 80 90 80\nELANG 85 80 95\nRAJAWALI 80 90 80\nKANCIL 90 90 90\n",
            "1. KANCIL - 90.00\n2. ELANG - 86.00\n3. GARUDA - 84.00\n4. RAJAWALI - 84.00",
        ),
        (
            "3\nBIMA 80 90 80\nARJUNA 90 75 90\nCITRA 80 90 80\n",
            "1. BIMA - 84.00\n2. CITRA - 84.00\n3. ARJUNA - 84.00",
        ),
        ("1\nMELATI 100 100 100\n", "1. MELATI - 100.00"),
        ("2\nZEBRA 70 80 70\nANGSA 70 80 70\n", "1. ANGSA - 74.00\n2. ZEBRA - 74.00"),
        ("3\nS1 60 70 80\nS2 80 70 60\nS3 70 70 70\n", "1. S1 - 70.00\n2. S2 - 70.00\n3. S3 - 70.00"),
    ],
    # === PAKET 2 ===
    5: [
        ("AZ\nKIZNFPZ 2026!\n", "PRAMUKA 2026!"),
        ("AN\nCENZHXN\n", "PRAMUKA"),
        ("AN\nRegu Elang #1\n", "Erth Rynat #1"),
        ("AZ\nHello, Scout!\n", "Svool, Hxlfg!"),
        ("AN\nNOPQRSTUVWXYZ\n", "ABCDEFGHIJKLM"),
    ],
    6: [
        ("1.6 0.8 6.0\n", "Tinggi: 12.00 m\nKategori: SEDANG"),
        ("1.5 1.5 4.2\n", "Tinggi: 4.20 m\nKategori: RENDAH"),
        ("2.0 0.5 4.5\n", "Tinggi: 18.00 m\nKategori: TINGGI"),
        ("1.6 0 5.0\n", "TIDAK VALID"),
        ("1.5 1.0 10.0\n", "Tinggi: 15.00 m\nKategori: SEDANG"),
    ],
    7: [
        ("07:30\n2\n1500 50 10\n1000 40 5\n", "Jarak: 2.50 km\nDurasi: 70 menit\nTiba: 08:40"),
        ("23:20\n1\n2000 40 10\n", "Jarak: 2.00 km\nDurasi: 60 menit\nTiba: 00:20"),
        ("08:00\n3\n500 60 0\n750 60 5\n250 50 0\n", "Jarak: 1.50 km\nDurasi: 32 menit\nTiba: 08:32"),
        ("12:00\n0\n", "Jarak: 0.00 km\nDurasi: 0 menit\nTiba: 12:00"),
        ("06:15\n2\n3200 80 15\n1800 60 10\n", "Jarak: 5.00 km\nDurasi: 95 menit\nTiba: 07:50"),
    ],
    8: [
        (
            "3\nTALI 10\nTONGKAT 8\nKOMPAS 2\n4\nTALI 4\nTONGKAT 8\nTALI 3\nKOMPAS 1\n",
            "KOMPAS: KURANG 1\nTALI: KURANG 3",
        ),
        ("2\nTENDA 2\nMATRAS 6\n2\nTENDA 3\nMATRAS 6\n", "SEMUA LENGKAP"),
        ("3\nP3K 2\nSENTER 4\nPELUIT 3\n0\n", "P3K: KURANG 2\nPELUIT: KURANG 3\nSENTER: KURANG 4"),
        ("2\nTALI 5\nTALI 5\n2\nTALI 6\nTENDA 2\n", "TALI: KURANG 4"),
        ("1\nSEMAPHORE 4\n3\nSEMAPHORE 1\nSEMAPHORE 2\nSEMAPHORE 1\n", "SEMUA LENGKAP"),
    ],
    # === PAKET 3 ===
    9: [
        ("16-18-1-13-21-11-1 0 19-9-1-16\n", "PRAMUKA SIAP"),
        ("5 12 1 14 7\n", "ELANG"),
        ("19-1-20-25-1 0 4-1-18-13-1\n", "SATYA DARMA"),
        ("1 27 26 99\n", "A?Z?"),
        ("20-18-9 0 19-1-20-25-1\n", "TRI SATYA"),
    ],
    10: [
        ("ENKRIPSI\n3\n2\nPramuka Siap!\nRegu Elang 1\n", "Sudpxnd Vlds!\nUhjx Hodqj 1"),
        ("DEKRIPSI\n3\n1\nSudpxnd Vlds!\n", "Pramuka Siap!"),
        ("ENKRIPSI\n29\n1\nXYZ xyz\n", "ABC abc"),
        ("DEKRIPSI\n5\n1\nABC\n", "VWX"),
        ("ENKRIPSI\n0\n2\nDasa Darma\n2026\n", "Dasa Darma\n2026"),
    ],
    11: [
        (
            "22:00\n90\n3\nBudi\nSiti\nAndi\n4\n",
            "Shift 1: 22:00-23:30 - Budi\nShift 2: 23:30-01:00 - Siti\nShift 3: 01:00-02:30 - Andi\nShift 4: 02:30-04:00 - Budi",
        ),
        (
            "23:30\n60\n2\nRina\nDito\n3\n",
            "Shift 1: 23:30-00:30 - Rina\nShift 2: 00:30-01:30 - Dito\nShift 3: 01:30-02:30 - Rina",
        ),
        ("00:00\n45\n1\nFajar\n2\n", "Shift 1: 00:00-00:45 - Fajar\nShift 2: 00:45-01:30 - Fajar"),
        (
            "20:15\n120\n2\nAyu\nBagas\n2\n",
            "Shift 1: 20:15-22:15 - Ayu\nShift 2: 22:15-00:15 - Bagas",
        ),
        (
            "21:00\n30\n4\nA\nB\nC\nD\n5\n",
            "Shift 1: 21:00-21:30 - A\nShift 2: 21:30-22:00 - B\nShift 3: 22:00-22:30 - C\nShift 4: 22:30-23:00 - D\nShift 5: 23:00-23:30 - A",
        ),
    ],
    12: [
        (
            "4\nELANG 80 80 90 90 4 TIDAK\nGARUDA 85 85 80 80 1 TIDAK\nRAJAWALI 90 90 90 90 0 YA\nKANCIL 84 80 86 82 2 TIDAK\n",
            "1. ELANG - 83.00\n2. KANCIL - 82.00\n3. GARUDA - 82.00\nDISKUALIFIKASI: RAJAWALI",
        ),
        (
            "3\nBIMA 80 80 90 70 0 TIDAK\nARJUNA 80 80 80 80 0 TIDAK\nCITRA 80 80 90 70 0 TIDAK\n",
            "1. BIMA - 80.00\n2. CITRA - 80.00\n3. ARJUNA - 80.00",
        ),
        ("2\nM1 10 10 10 10 40 TIDAK\nM2 90 90 90 90 0 TIDAK\n", "1. M2 - 90.00\n2. M1 - 0.00"),
        ("2\nZ 80 80 80 80 0 YA\nA 90 90 90 90 0 YA\n", "DISKUALIFIKASI: A\nDISKUALIFIKASI: Z"),
        ("1\nMAWAR 95 90 85 90 0 TIDAK\n", "1. MAWAR - 90.00"),
    ],
    # === PAKET 4 ===
    13: [
        ("3 150 8\n500 320 450\n", "Potongan: 8\nSisa Tali: 70 cm\nStatus: CUKUP"),
        ("4 200 10\n350 410 180 500\n", "Potongan: 5\nSisa Tali: 440 cm\nStatus: KURANG 5"),
        ("2 100 5\n300 200\n", "Potongan: 5\nSisa Tali: 0 cm\nStatus: CUKUP"),
        ("3 250 2\n100 200 249\n", "Potongan: 0\nSisa Tali: 549 cm\nStatus: KURANG 2"),
        ("1 75 3\n300\n", "Potongan: 4\nSisa Tali: 0 cm\nStatus: CUKUP"),
    ],
    14: [
        ("4\nU 4\nT 3\nS 1\nB 0\n", "Posisi: (3, 3)\nJarak Langkah: 6\nJarak Lurus: 4.24"),
        ("2\nT 3\nU 4\n", "Posisi: (3, 4)\nJarak Langkah: 7\nJarak Lurus: 5.00"),
        ("4\nU 5\nS 5\nT 2\nB 2\n", "Posisi: (0, 0)\nJarak Langkah: 0\nJarak Lurus: 0.00"),
        ("3\nB 6\nS 8\nU 0\n", "Posisi: (-6, -8)\nJarak Langkah: 14\nJarak Lurus: 10.00"),
        ("0\n", "Posisi: (0, 0)\nJarak Langkah: 0\nJarak Lurus: 0.00"),
    ],
    15: [
        ("2-4 2-6 0-1 1-6 3-5 1-4 0-1\n", "PRAMUKA"),
        ("7-2 1-0 3-4 3-6 0-1 / 0-4 0-1 2-6 1-6 0-1\n", "SATYA DARMA"),
        ("4-6 0-1 3-6 0-1\n", "JAYA"),
        ("5-6 5-7 6-7\n", "WXZ"),
        ("0-1 4-5 0-2 / 9-9\n", "A?B ?"),
    ],
    16: [
        (
            "10 4\nTENDA 6 95\nKOMPAS 1 90\nMAKANAN 4 85\nAIR 3 90\n",
            "Dibawa: TENDA, KOMPAS, AIR\nTotal Berat: 10 kg\nTotal Prioritas: 275",
        ),
        (
            "5 3\nB 3 80\nA 3 80\nC 2 80\n",
            "Dibawa: C, A\nTotal Berat: 5 kg\nTotal Prioritas: 160",
        ),
        (
            "3 2\nTENDA 5 100\nKOMPOR 4 90\n",
            "Dibawa: TIDAK ADA\nTotal Berat: 0 kg\nTotal Prioritas: 0",
        ),
        (
            "12 3\nP3K 2 100\nSENTER 1 80\nTALI 3 70\n",
            "Dibawa: P3K, SENTER, TALI\nTotal Berat: 6 kg\nTotal Prioritas: 250",
        ),
        (
            "7 4\nZ 4 70\nA 3 70\nB 4 70\nC 3 90\n",
            "Dibawa: C, A\nTotal Berat: 6 kg\nTotal Prioritas: 160",
        ),
    ],
}


@dataclass
class CaseResult:
    index: int
    status: str  # "LULUS", "SALAH", "ERROR", "TIMEOUT"
    elapsed_ms: int
    input_data: str
    expected: str
    actual: str = ""
    error_message: str = ""


@dataclass
class FileResult:
    path: pathlib.Path
    soal_num: int
    soal_title: str
    cases: list[CaseResult] = field(default_factory=list)
    bad_input_lines: list[int] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.status == "LULUS")

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def score(self) -> int:
        if not self.total:
            return 0
        return int((self.passed / self.total) * 25)

    @property
    def perfect(self) -> bool:
        return self.total > 0 and self.passed == self.total and not self.bad_input_lines


def detect_soal(path: pathlib.Path | str) -> int | None:
    name = pathlib.Path(path).name.lower()
    m = re.search(r"soal(\d+)", name)
    if not m:
        return None
    num = int(m.group(1))
    return num if num in TEST_CASES else None


def check_juknis_input(code: str) -> list[int]:
    """Deteksi pemanggilan input(...) yang berisi argumen (melanggar Juknis)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        bad: list[int] = []
        for idx, line in enumerate(code.splitlines(), start=1):
            part = line.split("#", 1)[0]
            for m in re.finditer(r"(?<![A-Za-z0-9_.])input\s*\(([^)]+)\)", part):
                if m.group(1).strip():
                    bad.append(idx)
        return sorted(set(bad))

    bad_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
            if node.args or node.keywords:
                bad_lines.add(node.lineno)
    return sorted(bad_lines)


def find_soal_files(
    directory: pathlib.Path,
    soal_num: int | None = None,
    paket_num: int | None = None,
) -> list[pathlib.Path]:
    """Cari file soal1..soal16 (*.py) secara terurut berdasarkan nomor soal lalu nama file."""
    if not directory.is_dir():
        return []
    allowed: set[int] | None = None
    if paket_num is not None and paket_num in PAKET_INFO:
        allowed = set(PAKET_INFO[paket_num][1])

    found: list[tuple[int, str, pathlib.Path]] = []
    for f in directory.glob("*.py"):
        if f.name in ("cek_jawaban.py", "cek_jawaban_gui.py"):
            continue
        num = detect_soal(f)
        if num is None:
            continue
        if soal_num is not None and num != soal_num:
            continue
        if allowed is not None and num not in allowed:
            continue
        found.append((num, f.name.lower(), f))
    found.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in found]


def grade_file(path: pathlib.Path, soal_num: int | None = None, timeout: float = 3.0) -> FileResult:
    resolved_soal = soal_num if soal_num is not None else detect_soal(path)
    if resolved_soal not in TEST_CASES:
        raise ValueError(
            f"Nomor soal (1-16) tidak terdeteksi dari '{path.name}'. Pilih nomor soal secara manual."
        )

    code = path.read_text(encoding="utf-8")
    bad_inputs = check_juknis_input(code)
    result = FileResult(
        path=path,
        soal_num=resolved_soal,
        soal_title=SOAL_TITLES[resolved_soal],
        bad_input_lines=bad_inputs,
    )

    for idx, (inp, expected) in enumerate(TEST_CASES[resolved_soal], start=1):
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, "-u", str(path)],
                input=inp,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
        except subprocess.TimeoutExpired:
            elapsed_ms = int(timeout * 1000)
            result.cases.append(
                CaseResult(
                    index=idx,
                    status="TIMEOUT",
                    elapsed_ms=elapsed_ms,
                    input_data=inp.rstrip("\n"),
                    expected=expected.strip(),
                    error_message=f"Program terlalu lama (melebihi {timeout:.0f} detik / kemungkinan infinite loop).",
                )
            )
            continue

        if proc.returncode != 0:
            result.cases.append(
                CaseResult(
                    index=idx,
                    status="ERROR",
                    elapsed_ms=elapsed_ms,
                    input_data=inp.rstrip("\n"),
                    expected=expected.strip(),
                    actual=proc.stdout.strip(),
                    error_message=proc.stderr.strip() or f"Exit code {proc.returncode}",
                )
            )
            continue

        actual = proc.stdout.strip()
        exp_clean = expected.strip()
        status = "LULUS" if actual == exp_clean else "SALAH"
        result.cases.append(
            CaseResult(
                index=idx,
                status=status,
                elapsed_ms=elapsed_ms,
                input_data=inp.rstrip("\n"),
                expected=exp_clean,
                actual=actual,
            )
        )

    return result
