import difflib
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import sublime
import sublime_plugin

REGION_ERROR = "python_ruff_error"
REGION_WARN = "python_ruff_warn"
STATUS_KEY = "python_ruff_status"
RULES = "E,F,W,I,B,UP,SIM"
IGNORE_RULES = "E501"

# Daftar fungsi/tipe/exception bawaan Python 3 untuk deteksi typo & autocomplete offline
PYTHON_BUILTINS = [
    "abs", "all", "any", "ascii", "bin", "bool", "breakpoint", "bytearray",
    "bytes", "callable", "chr", "classmethod", "compile", "complex", "delattr",
    "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float",
    "format", "frozenset", "getattr", "globals", "hasattr", "hash", "help",
    "hex", "id", "input", "int", "isinstance", "issubclass", "iter", "len",
    "list", "locals", "map", "max", "memoryview", "min", "next", "object",
    "oct", "open", "ord", "pow", "print", "property", "range", "repr",
    "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
    "str", "sum", "super", "tuple", "type", "vars", "zip",
    "True", "False", "None",
    "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
    "AttributeError", "FileNotFoundError", "RuntimeError", "OSError",
    "ZeroDivisionError", "ImportError", "StopIteration",
]

# Method bawaan Python 3 paling umum (str, list, dict, set, file, path)
COMMON_METHODS = [
    "append", "clear", "copy", "count", "extend", "index", "insert", "pop",
    "remove", "reverse", "sort",
    "get", "items", "keys", "popitem", "setdefault", "update", "values",
    "add", "difference", "discard", "intersection", "issubset", "issuperset",
    "union",
    "capitalize", "casefold", "center", "encode", "decode", "endswith",
    "find", "format", "isalnum", "isalpha", "isdigit", "islower", "isnumeric",
    "isspace", "isupper", "join", "ljust", "lower", "lstrip", "partition",
    "removeprefix", "removesuffix", "replace", "rfind", "rjust", "rsplit",
    "rstrip", "split", "splitlines", "startswith", "strip", "swapcase",
    "title", "upper", "zfill",
    "close", "flush", "read", "readline", "readlines", "seek", "write",
    "writelines", "exists", "mkdir", "read_text", "write_text", "glob",
]

# Kamus typo umum
TYPO_ALIASES = {
    "prnt": "print",
    "pirnt": "print",
    "pritn": "print",
    "prnit": "print",
    "lenght": "len",
    "length": "len",
    "lne": "len",
    "rnage": "range",
    "ragne": "range",
    "inpt": "input",
    "ipnut": "input",
    "retrun": "return",
    "ture": "True",
    "flase": "False",
    "fasle": "False",
    "none": "None",
    "apend": "append",
    "appnd": "append",
    "appeend": "append",
    "splt": "split",
    "spilt": "split",
    "strp": "strip",
    "stirp": "strip",
    "lowr": "lower",
    "uppr": "upper",
    "itmes": "items",
    "valus": "values",
    "kyes": "keys",
    "replce": "replace",
    "formatt": "format",
    "statrswith": "startswith",
    "endwith": "endswith",
    "startwith": "startswith",
}

