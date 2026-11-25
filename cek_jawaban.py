#!/usr/bin/env python3
"""Penguji Otomatis Offline (CLI) — Lomba Coding Python Pramuka Penggalang.

Pemakaian:
  python3 cek_jawaban.py latihan/soal1_ELANG.py
  python3 cek_jawaban.py 1
  python3 cek_jawaban.py --soal 3 jawaban_morse.py
  python3 cek_jawaban.py all
  python3 cek_jawaban.py kunci_jawaban/
"""

from __future__ import annotations

import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent
LATIHAN_DIR = ROOT_DIR / "latihan"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from penguji.core import (  # noqa: E402
    PAKET_INFO,
    TEST_CASES,
    CaseResult,
    FileResult,
    find_soal_files,
    grade_file,
)


class Style:
    def __init__(self, enabled: bool) -> None:
        self.on = enabled

    def _w(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.on else text

    def bold(self, t: str) -> str:
        return self._w("1", t)

    def dim(self, t: str) -> str:
        return self._w("2", t)

    def green(self, t: str) -> str:
        return self._w("1;32", t)

    def red(self, t: str) -> str:
        return self._w("1;31", t)

    def yellow(self, t: str) -> str:
        return self._w("1;33", t)

    def cyan(self, t: str) -> str:
        return self._w("1;36", t)

    def blue(self, t: str) -> str:
        return self._w("1;34", t)


def progress_bar(score: int, max_score: int, width: int = 20) -> str:
    ratio = (score / max_score) if max_score else 0.0
    filled = round(ratio * width)
    return "█" * filled + "░" * (width - filled)


def format_multiline(label: str, text: str, s: Style, is_empty_hint: bool = False) -> None:
    if not text and is_empty_hint:
        print(f"      {s.dim(label + ':')} {s.dim('(kosong — belum mencetak output)')}")
        return
    lines = text.splitlines() or [""]
    if len(lines) == 1:
        print(f"      {s.dim(label + ':')} {lines[0]}")
    else:
        print(f"      {s.dim(label + ':')}")
        for ln in lines:
            print(f"        │ {ln}")


def print_file_result(res: FileResult, s: Style, show_diff: bool = True) -> None:
    line = "─" * 62
    print(s.dim(f"┌{line}┐"))
    header = f" Soal {res.soal_num}: {res.soal_title} "
    print(f"{s.dim('│')} {s.cyan(header)}")
    print(f"{s.dim('│')} File : {s.bold(res.path.name)}  {s.dim('(' + str(res.path.parent) + ')')}")
    print(s.dim(f"└{line}┘"))

    if res.bad_input_lines:
        baris = ", ".join(str(b) for b in res.bad_input_lines)
        print(s.yellow(f"  ⚠ PERINGATAN JUKNIS: Ada teks di dalam input() pada baris {baris}!"))
        print(s.dim("    Sesuai Juknis, tulis input() kosong tanpa teks di dalam kurung."))

    all_empty = all(c.status == "SALAH" and c.actual == "" for c in res.cases)

    for c in res.cases:
        _print_case_row(c, s, compact_empty=all_empty, show_diff=show_diff)

    if all_empty:
        print(s.dim("  ℹ Semua output masih kosong (file belum diisi kode jawaban)."))

    bar = progress_bar(res.score, 25, width=15)
    skor_txt = f"{res.score:>2}/25"
    if res.perfect:
        badge = s.green("SEMPURNA (100%)")
        skor_colored = s.green(skor_txt)
    elif res.score > 0:
        badge = s.yellow("SEBAGIAN LULUS")
        skor_colored = s.yellow(skor_txt)
    else:
        badge = s.red("BELUM LULUS")
        skor_colored = s.red(skor_txt)

    print(f"  Skor Soal {res.soal_num} : [{bar}] {skor_colored}  ({res.passed}/{res.total} uji) · {badge}\n")


def _print_case_row(c: CaseResult, s: Style, compact_empty: bool, show_diff: bool) -> None:
    waktu = s.dim(f"({c.elapsed_ms:>3} ms)")
    if c.status == "LULUS":
        print(f"  {s.green('✓')} Uji #{c.index}  {s.green('LULUS  ')}  {waktu}")
        return
    if c.status == "TIMEOUT":
        print(f"  {s.yellow('⏱')} Uji #{c.index}  {s.yellow('TIMEOUT')}  {waktu}")
        print(f"      {s.yellow(c.error_message)}")
        return
    if c.status == "ERROR":
        print(f"  {s.red('!')} Uji #{c.index}  {s.red('ERROR  ')}  {waktu}")
        last_lines = c.error_message.splitlines()[-4:]
        for ln in last_lines:
            print(f"      {s.red(ln)}")
        return

    print(f"  {s.red('✗')} Uji #{c.index}  {s.red('SALAH  ')}  {waktu}")
    if show_diff and not compact_empty:
        format_multiline("Output Siswa ", c.actual, s, is_empty_hint=True)
        format_multiline("Kunci Jawaban", c.expected, s)


def pad_styled(styled: str, plain: str, width: int) -> str:
    return styled + (" " * max(0, width - len(plain)))


def print_summary(results: list[FileResult], label: str, s: Style) -> None:
    total_score = sum(r.score for r in results)
    max_score = len(results) * 25
    bar = progress_bar(total_score, max_score, width=20)

    print(s.bold(f"═══ REKAP NILAI · {label} ═══"))
    print(s.dim(f"  {'File':<24} {'Soal':<6} {'Uji':<7} {'Skor':<8} {'Juknis':<8} Status"))
    print(s.dim("  " + "─" * 62))
    for r in results:
        juknis_raw = "OK" if not r.bad_input_lines else "CEK"
        juknis_styled = s.green(juknis_raw) if not r.bad_input_lines else s.yellow(juknis_raw)
        skor_raw = f"{r.score:>2}/25"
        if r.perfect:
            st = s.green("✓ LULUS")
            sk_styled = s.green(skor_raw)
        elif r.score > 0:
            st = s.yellow("◐ PARSIAL")
            sk_styled = s.yellow(skor_raw)
        else:
            st = s.red("✗ BELUM")
            sk_styled = s.red(skor_raw)
        uji_raw = f"{r.passed}/{r.total}"
        print(
            f"  {r.path.name:<24} #{r.soal_num:<5} {uji_raw:<7} "
            f"{pad_styled(sk_styled, skor_raw, 8)} {pad_styled(juknis_styled, juknis_raw, 8)} {st}"
        )
    print(s.dim("  " + "─" * 62))

    if total_score == max_score and all(r.perfect for r in results):
        total_fmt = s.green(f"{total_score}/{max_score} · SEMPURNA!")
    elif total_score >= max_score * 0.6:
        total_fmt = s.yellow(f"{total_score}/{max_score} · CUKUP BAIK")
    else:
        total_fmt = s.red(f"{total_score}/{max_score} · PERLU LATIHAN")

    print(f"  {s.bold('TOTAL SKOR')} : [{bar}] {total_fmt}\n")


def resolve_file(arg: str) -> pathlib.Path | None:
    p = pathlib.Path(arg)
    if p.is_file():
        return p.resolve()
    for folder in (LATIHAN_DIR, ROOT_DIR):
        cand = folder / arg
        if cand.is_file():
            return cand.resolve()
    return None


def show_help(s: Style) -> None:
    print(s.bold("Penguji Lomba Coding Python — Bank 16 Soal Pramuka Penggalang (4 Paket)"))
    print("Pemakaian singkat:")
    print(f"  {s.cyan('cek soal1_ELANG.py')}     Uji 1 file jawaban (deteksi nomor soal 1–16 otomatis)")
    print(f"  {s.cyan('cek 1')} .. {s.cyan('cek 16')}        Uji cepat soal nomor 1–16 di folder ini / latihan")
    print(f"  {s.cyan('cek 15 jawaban.py')}      Uji file dengan nomor soal manual (1–16)")
    print(f"  {s.cyan('cek paket1')} .. {s.cyan('paket4')}   Uji 1 paket simulasi (4 soal = skor /100)")
    print(f"  {s.cyan('cek all')} / {s.cyan('cekall')}       Uji semua soal (1–16) di folder ini / latihan")
    print(f"  {s.cyan('cek folder_tim/')}        Uji semua soal milik 1 tim + tabel rekap nilai")
    print(f"  {s.cyan('cekgui')}                 Buka aplikasi penguji grafis (GUI Desktop)")


def main() -> None:
    raw_args = sys.argv[1:]
    use_color = sys.stdout.isatty()
    soal_override: int | None = None
    args: list[str] = []

    i = 0
    while i < len(raw_args):
        a = raw_args[i]
        if a == "--no-color":
            use_color = False
            i += 1
        elif a == "--color":
            use_color = True
            i += 1
        elif a == "--soal" and i + 1 < len(raw_args):
            soal_override = int(raw_args[i + 1])
            i += 2
        else:
            args.append(a)
            i += 1

    s = Style(use_color)

    if not args or args[0] in ("-h", "--help", "help"):
        show_help(s)
        sys.exit(0)

    # Mode: cek paket1 .. paket4 [folder]
    if args[0].lower() in ("paket1", "paket2", "paket3", "paket4"):
        p_num = int(args[0][-1])
        p_title = PAKET_INFO[p_num][0]
        target_dir = pathlib.Path(args[1]).resolve() if len(args) >= 2 else pathlib.Path.cwd()
        files = find_soal_files(target_dir, paket_num=p_num)
        label = f"{p_title} ({target_dir})"
        if not files and len(args) == 1:
            files = find_soal_files(LATIHAN_DIR, paket_num=p_num)
            label = f"{p_title} ({LATIHAN_DIR})"
        if not files:
            print(s.red(f"[ERROR] Tidak ditemukan file untuk {p_title}."))
            sys.exit(1)
        results = [grade_file(f) for f in files]
        for r in results:
            print_file_result(r, s)
        print_summary(results, label, s)
        sys.exit(0 if all(r.perfect for r in results) else 1)

    # Mode: cek all / semua
    if args[0].lower() in ("all", "semua"):
        cwd = pathlib.Path.cwd()
        files = find_soal_files(cwd)
        label = str(cwd)
        if not files:
            files = find_soal_files(LATIHAN_DIR)
            label = str(LATIHAN_DIR)
        if not files:
            print(s.red("[ERROR] Tidak ditemukan file soal1..soal16 (*.py)."))
            sys.exit(1)
        results = [grade_file(f) for f in files]
        for r in results:
            print_file_result(r, s)
        print_summary(results, label, s)
        sys.exit(0 if all(r.perfect for r in results) else 1)

    # Mode: cek <folder>
    p0 = pathlib.Path(args[0])
    if p0.is_dir():
        files = find_soal_files(p0.resolve())
        if not files:
            print(s.red(f"[ERROR] Tidak ada file soal1..soal16 (*.py) di {p0}"))
            sys.exit(1)
        results = [grade_file(f) for f in files]
        for r in results:
            print_file_result(r, s)
        print_summary(results, str(p0.resolve()), s)
        sys.exit(0 if all(r.perfect for r in results) else 1)

    # Mode: cek <1..16> [file]
    if args[0].isdigit() and int(args[0]) in TEST_CASES and soal_override is None:
        soal_num = int(args[0])
        if len(args) >= 2:
            target = resolve_file(args[1])
            if not target:
                print(s.red(f"[ERROR] File tidak ditemukan: {args[1]}"))
                sys.exit(1)
            res = grade_file(target, soal_num)
            print_file_result(res, s)
            sys.exit(0 if res.perfect else 1)

        cwd = pathlib.Path.cwd()
        files = find_soal_files(cwd, soal_num) or find_soal_files(LATIHAN_DIR, soal_num)
        if not files:
            print(s.red(f"[ERROR] Tidak ditemukan file soal{soal_num}_*.py di folder ini atau {LATIHAN_DIR}"))
            sys.exit(1)
        results = [grade_file(f, soal_num) for f in files]
        for r in results:
            print_file_result(r, s)
        if len(results) > 1:
            print_summary(results, f"Soal {soal_num}", s)
        sys.exit(0 if all(r.perfect for r in results) else 1)

    # Mode: cek <file.py> [file2.py ...]
    targets: list[pathlib.Path] = []
    for a in args:
        t = resolve_file(a)
        if not t:
            print(s.red(f"[ERROR] File tidak ditemukan: {a}"))
            sys.exit(1)
        targets.append(t)

    try:
        results = [grade_file(t, soal_override) for t in targets]
    except ValueError as err:
        print(s.red(f"[ERROR] {err}"))
        sys.exit(1)

    for r in results:
        print_file_result(r, s)
    if len(results) > 1:
        print_summary(results, f"{len(results)} file", s)
    sys.exit(0 if all(r.perfect for r in results) else 1)


if __name__ == "__main__":
    main()
