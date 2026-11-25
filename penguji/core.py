"""Mesin penguji inti (dipakai bersama oleh CLI dan GUI)."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import pathlib
import re
import subprocess
import sys
import time

SOAL_TITLES: dict[int, str] = {
    1: "Kompas, Azimuth & Back Azimuth",
    2: "Logistik Tenda & Air Perkemahan",
    3: "Penerjemah Sandi Morse Internasional",
    4: "Klasemen Lomba Tingkat Penggalang",
}

TEST_CASES: dict[int, list[tuple[str, str]]] = {
    1: [
        (
            "10\n3\nKANAN 90\nKIRI 120\nKIRI 10\n",
            "Azimuth: 330 (Barat Laut)\nBack Azimuth: 150",
        ),
        (
            "0\n0\n",
            "Azimuth: 0 (Utara)\nBack Azimuth: 180",
        ),
        (
            "350\n2\nKANAN 25\nKANAN 35\n",
            "Azimuth: 50 (Timur Laut)\nBack Azimuth: 230",
        ),
        (
            "180\n1\nKANAN 720\n",
            "Azimuth: 180 (Selatan)\nBack Azimuth: 0",
        ),
        (
            "90\n2\nKANAN 45\nKANAN 90\n",
            "Azimuth: 225 (Barat Daya)\nBack Azimuth: 45",
        ),
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
        (
            "2\nZEBRA 70 80 70\nANGSA 70 80 70\n",
            "1. ANGSA - 74.00\n2. ZEBRA - 74.00",
        ),
        (
            "3\nS1 60 70 80\nS2 80 70 60\nS3 70 70 70\n",
            "1. S1 - 70.00\n2. S2 - 70.00\n3. S3 - 70.00",
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
    m = re.search(r"soal([1-4])", name)
    return int(m.group(1)) if m else None


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


def find_soal_files(directory: pathlib.Path, soal_num: int | None = None) -> list[pathlib.Path]:
    """Cari file soal1..soal4 (*.py) secara terurut berdasarkan nomor soal lalu nama file."""
    if not directory.is_dir():
        return []
    found: list[tuple[int, str, pathlib.Path]] = []
    for f in directory.glob("*.py"):
        if f.name in ("cek_jawaban.py", "cek_jawaban_gui.py"):
            continue
        num = detect_soal(f)
        if num is None:
            continue
        if soal_num is None or num == soal_num:
            found.append((num, f.name.lower(), f))
    found.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in found]


def grade_file(path: pathlib.Path, soal_num: int | None = None, timeout: float = 3.0) -> FileResult:
    resolved_soal = soal_num if soal_num is not None else detect_soal(path)
    if resolved_soal not in TEST_CASES:
        raise ValueError(
            f"Nomor soal (1-4) tidak terdeteksi dari '{path.name}'. Pilih nomor soal secara manual."
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