# Kamus lengkap kode Ruff (E, F, W, I, B, UP, SIM) -> Bahasa Indonesia
RUFF_EXACT_ID = {
    # Imports (I, E4, F4)
    "I001": "Urutan import belum rapi (tekan Ctrl+S untuk merapikan)",
    "I002": "Import wajib belum ditambahkan di bagian atas file",
    "E401": "Pisahkan beberapa import ke baris masing-masing (1 modul per baris)",
    "E402": "Import sebaiknya diletakkan di bagian paling atas file",
    "F402": "Nama import tertimpa oleh variabel perulangan (loop)",
    "F403": "Hindari `from modul import *`, sebutkan nama yang dipakai secara jelas",
    "F404": "Import `from __future__` harus diletakkan di baris paling atas file",
    "F405": "Nama ini berasal dari `import *` dan bisa membingungkan",
    "F406": "`from modul import *` hanya boleh di level atas modul, bukan di dalam fungsi",

    # Pyflakes / Logika & Typo (F)
    "F501": "Format string `%` tidak valid",
    "F504": "Argumen format `%` ada yang tidak dipakai",
    "F521": "Format `.format(...)` tidak valid",
    "F522": "Argumen kata kunci pada `.format(...)` tidak terpakai",
    "F523": "Argumen posisi pada `.format(...)` tidak terpakai",
    "F524": "Argumen untuk placeholder `.format(...)` kurang",
    "F541": "f-string tidak memiliki variabel/placeholder `{ }` (hapus huruf `f`)",
    "F602": "Key dictionary berupa variabel yang sama ditulis duplikat",
    "F621": "Terlalu banyak ekspresi bintang (`*`) dalam unpacking",
    "F622": "Dua ekspresi bintang (`*`) tidak boleh dalam satu unpacking",
    "F631": "Assert memakai tuple tidak kosong — kondisinya akan selalu True",
    "F632": "Gunakan `==` untuk membandingkan nilai teks/angka, bukan `is`",
    "F633": "Penggunaan `>>` pada `print` sudah tidak valid di Python 3",
    "F634": "Kondisi `if` berupa tuple — akan selalu bernilai True",
    "F701": "`break` hanya boleh digunakan di dalam perulangan (`for`/`while`)",
    "F702": "`continue` hanya boleh digunakan di dalam perulangan (`for`/`while`)",
    "F704": "`yield` / `yield from` hanya boleh digunakan di dalam fungsi",
    "F706": "`return` hanya boleh digunakan di dalam fungsi",
    "F707": "`except:` kosong harus diletakkan di urutan terakhir",
    "F822": "Nama di dalam `__all__` belum didefinisikan",
    "F823": "Variabel lokal dipakai sebelum diberi nilai",
    "F831": "Nama parameter fungsi ditulis duplikat",
    "F901": "`raise NotImplemented` salah — gunakan `raise NotImplementedError`",

    # PEP 8 / Style & Perbandingan (E, W)
    "E701": "Pisahkan pernyataan setelah `:` ke baris baru",
    "E702": "Hindari menggabungkan beberapa pernyataan dengan `;` dalam satu baris",
    "E703": "Titik koma (`;`) di akhir baris tidak diperlukan di Python",
    "E711": "Bandingkan None dengan `is None` / `is not None`, bukan `==` atau `!=`",
    "E712": "Hindari `== True` / `== False`, tulis `if kondisi:` atau `if not kondisi:` langsung",
    "E713": "Gunakan `a not in b` daripada `not a in b`",
    "E714": "Gunakan `a is not b` daripada `not a is b`",
    "E721": "Gunakan `isinstance(x, Tipe)` untuk mengecek tipe data, bukan `type(x) == ...`",
    "E722": "Hindari `except:` kosong — sebutkan tipe error (misal `except Exception:`)",
    "E731": "Lebih baik buat `def nama():` daripada menyimpan `lambda` ke variabel",
    "E741": "Nama variabel terlalu ambigu (`l`, `O`, atau `I` mirip angka `1`/`0`)",
    "E742": "Nama class terlalu ambigu (`l`, `O`, atau `I`)",
    "E743": "Nama fungsi terlalu ambigu (`l`, `O`, atau `I`)",
    "W191": "Indentasi mengandung karakter Tab — gunakan 4 spasi",
    "W291": "Ada spasi berlebih di akhir baris",
    "W292": "Tambahkan satu baris kosong di akhir file",
    "W293": "Baris kosong mengandung spasi berlebih",
    "W605": "Urutan escape `\\` tidak valid di dalam string (gunakan raw string `r\"...\"`)",

    # Bugbear / Jebakan Umum Python (B)
    "B002": "Operator `++x` tidak menambah nilai di Python — gunakan `x += 1`",
    "B003": "Mengubah `os.environ` langsung bisa bermasalah — gunakan `os.environ.clear()`",
    "B004": "Gunakan `callable(obj)` daripada `hasattr(obj, '__call__')`",
    "B005": "`.strip()` menghapus per karakter, bukan kata utuh — pakai `.removeprefix()` / `.removesuffix()`",
    "B006": "Jangan pakai list/dict (`[]`/`{}`) sebagai default parameter — gunakan `None` lalu buat di dalam fungsi",
    "B008": "Jangan memanggil fungsi langsung di nilai default parameter",
    "B009": "Gunakan `obj.atribut` langsung daripada `getattr(obj, 'atribut')`",
    "B010": "Gunakan `obj.atribut = nilai` langsung daripada `setattr(obj, 'atribut', nilai)`",
    "B011": "Hindari `assert False` — gunakan `raise AssertionError(...)`",
    "B012": "Hindari `return`/`break`/`continue` di dalam blok `finally` karena bisa menelan error",
    "B013": "Tuple di `except (Error,)` hanya berisi 1 item — tulis `except Error:` saja",
    "B014": "Ada tipe exception duplikat di dalam `except (...)`",
    "B015": "Hasil perbandingan tidak dipakai/disimpan — mungkin maksudnya `=` bukan `==`?",
    "B016": "Tidak bisa melakukan `raise` pada angka/teks langsung — gunakan class Exception",
    "B017": "Hindari menangkap `Exception` terlalu luas saat pengujian",
    "B018": "Ekspresi ini tidak berguna karena hasilnya tidak disimpan atau dipakai",
    "B019": "Hati-hati memakai `@lru_cache` pada method class (bisa menyebabkan kebocoran memori)",
    "B020": "Variabel loop menimpa koleksi yang sedang diiterasi",
    "B023": "Fungsi di dalam loop menangkap variabel loop secara terlambat (ikat dengan parameter default)",
    "B024": "Class abstrak ini belum memiliki `@abstractmethod`",
    "B025": "Blok `except` menangkap tipe error yang sama lebih dari sekali",
    "B026": "Argumen `*args` sebaiknya diletakkan setelah argumen kata kunci",
    "B027": "Method kosong di class abstrak — tambahkan `@abstractmethod` jika wajib di-override",
    "B028": "Sertakan parameter `stacklevel=2` saat memanggil `warnings.warn(...)`",
    "B029": "`except ():` kosong tidak akan menangkap error apa pun",
    "B030": "Isi `except` harus berupa class Exception, bukan tipe lain",
    "B033": "Ada elemen duplikat di dalam `set`",
    "B904": "Di dalam `except`, gunakan `raise ErrorBaru(...) from err` agar jejak error tetap utuh",
    "B905": "Tambahkan `strict=True` atau `strict=False` pada `zip(...)` agar aman jika panjang list berbeda",

    # Simplify (SIM)
    "SIM101": "Beberapa `isinstance(...)` dengan `or` bisa digabung jadi `isinstance(x, (A, B))`",
    "SIM102": "Gabungkan `if` bersarang menjadi satu `if` dengan `and`",
    "SIM103": "Langsung `return` kondisi boolean tanpa `if ...: return True else: return False`",
    "SIM105": "Blok `try/except: pass` bisa diringkas dengan `contextlib.suppress(...)`",
    "SIM108": "Blok `if/else` singkat ini bisa diringkas menjadi ternary (`a if kondisi else b`)",
    "SIM109": "Beberapa perbandingan `==` dengan `or` bisa diringkas pakai `x in (a, b)`",
    "SIM110": "Loop pengecekan ini bisa diringkas dengan `any(...)`",
    "SIM111": "Loop pengecekan ini bisa diringkas dengan `all(...)`",
    "SIM114": "Dua cabang `if`/`elif` punya isi sama — gabungkan kondisinya dengan `or`",
    "SIM115": "Gunakan `with open(...) as f:` agar file otomatis tertutup setelah selesai",
    "SIM117": "Gabungkan beberapa `with` bersarang menjadi satu baris `with a, b:`",
    "SIM118": "Gunakan `k in d` langsung daripada `k in d.keys()`",
    "SIM201": "Gunakan `a != b` daripada `not a == b`",
    "SIM202": "Gunakan `a == b` daripada `not a != b`",
    "SIM210": "Langsung `bool(kondisi)` daripada `True if kondisi else False`",
    "SIM211": "Langsung `not kondisi` daripada `False if kondisi else True`",
    "SIM222": "Ekspresi `... or True` akan selalu bernilai True",
    "SIM223": "Ekspresi `... and False` akan selalu bernilai False",
    "SIM300": "Tulis variabel di sebelah kiri perbandingan (misal `x == 5`, bukan `5 == x`)",
    "SIM401": "Gunakan `d.get(key, default)` daripada `if key in d: ... else: ...`",

    # Python 3 Modern (UP / pyupgrade)
    "UP004": "Class mewarisi `object` tidak perlu ditulis lagi di Python 3 (`class Nama:` saja)",
    "UP006": "Di Python 3.9+, gunakan tipe bawaan `list[...]`, `dict[...]` daripada `typing.List`/`Dict`",
    "UP007": "Di Python 3.10+, gunakan `X | Y` daripada `Union[X, Y]` atau `Optional[X]`",
    "UP008": "Di Python 3, cukup tulis `super()` tanpa argumen",
    "UP009": "Deklarasi `# -*- coding: utf-8 -*-` tidak diperlukan lagi di Python 3",
    "UP015": "Mode `'r'` pada `open(...)` adalah default dan boleh tidak ditulis",
    "UP018": "Penulisan literal bawaan seperti `str()` / `int()` bisa disederhanakan menjadi `\"\"` / `0`",
    "UP031": "Gunakan f-string atau `.format()` daripada format lama `%`",
    "UP032": "Gunakan f-string (`f\"...\"`) daripada `.format(...)` agar lebih cepat & jelas",
    "UP035": "Import tipe ini sudah usang — gunakan versi bawaan Python 3 modern",
    "UP038": "Gunakan `isinstance(x, A | B)` (sintaks Python 3.10+)",
    "UP045": "Gunakan `X | None` daripada `Optional[X]`",
}

