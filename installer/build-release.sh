#!/usr/bin/env bash
# Membangun seluruh artefak rilis (Linux .run, Linux .tar.gz, Windows .zip, Paket Soal & PDF)
set -euo pipefail

VERSION="${1:-v1.0.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

echo "==> Membangun rilis Koding Penggalang $VERSION ..."

# 1. Staging paket Linux
LINUX_STAGE="$STAGE_DIR/koding-penggalang-$VERSION-linux"
mkdir -p "$LINUX_STAGE/payload/installer"
cp -a "$ROOT_DIR/modul" "$ROOT_DIR/latihan" "$ROOT_DIR/kunci_jawaban" "$ROOT_DIR/penguji" \
      "$ROOT_DIR/cek_jawaban.py" "$ROOT_DIR/cek_jawaban_gui.py" "$ROOT_DIR/README.md" \
      "$LINUX_STAGE/payload/"
cp -a "$ROOT_DIR/installer/sublime_bundle" "$LINUX_STAGE/payload/installer/"
cp -a "$ROOT_DIR/installer/install-linux.sh" "$LINUX_STAGE/install-linux.sh"
cp -a "$ROOT_DIR/installer/CARA_INSTALL.txt" "$LINUX_STAGE/CARA_INSTALL.txt"
chmod +x "$LINUX_STAGE/install-linux.sh"
find "$LINUX_STAGE" -name "__pycache__" -type d -exec rm -rf {} +

# 1a. Linux tar.gz
LINUX_TGZ="$DIST_DIR/koding-penggalang-$VERSION-linux.tar.gz"
tar -C "$STAGE_DIR" -czf "$LINUX_TGZ" "koding-penggalang-$VERSION-linux"

# 1b. Linux 1-klik self-extracting installer (.run)
LINUX_RUN="$DIST_DIR/KodingPenggalang-Installer-Linux-$VERSION.run"
cat > "$LINUX_RUN" <<'HEADER'
#!/usr/bin/env bash
set -euo pipefail
TMP_EXTRACT="$(mktemp -d /tmp/koding-penggalang-install.XXXXXX)"
trap 'rm -rf "$TMP_EXTRACT"' EXIT
ARCHIVE_LINE="$(awk '/^__ARCHIVE_BELOW__$/ {print NR + 1; exit 0;}' "$0")"
tail -n +"$ARCHIVE_LINE" "$0" | tar -xz -C "$TMP_EXTRACT"
INSTALLER="$(find "$TMP_EXTRACT" -maxdepth 2 -name install-linux.sh | head -n 1)"
exec bash "$INSTALLER" "$@"
__ARCHIVE_BELOW__
HEADER
cat "$LINUX_TGZ" >> "$LINUX_RUN"
chmod +x "$LINUX_RUN"

# 2. Staging paket Windows (.zip dengan INSTALL_KODING_PENGGALANG.bat di root)
WIN_STAGE="$STAGE_DIR/koding-penggalang-$VERSION-windows"
mkdir -p "$WIN_STAGE/payload/installer"
cp -a "$ROOT_DIR/modul" "$ROOT_DIR/latihan" "$ROOT_DIR/kunci_jawaban" "$ROOT_DIR/penguji" \
      "$ROOT_DIR/cek_jawaban.py" "$ROOT_DIR/cek_jawaban_gui.py" "$ROOT_DIR/README.md" \
      "$WIN_STAGE/payload/"
cp -a "$ROOT_DIR/installer/sublime_bundle" "$WIN_STAGE/payload/installer/"
cp -a "$ROOT_DIR/installer/INSTALL_KODING_PENGGALANG.bat" "$WIN_STAGE/"
cp -a "$ROOT_DIR/installer/install-windows.ps1" "$WIN_STAGE/"
cp -a "$ROOT_DIR/installer/CARA_INSTALL.txt" "$WIN_STAGE/"
find "$WIN_STAGE" -name "__pycache__" -type d -exec rm -rf {} +

WIN_ZIP="$DIST_DIR/koding-penggalang-$VERSION-windows.zip"
python3 - "$WIN_STAGE" "$WIN_ZIP" <<'PY'
import pathlib, sys, zipfile
src = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in sorted(src.rglob("*")):
        if p.is_file():
            zf.write(p, p.relative_to(src))
PY

# 3. Paket Materi, Contoh Soal & Kunci Jawaban (tanpa installer Sublime — ringan untuk semua OS)
SOAL_STAGE="$STAGE_DIR/Paket-Soal-dan-Kunci-Jawaban-$VERSION"
mkdir -p "$SOAL_STAGE"
cp -a "$ROOT_DIR/modul" "$ROOT_DIR/latihan" "$ROOT_DIR/kunci_jawaban" "$ROOT_DIR/penguji" \
      "$ROOT_DIR/cek_jawaban.py" "$ROOT_DIR/cek_jawaban_gui.py" "$ROOT_DIR/README.md" \
      "$SOAL_STAGE/"
find "$SOAL_STAGE" -name "__pycache__" -type d -exec rm -rf {} +

SOAL_ZIP="$DIST_DIR/Paket-Soal-dan-Kunci-Jawaban-$VERSION.zip"
python3 - "$SOAL_STAGE" "$SOAL_ZIP" <<'PY'
import pathlib, sys, zipfile
src = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in sorted(src.rglob("*")):
        if p.is_file():
            zf.write(p, p.relative_to(src))
PY

# 4. Salin 3 file PDF langsung agar bisa diunduh 1-klik di halaman GitHub Release
cp -a "$ROOT_DIR/modul/01_Modul_Belajar_Pemrograman_dan_Python3_Penggalang.pdf" "$DIST_DIR/"
cp -a "$ROOT_DIR/modul/02_Referensi_Cepat_Sintaks_Python3_Saat_Lomba.pdf" "$DIST_DIR/"
cp -a "$ROOT_DIR/modul/03_Paket_Latihan_4_Soal_Lomba_Penggalang.pdf" "$DIST_DIR/"

# 5. Buat checksum SHA256
(cd "$DIST_DIR" && sha256sum *.run *.tar.gz *.zip *.pdf > SHA256SUMS.txt)

echo "==> Artefak rilis selesai dibuat di $DIST_DIR:"
ls -lh "$DIST_DIR"