_DIAGNOSTICS = {}
_PHANTOM_SETS = {}
_TIMERS = {}
_FORMATTING_VIEWS = set()
_INLINE_ENABLED = True


def find_ruff():
    candidates = [
        shutil.which("ruff") or "",
        shutil.which("ruff.exe") or "",
        os.path.expanduser("~/.local/bin/ruff"),
        os.path.expanduser("~/.local/bin/ruff.exe"),
        "/usr/local/bin/ruff",
        "/usr/bin/ruff",
    ]
    if sys.platform.startswith("win"):
        import glob

        local_app = os.environ.get("LOCALAPPDATA", "")
        roaming_app = os.environ.get("APPDATA", "")
        for base in (local_app, roaming_app):
            if base:
                candidates.extend(glob.glob(os.path.join(base, "Programs", "Python", "Python*", "Scripts", "ruff.exe")))
                candidates.extend(glob.glob(os.path.join(base, "Python", "Python*", "Scripts", "ruff.exe")))
    for path in candidates:
        if path and os.path.isfile(path) and (sys.platform.startswith("win") or os.access(path, os.X_OK)):
            return path
    return None


def is_python_view(view):
    if not view or view.is_scratch() or view.settings().get("is_widget"):
        return False
    syntax = view.syntax()
    if syntax and "python" in (syntax.scope or "").lower():
        return True
    fname = view.file_name() or ""
    return fname.endswith(".py")


def is_severe(code):
    if not code:
        return True
    c = str(code)
    return (
        c == "invalid-syntax"
        or c == "SYNTAX"
        or c == "TYPO-METHOD"
        or c == "JUKNIS"
        or c.startswith("E9")
        or c.startswith("F82")
        or c.startswith("F6")
        or c.startswith("F7")
        or c.startswith("B006")
    )


def extract_local_symbols(code_text):
    symbols = set()
    for m in re.finditer(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)", code_text, re.M):
        symbols.add(m.group(1))
        for raw_arg in m.group(2).split(","):
            arg = raw_arg.strip().lstrip("*").split(":")[0].split("=")[0].strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", arg):
                symbols.add(arg)
    for m in re.finditer(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", code_text, re.M):
        symbols.add(m.group(1))
    for m in re.finditer(r"^[ \t]*([A-Za-z_][A-Za-z0-9_]*)[ \t]*(?::[^=\n]+)?=(?!=)", code_text, re.M):
        name = m.group(1)
        if name not in ("if", "elif", "else", "for", "while", "return", "with", "try", "except", "def", "class", "import", "from"):
            symbols.add(name)
    for m in re.finditer(r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b", code_text):
        symbols.add(m.group(1))
    for m in re.finditer(r"^\s*import\s+([A-Za-z_][A-Za-z0-9_]*)", code_text, re.M):
        symbols.add(m.group(1))
    for m in re.finditer(r"^\s*from\s+\S+\s+import\s+(.+)$", code_text, re.M):
        for part in m.group(1).split(","):
            name = part.strip().split(" as ")[-1].strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                symbols.add(name)
    return symbols


def suggest_name(bad_name, local_symbols):
    if bad_name in TYPO_ALIASES:
        return TYPO_ALIASES[bad_name]
    pool = sorted(set(PYTHON_BUILTINS) | set(local_symbols) - {bad_name})
    matches = difflib.get_close_matches(bad_name, pool, n=1, cutoff=0.62)
    return matches[0] if matches else None


# Kamus typo khusus method bawaan yang 100% bebas false-positive pada framework (FastAPI, pathlib, pytest, dll.)
METHOD_TYPO_MAP = {
    "apend": "append",
    "appnd": "append",
    "appeend": "append",
    "extnd": "extend",
    "insrt": "insert",
    "remvoe": "remove",
    "revese": "reverse",
    "splt": "split",
    "spilt": "split",
    "strp": "strip",
    "stirp": "strip",
    "lstrp": "lstrip",
    "rstrp": "rstrip",
    "lowr": "lower",
    "uppr": "upper",
    "itmes": "items",
    "valus": "values",
    "kyes": "keys",
    "replce": "replace",
    "repalce": "replace",
    "formatt": "format",
    "fomat": "format",
    "startwith": "startswith",
    "statrswith": "startswith",
    "endwith": "endswith",
    "redlines": "readlines",
    "redline": "readline",
    "wrte": "write",
    "clsoe": "close",
    "coppy": "copy",
    "conut": "count",
    "updat": "update",
    "jion": "join",
    "encde": "encode",
    "decde": "decode",
    "capitialize": "capitalize",
}


def find_method_typos(code_text, local_symbols):
    """Deteksi offline typo method bawaan secara presisi (0 false positive di framework/library)."""
    findings = []
    known_local = set(local_symbols)
    lines = code_text.splitlines()
    for row_idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        code_part = line.split("#", 1)[0]
        for m in re.finditer(r"\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", code_part):
            meth = m.group(1)
            if meth in known_local:
                continue
            suggestion = METHOD_TYPO_MAP.get(meth)
            if suggestion:
                findings.append(
                    {
                        "row": row_idx,
                        "col": m.start(1),
                        "end_row": row_idx,
                        "end_col": m.end(1),
                        "code": "TYPO-METHOD",
                        "message": "Typo method `.{}()` -> maksudnya `.{}()`?".format(meth, suggestion),
                        "bad_token": meth,
                        "suggestion": suggestion,
                        "is_call": True,
                        "fixable": True,
                        "severe": True,
                    }
                )
    return findings


def find_juknis_input_prompts(code_text):
    """Cek aturan Juknis Lomba: input() wajib kosong tanpa teks di dalam kurung."""
    findings = []
    lines = code_text.splitlines()
    for row_idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        code_part = line.split("#", 1)[0]
        # Cocokkan pemanggilan input(...) yang tidak diawali huruf/titik (bukan foo.input atau my_input)
        for m in re.finditer(r"(?<![A-Za-z0-9_.])input\s*\(([^)]+)\)", code_part):
            inner = m.group(1).strip()
            if inner:
                findings.append(
                    {
                        "row": row_idx,
                        "col": m.start(0),
                        "end_row": row_idx,
                        "end_col": m.end(0),
                        "code": "JUKNIS",
                        "message": "`input()` wajib kosong tanpa teks di dalam kurung (tekan Ctrl+. untuk kosongkan)",
                        "bad_token": m.group(0),
                        "suggestion": "input()",
                        "is_call": True,
                        "fixable": True,
                        "severe": True,
                    }
                )
    return findings


def translate_message_id(code, msg):
    """Terjemahkan semua pesan error/warning Ruff & sintaks Python ke Bahasa Indonesia (100% offline)."""
    c = str(code or "")

    # 1. Syntax Error (invalid-syntax / E9xx)
    if c in ("invalid-syntax", "SYNTAX") or c.startswith("E9"):
        low = msg.lower()
        if "expected `:`" in low or "expected ':'" in low:
            return "Kesalahan sintaks: lupa tanda titik dua (`:`)"
        if "expected an indented block" in low:
            return "Kesalahan sintaks: baris di bawah ini perlu menjorok ke dalam (4 spasi)"
        if "unexpected indentation" in low or "unindent" in low:
            return "Kesalahan sintaks: indentasi tidak sejajar atau berlebih"
        if "expected `)`" in low or "unclosed `(`" in low or "was never closed" in low:
            return "Kesalahan sintaks: tanda kurung `()` belum ditutup"
        if "expected `]`" in low or "unclosed `[`" in low:
            return "Kesalahan sintaks: tanda kurung siku `[]` belum ditutup"
        if "expected `}`" in low or "unclosed `{`" in low:
            return "Kesalahan sintaks: tanda kurung kurawal `{}` belum ditutup"
        if "unterminated string" in low or "eol while scanning string" in low:
            return "Kesalahan sintaks: tanda kutip string belum ditutup"
        if "cannot assign to" in low:
            return "Kesalahan sintaks: nilai tidak bisa dimasukkan ke sisi kiri tanda `=` ini"
        if "expected an expression" in low:
            return "Kesalahan sintaks: kurang nilai/ekspresi di posisi ini"
        if "unexpected token" in low:
            return "Kesalahan sintaks: ada simbol/kata tak terduga ({})".format(msg)
        return "Kesalahan sintaks: {}".format(msg)

    # 2. Pola spesifik dengan ekstraksi nama simbol/angka
    patterns = [
        (r"`([^`]+)` imported but unused", lambda m: "Import `{}` tidak digunakan".format(m.group(1))),
        (r"Local variable `([^`]+)` is assigned to but never used", lambda m: "Variabel lokal `{}` dibuat tetapi tidak pernah dipakai".format(m.group(1))),
        (r"Dictionary key literal `([^`]+)` repeated", lambda m: "Key dictionary `{}` ditulis duplikat".format(m.group(1))),
        (r"Loop control variable `([^`]+)` not used", lambda m: "Variabel loop `{}` tidak dipakai di dalam perulangan (ganti ke `_`)".format(m.group(1))),
        (r"Redefinition of unused `([^`]+)`", lambda m: "Nama `{}` didefinisikan ulang padahal sebelumnya belum dipakai".format(m.group(1))),
        (r"Line too long \((\d+) > (\d+)\)", lambda m: "Baris terlalu panjang ({} > {} karakter)".format(m.group(1), m.group(2))),
        (r"Unable to detect undefined names", lambda m: "Tidak dapat memeriksa nama variabel karena ada `import *`"),
        (r"Cannot assign to `([^`]+)`", lambda m: "Tidak boleh mengisi ulang nama `{}`".format(m.group(1))),
        (r"Duplicate argument name `([^`]+)`", lambda m: "Nama parameter `{}` ditulis duplikat di fungsi".format(m.group(1))),
        (r"Undefined name `([^`]+)`", lambda m: "Nama `{}` belum didefinisikan".format(m.group(1))),
    ]
    for pat, fn in patterns:
        m = re.search(pat, msg)
        if m:
            return fn(m)

    # 3. Kamus kode aturan lengkap
    if c in RUFF_EXACT_ID:
        return RUFF_EXACT_ID[c]

    # 4. Fallback cerdas per kategori kode
    if c.startswith("UP"):
        return "Bisa diperbarui ke sintaks Python 3 modern (tekan Ctrl+. untuk rapikan)"
    if c.startswith("SIM"):
        return "Saran penyederhanaan kode agar lebih bersih & mudah dibaca"
    if c.startswith("B"):
        return "Potensi bug Python: {}".format(msg)
    if c.startswith("F"):
        return "Kesalahan logika/nama Python: {}".format(msg)
    if c.startswith("E") or c.startswith("W"):
        return "Kerapian sintaks PEP 8: {}".format(msg)

    return msg


def run_ruff(args, code_text):
    ruff = find_ruff()
    if not ruff:
        return None, None, "ruff tidak ditemukan di PATH"
    try:
        kwargs = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        if sys.platform.startswith("win") and hasattr(subprocess, "CREATE_NO_WINDOW"):
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen([ruff] + args, **kwargs)
        out, _err = proc.communicate(code_text.encode("utf-8"), timeout=5)
        return proc.returncode, out, None
    except Exception as exc:
        return None, None, str(exc)


def lint_view_async(view):
    if not is_python_view(view):
        return
    view_id = view.id()
    code = view.substr(sublime.Region(0, view.size()))
    fname = view.file_name() or "untitled.py"

    rc, out, err = run_ruff(
        [
            "check",
            "--output-format",
            "json",
            "--select",
            RULES,
            "--ignore",
            IGNORE_RULES,
            "--stdin-filename",
            fname,
            "-",
        ],
        code,
    )
    if err or rc is None:
        return

    try:
        items = json.loads(out.decode("utf-8", errors="replace") or "[]")
    except Exception:
        items = []

    local_symbols = extract_local_symbols(code)
    extra_findings = find_method_typos(code, local_symbols) + find_juknis_input_prompts(code)

    sublime.set_timeout(
        lambda: apply_diagnostics(view, view_id, code, items, extra_findings, local_symbols),
        0,
    )


def apply_diagnostics(view, view_id, code_text, items, method_typos, local_symbols):
    if not view.is_valid():
        return

    error_regions = []
    warn_regions = []
    diag_list = []
    per_row = {}

    for item in items:
        loc = item.get("location") or {}
        end_loc = item.get("end_location") or loc
        row = max(0, int(loc.get("row", 1)) - 1)
        col = max(0, int(loc.get("column", 1)) - 1)
        end_row = max(row, int(end_loc.get("row", row + 1)) - 1)
        end_col = max(col + 1, int(end_loc.get("column", col + 1)) - 1)

        start_pt = view.text_point(row, col)
        end_pt = view.text_point(end_row, end_col)
        if end_pt <= start_pt:
            end_pt = min(view.size(), start_pt + 1)

        region = sublime.Region(start_pt, end_pt)
        code = item.get("code") or "invalid-syntax"
        msg = item.get("message") or "Kesalahan"
        fixable = bool(item.get("fix"))
        severe = is_severe(code)
        bad_token = None
        suggestion = None
        is_call = False

        if code == "F821":
            m = re.search(r"Undefined name `([^`]+)`", msg)
            if m:
                bad_token = m.group(1)
                after_char = view.substr(sublime.Region(end_pt, min(view.size(), end_pt + 1)))
                is_call = after_char == "("
                suggestion = suggest_name(bad_token, local_symbols)
                if suggestion:
                    msg = "Nama `{}` belum dikenal -> maksudnya `{}`?".format(bad_token, suggestion)
                    fixable = True
                elif is_call:
                    msg = "Fungsi `{}` belum dibuat (Ctrl+. untuk buat otomatis)".format(bad_token)
                    fixable = True
                else:
                    msg = "Nama `{}` belum didefinisikan".format(bad_token)
        else:
            msg = translate_message_id(code, msg)

        if severe:
            error_regions.append(region)
        else:
            warn_regions.append(region)

        entry = {
            "row": row,
            "col": col,
            "code": code,
            "message": msg,
            "fixable": fixable,
            "severe": severe,
            "bad_token": bad_token,
            "suggestion": suggestion,
            "is_call": is_call,
            "region": region,
        }
        diag_list.append(entry)

        prev = per_row.get(row)
        if prev is None or (severe and not prev["severe"]):
            per_row[row] = entry

    for mt in method_typos:
        start_pt = view.text_point(mt["row"], mt["col"])
        end_pt = view.text_point(mt["end_row"], mt["end_col"])
        region = sublime.Region(start_pt, end_pt)
        error_regions.append(region)
        entry = dict(mt)
        entry["region"] = region
        diag_list.append(entry)
        prev = per_row.get(mt["row"])
        if prev is None or not prev["severe"]:
            per_row[mt["row"]] = entry

    _DIAGNOSTICS[view_id] = diag_list

    flags = (
        sublime.DRAW_NO_FILL
        | sublime.DRAW_NO_OUTLINE
        | sublime.DRAW_SQUIGGLY_UNDERLINE
    )
    view.add_regions(REGION_ERROR, error_regions, "region.orangish", "dot", flags)
    view.add_regions(REGION_WARN, warn_regions, "region.yellowish", "circle", flags)

    render_phantoms(view, view_id, per_row)
    update_status(view)


def format_rich_html(text):
    """Ubah backtick `kode` menjadi span kode berwarna lembut agar tampil bersih tanpa karakter `."""
    escaped = html.escape(text)
    return re.sub(
        r"`([^`]+)`",
        r"<span style='color:#79c0ff;background:#161b22;padding:0 3px;border-radius:3px;'>\1</span>",
        escaped,
    )


def render_phantoms(view, view_id, per_row):
    pset = _PHANTOM_SETS.get(view_id)
    if pset is None:
        pset = sublime.PhantomSet(view, "python_ruff_inline")
        _PHANTOM_SETS[view_id] = pset

    if not _INLINE_ENABLED or not per_row:
        pset.update([])
        return

    phantoms = []
    for row in sorted(per_row.keys()):
        d = per_row[row]
        line_reg = view.line(view.text_point(row, 0))
        line_text = view.substr(line_reg)
        # Sejajarkan posisi pesan tepat mengikuti indentasi baris kode (tidak mendorong `:` ke baris baru!)
        indent_cols = len(line_text) - len(line_text.lstrip(" \t"))
        anchor_pt = min(line_reg.begin() + indent_cols, line_reg.end())

        color = "#fdac54" if d["severe"] else "#d29922"
        icon = "●" if d["severe"] else "○"
        short_msg = d["message"]
        if len(short_msg) > 84:
            short_msg = short_msg[:81] + "..."
        body = (
            "<body style='margin:0;padding:0;background:transparent;'>"
            "<span style='color:{color};font-size:0.86em;'>"
            "{icon} [{code}] {msg}"
            "</span></body>"
        ).format(
            color=color,
            icon=icon,
            code=html.escape(str(d["code"])),
            msg=format_rich_html(short_msg),
        )
        phantoms.append(sublime.Phantom(sublime.Region(anchor_pt, anchor_pt), body, sublime.LAYOUT_BELOW))

    pset.update(phantoms)


def update_status(view):
    if not is_python_view(view):
        view.erase_status(STATUS_KEY)
        return

    diags = _DIAGNOSTICS.get(view.id(), [])
    if not diags:
        view.set_status(STATUS_KEY, "Py3 · Bersih (Offline)")
        return

    sel = view.sel()
    cur_row = view.rowcol(sel[0].begin())[0] if sel else -1
    for d in diags:
        if d["row"] == cur_row:
            hint = " [Ctrl+. perbaiki]" if d["fixable"] else ""
            view.set_status(
                STATUS_KEY,
                "Py3 [{}]: {}{}".format(d["code"], d["message"], hint),
            )
            return

    err_count = sum(1 for d in diags if d["severe"])
    warn_count = len(diags) - err_count
    view.set_status(
        STATUS_KEY,
        "Py3: {} error, {} peringatan (F8 | Ctrl+Shift+M)".format(err_count, warn_count),
    )


class PythonRuffReplaceTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text="", region_a=None, region_b=None):
        if region_a is not None and region_b is not None:
            self.view.replace(edit, sublime.Region(int(region_a), int(region_b)), text)
            return
        vp = self.view.viewport_position()
        saved_sel = [(r.a, r.b) for r in self.view.sel()]
        self.view.replace(edit, sublime.Region(0, self.view.size()), text)
        self.view.sel().clear()
        max_pt = self.view.size()
        for a, b in saved_sel:
            self.view.sel().add(sublime.Region(min(a, max_pt), min(b, max_pt)))
        sublime.set_timeout(lambda: self.view.set_viewport_position(vp, False), 1)


class PythonRuffFormatCommand(sublime_plugin.TextCommand):
    """Format rapi (PEP 8 indentasi + hapus unused imports + urutkan import) dengan guard anti-rusak."""

    def run(self, edit, remove_unused_imports=True, fix_all=False):
        if not is_python_view(self.view):
            return
        code = self.view.substr(sublime.Region(0, self.view.size()))
        if not code.strip():
            return
        fname = self.view.file_name() or "untitled.py"

        rc_check, _out_chk, err_chk = run_ruff(["format", "--check", "--stdin-filename", fname, "-"], code)
        if err_chk or rc_check is None:
            sublime.status_message("Py3: {}".format(err_chk or "ruff tidak tersedia"))
            return
        if rc_check == 2:
            threading.Thread(target=lint_view_async, args=(self.view,), daemon=True).start()
            sublime.status_message("Py3: Ada kesalahan sintaks — perbaiki dulu baris yang disorot (F8)")
            return

        working = code
        # Jangan hapus unused import otomatis pada __init__.py (sering dipakai untuk re-export paket)
        is_init_py = os.path.basename(fname) == "__init__.py"
        if fix_all:
            select_rules = RULES
        elif remove_unused_imports and not is_init_py:
            select_rules = "I,F401"
        else:
            select_rules = "I"
        fix_args = [
            "check",
            "--select",
            select_rules,
            "--ignore",
            IGNORE_RULES,
            "--fix",
            "--exit-zero",
            "--stdin-filename",
            fname,
            "-",
        ]
        if is_init_py:
            fix_args.insert(5, "--unfixable")
            fix_args.insert(6, "F401")
        rc_fix, out_fix, err_fix = run_ruff(fix_args, working)
        if not err_fix and rc_fix == 0 and out_fix:
            candidate = out_fix.decode("utf-8", errors="replace")
            if candidate.strip():
                working = candidate

        rc_fmt, out_fmt, err_fmt = run_ruff(["format", "--stdin-filename", fname, "-"], working)
        if err_fmt or rc_fmt != 0:
            threading.Thread(target=lint_view_async, args=(self.view,), daemon=True).start()
            return

        new_code = out_fmt.decode("utf-8", errors="replace")
        if new_code and new_code != code:
            _FORMATTING_VIEWS.add(self.view.id())
            try:
                vp = self.view.viewport_position()
                saved_sel = [(r.a, r.b) for r in self.view.sel()]
                self.view.replace(edit, sublime.Region(0, self.view.size()), new_code)
                self.view.sel().clear()
                max_pt = self.view.size()
                for a, b in saved_sel:
                    self.view.sel().add(sublime.Region(min(a, max_pt), min(b, max_pt)))
                sublime.set_timeout(lambda: self.view.set_viewport_position(vp, False), 1)
            finally:
                _FORMATTING_VIEWS.discard(self.view.id())

        threading.Thread(target=lint_view_async, args=(self.view,), daemon=True).start()


class PythonRuffCreateStubCommand(sublime_plugin.TextCommand):
    """Auto-buat kerangka fungsi baru untuk fungsi yang dipanggil tapi belum didefinisikan."""

    def run(self, edit, func_name="fungsi_baru", arg_count=0):
        params = ", ".join(["arg{}".format(i + 1) for i in range(max(0, int(arg_count)))])
        stub = (
            "\n\ndef {}({}):\n"
            "    \"\"\"TODO: jelaskan fungsi {}.\"\"\"\n"
            "    raise NotImplementedError\n"
        ).format(func_name, params, func_name)

        code = self.view.substr(sublime.Region(0, self.view.size()))
        insert_pos = 0
        for m in re.finditer(r"^(?:from\s+\S+\s+import\s+.+|import\s+.+)$", code, re.M):
            insert_pos = m.end()
        if insert_pos == 0:
            stub = stub.lstrip("\n") + "\n"
        self.view.insert(edit, insert_pos, stub)
        threading.Thread(target=lint_view_async, args=(self.view,), daemon=True).start()


class PythonRuffQuickFixCommand(sublime_plugin.TextCommand):
    """Menu Perbaikan Cepat (Ctrl+.) ala VS Code dalam Bahasa Indonesia."""

    def run(self, edit):
        if not is_python_view(self.view):
            return
        view = self.view
        diags = _DIAGNOSTICS.get(view.id(), [])
        sel = view.sel()
        cur_row = view.rowcol(sel[0].begin())[0] if sel else -1

        actions = []
        row_diags = [d for d in diags if d["row"] == cur_row]

        for d in row_diags:
            if d.get("code") == "JUKNIS" and d.get("suggestion"):
                actions.append(
                    (
                        "Sesuai Juknis: kosongkan menjadi `input()`",
                        ("replace_typo", d["region"].a, d["region"].b, "input()"),
                    )
                )
            elif d.get("suggestion") and d.get("bad_token"):
                actions.append(
                    (
                        "Perbaiki typo: `{}` -> `{}`".format(d["bad_token"], d["suggestion"]),
                        ("replace_typo", d["region"].a, d["region"].b, d["suggestion"]),
                    )
                )
            if d.get("code") == "F821" and d.get("bad_token") and d.get("is_call"):
                line_text = view.substr(view.line(d["region"].a))
                m_call = re.search(re.escape(d["bad_token"]) + r"\(([^)]*)\)", line_text)
                argc = 0
                if m_call and m_call.group(1).strip():
                    argc = len([p for p in m_call.group(1).split(",") if p.strip()])
                actions.append(
                    (
                        "Buat fungsi baru: def {}(...)".format(d["bad_token"]),
                        ("create_stub", d["bad_token"], argc),
                    )
                )

        actions.append(
            (
                "Rapikan semua otomatis (hapus import tak terpakai, indentasi & sintaks)",
                ("fix_all",),
            )
        )

        labels = [a[0] for a in actions]

        def on_pick(idx):
            if idx < 0:
                return
            act = actions[idx][1]
            kind = act[0]
            if kind == "replace_typo":
                _, a, b, repl = act
                view.run_command(
                    "python_ruff_replace_text",
                    {"text": repl, "region_a": a, "region_b": b},
                )
                threading.Thread(target=lint_view_async, args=(view,), daemon=True).start()
                sublime.status_message("Py3: Typo diperbaiki menjadi {}".format(repl))
            elif kind == "create_stub":
                _, fn_name, argc = act
                view.run_command(
                    "python_ruff_create_stub",
                    {"func_name": fn_name, "arg_count": argc},
                )
                sublime.status_message("Py3: Fungsi def {}() berhasil dibuat".format(fn_name))
            elif kind == "fix_all":
                view.run_command(
                    "python_ruff_format",
                    {"remove_unused_imports": True, "fix_all": True},
                )
                sublime.status_message("Py3: Perapian otomatis selesai (Offline)")

        if len(actions) == 1:
            on_pick(0)
        else:
            view.window().show_quick_panel(labels, on_pick)


class PythonRunInteractiveCommand(sublime_plugin.WindowCommand):
    """Shortcut F6: Simpan file Python lalu jalankan di Terminal Interaktif (mendukung input())."""

    def run(self):
        view = self.window.active_view()
        if not is_python_view(view):
            sublime.status_message("Py3: Buka file .py terlebih dahulu untuk menjalankan.")
            return
        fname = view.file_name()
        if not fname:
            sublime.status_message("Py3: Simpan file .py terlebih dahulu (Ctrl+S) sebelum menjalankan (F6).")
            return
        if view.is_dirty():
            view.run_command("save")

        bname = os.path.basename(fname)
        title = "Python 3 — {}".format(bname)
        try:
            if sys.platform.startswith("win"):
                py_exe = shutil.which("python") or shutil.which("py") or "python"
                cmd_line = 'start "{}" cmd /k "{} -u "{}" & echo. & pause"'.format(title, py_exe, fname)
                subprocess.Popen(cmd_line, shell=True)
            else:
                runner = os.path.expanduser("~/.local/bin/py3-run-interactive")
                if os.path.isfile(runner):
                    inner = "bash {} {}".format(shlex.quote(runner), shlex.quote(fname))
                else:
                    inner = "python3 -u {}; echo; read -p 'Tekan Enter untuk menutup...'".format(shlex.quote(fname))
                term_cmds = [
                    ("lxterminal", ["lxterminal", "-t", title, "-e", inner]),
                    ("xfce4-terminal", ["xfce4-terminal", "--title", title, "-e", inner]),
                    ("gnome-terminal", ["gnome-terminal", "--title", title, "--", "bash", "-c", inner]),
                    ("konsole", ["konsole", "-e", "bash", "-c", inner]),
                    ("mate-terminal", ["mate-terminal", "-t", title, "-e", inner]),
                    ("x-terminal-emulator", ["x-terminal-emulator", "-e", "bash", "-c", inner]),
                    ("xterm", ["xterm", "-T", title, "-e", "bash", "-c", inner]),
                ]
                launched = False
                for term_bin, argv in term_cmds:
                    if shutil.which(term_bin):
                        subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        launched = True
                        break
                if not launched:
                    sublime.status_message("Py3: Terminal emulator tidak ditemukan.")
                    return
            sublime.status_message("Py3: Menjalankan {} di Terminal Interaktif...".format(bname))
        except Exception as exc:
            sublime.status_message("Py3: Gagal membuka Terminal ({})".format(exc))


class PythonRuffNextErrorCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if not is_python_view(self.view):
            return
        diags = _DIAGNOSTICS.get(self.view.id(), [])
        if not diags:
            sublime.status_message("Py3: Mantap, tidak ada error atau peringatan!")
            return
        cur_pt = self.view.sel()[0].begin() if self.view.sel() else 0
        ordered = sorted(diags, key=lambda d: (d["row"], d["col"]))
        target = ordered[0]
        for d in ordered:
            if d["region"].begin() > cur_pt:
                target = d
                break
        self.view.sel().clear()
        self.view.sel().add(target["region"])
        self.view.show_at_center(target["region"])
        update_status(self.view)


class PythonRuffToggleInlineCommand(sublime_plugin.WindowCommand):
    def run(self):
        global _INLINE_ENABLED
        _INLINE_ENABLED = not _INLINE_ENABLED
        view = self.window.active_view()
        if view and is_python_view(view):
            threading.Thread(target=lint_view_async, args=(view,), daemon=True).start()
        state = "AKTIF" if _INLINE_ENABLED else "NONAKTIF"
        sublime.status_message("Py3 Lensa Error Inline: {}".format(state))


class PythonRuffShowProblemsCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not is_python_view(view):
            return
        diags = _DIAGNOSTICS.get(view.id(), [])
        panel = self.window.create_output_panel("python_ruff_problems")
        panel.settings().set("result_file_regex", r"^(.+?):([0-9]+):([0-9]+):")
        panel.settings().set("word_wrap", True)
        fname = view.file_name() or "untitled.py"
        if not diags:
            content = "Pemeriksa Python 3 (Offline): Bersih, tidak ada error atau peringatan.\n"
        else:
            lines = [
                "{}:{}:{}: [{}] {}{}".format(
                    fname,
                    d["row"] + 1,
                    d["col"] + 1,
                    d["code"],
                    d["message"],
                    "  [Ctrl+. perbaiki]" if d["fixable"] else "",
                )
                for d in diags
            ]
            content = "\n".join(lines) + "\n"
        panel.set_read_only(False)
        panel.run_command("python_ruff_replace_text", {"text": content})
        panel.set_read_only(True)
        self.window.run_command("show_panel", {"panel": "output.python_ruff_problems"})


class PythonRuffListener(sublime_plugin.EventListener):
    def on_load_async(self, view):
        if is_python_view(view):
            lint_view_async(view)

    def on_activated_async(self, view):
        if is_python_view(view):
            lint_view_async(view)

    def on_modified_async(self, view):
        if not is_python_view(view) or view.id() in _FORMATTING_VIEWS:
            return
        vid = view.id()
        old = _TIMERS.get(vid)
        if old:
            old.cancel()
        t = threading.Timer(0.4, lint_view_async, args=(view,))
        t.daemon = True
        _TIMERS[vid] = t
        t.start()

    def on_pre_save(self, view):
        if is_python_view(view):
            view.run_command(
                "python_ruff_format",
                {"remove_unused_imports": True, "fix_all": True},
            )

    def on_post_save_async(self, view):
        if is_python_view(view):
            lint_view_async(view)

    def on_selection_modified(self, view):
        if is_python_view(view):
            update_status(view)

    def on_query_completions(self, view, prefix, locations):
        if not locations or not is_python_view(view):
            return None
        pt = locations[0]
        before_prefix = max(0, pt - len(prefix) - 1)
        prev_char = view.substr(sublime.Region(before_prefix, pt - len(prefix)))
        if prev_char == ".":
            return [
                sublime.CompletionItem(
                    trigger=m,
                    annotation="method bawaan",
                    completion="{}($1)".format(m),
                    completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
                    kind=sublime.KIND_FUNCTION,
                )
                for m in COMMON_METHODS
            ]

        return [
            sublime.CompletionItem(
                trigger=b,
                annotation=("fungsi bawaan" if b[0].islower() else "tipe/error"),
                completion=("{}($1)".format(b) if b[0].islower() else b),
                completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_FUNCTION if b[0].islower() else sublime.KIND_TYPE),
            )
            for b in PYTHON_BUILTINS
        ]

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT or not is_python_view(view):
            return
        diags = _DIAGNOSTICS.get(view.id(), [])
        row = view.rowcol(point)[0]
        matched = [d for d in diags if d["row"] == row]
        if not matched:
            return
        rows_html = []
        for d in matched:
            color = "#fdac54" if d["severe"] else "#f0b72f"
            label = "Error" if d["severe"] else "Peringatan"
            fix_note = (
                " <span style='color:#79c0ff;'>(Tekan Ctrl+. untuk perbaiki otomatis)</span>"
                if d["fixable"]
                else ""
            )
            rows_html.append(
                "<div style='margin:3px 0;'>"
                "<b style='color:{color};'>{label} [{code}]</b>: {msg}{fix}"
                "</div>".format(
                    color=color,
                    label=label,
                    code=html.escape(str(d["code"])),
                    msg=format_rich_html(d["message"]),
                    fix=fix_note,
                )
            )
        popup = (
            "<body style='background:#161b22;color:#e6edf3;padding:8px 10px;"
            "border:1px solid #30363d;font-size:0.92em;'>"
            + "".join(rows_html)
            + "</body>"
        )
        view.show_popup(popup, sublime.HIDE_ON_MOUSE_MOVE_AWAY, location=point, max_width=600)

    def on_close(self, view):
        vid = view.id()
        _DIAGNOSTICS.pop(vid, None)
        _PHANTOM_SETS.pop(vid, None)
        t = _TIMERS.pop(vid, None)
        if t:
            t.cancel()
