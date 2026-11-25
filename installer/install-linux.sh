#!/usr/bin/env bash
# ==============================================================================
# Installer 1-Klik Koding Penggalang untuk Linux (Debian/Ubuntu/Mint/Fedora/Arch)
# Memasang: Python 3, GTK 3 GUI, Ruff, Sublime Text 4 + Helper Python,
#           Modul PDF, Paket 4 Soal, Kunci Jawaban, CLI (cek) & GUI (cekgui).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/payload" ]; then
    SRC_ROOT="$SCRIPT_DIR/payload"
elif [ -f "$SCRIPT_DIR/cek_jawaban.py" ]; then
    SRC_ROOT="$SCRIPT_DIR"
else
    SRC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

INSTALL_DIR="${HOME}/koding-penggalang"
INSTALL_SUBLIME=1
ASSUME_YES=0

for arg in "$@"; do
    case "$arg" in
        --no-sublime) INSTALL_SUBLIME=0 ;;
        -y|--yes) ASSUME_YES=1 ;;
        --dir=*) INSTALL_DIR="${arg#*=}" ;;
        -h|--help)
            echo "Pemakaian: ./install-linux.sh [--no-sublime] [--yes] [--dir=/path/tujuan]"
            exit 0
            ;;
    esac
done

# Jika diklik dua kali dari file manager (tanpa terminal), buka terminal otomatis
if [ ! -t 0 ] && [ "$ASSUME_YES" -eq 0 ] && [ -n "${DISPLAY:-}" ]; then
    for term in lxterminal xfce4-terminal gnome-terminal konsole mate-terminal x-terminal-emulator xterm; do
        if command -v "$term" >/dev/null 2>&1; then
            case "$term" in
                gnome-terminal) exec "$term" -- bash "$0" "$@" ;;
                konsole|x-terminal-emulator|xterm) exec "$term" -e bash "$0" "$@" ;;
                *) exec "$term" -e "bash \"$0\" $*" ;;
            esac
        fi
    done
fi

GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

info()  { printf "${CYAN}[INFO]${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}[ OK ]${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
err()   { printf "${RED}[ERR ]${NC} %s\n" "$1"; }

echo "================================================================"
echo "   INSTALLER KODING PENGGALANG (LINUX) — PYTHON 3 + SUBLIME"
echo "================================================================"
echo "  Folder tujuan : $INSTALL_DIR"
echo "  Sublime Text  : $([ "$INSTALL_SUBLIME" -eq 1 ] && echo 'Ya (beserta Python Helper & Ruff)' || echo 'Lewati (--no-sublime)')"
echo "================================================================"
echo

# Deteksi package manager Linux
PKG_MGR="unknown"
if command -v apt-get >/dev/null 2>&1; then
    PKG_MGR="apt"
elif command -v dnf >/dev/null 2>&1; then
    PKG_MGR="dnf"
elif command -v pacman >/dev/null 2>&1; then
    PKG_MGR="pacman"
fi

run_sudo() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        warn "Hak akses sudo tidak tersedia untuk: $*"
        return 1
    fi
}

# 1. Pasang Python 3, GTK 3 PyGObject, dan pipx/pip
info "Memeriksa Python 3 dan dukungan GUI GTK 3..."
NEED_PY_GUI=0
if ! command -v python3 >/dev/null 2>&1; then
    NEED_PY_GUI=1
elif ! python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" >/dev/null 2>&1; then
    NEED_PY_GUI=1
fi

if [ "$NEED_PY_GUI" -eq 1 ]; then
    info "Memasang Python 3 & pustaka GUI GTK 3 ($PKG_MGR)..."
    case "$PKG_MGR" in
        apt)
            run_sudo apt-get update -qq || true
            run_sudo apt-get install -y python3 python3-pip python3-venv python3-gi gir1.2-gtk-3.0 pipx curl gpg || warn "Sebagian paket apt gagal dipasang."
            ;;
        dnf)
            run_sudo dnf install -y python3 python3-pip python3-gobject gtk3 pipx curl || warn "Sebagian paket dnf gagal dipasang."
            ;;
        pacman)
            run_sudo pacman -Sy --noconfirm --needed python python-pip python-gobject gtk3 python-pipx curl || warn "Sebagian paket pacman gagal dipasang."
            ;;
        *)
            warn "Distro Linux tidak dikenali otomatis. Pastikan python3 dan PyGObject/GTK3 sudah terpasang."
            ;;
    esac
fi
ok "Python 3 siap: $(python3 --version 2>/dev/null || echo 'tidak ditemukan')"

# 2. Pasang Sublime Text 4 (jika belum ada & diaktifkan)
if [ "$INSTALL_SUBLIME" -eq 1 ]; then
    if command -v subl >/dev/null 2>&1; then
        ok "Sublime Text sudah terpasang: $(command -v subl)"
    else
        info "Memasang Sublime Text 4 dari repositori resmi Sublime HQ..."
        case "$PKG_MGR" in
            apt)
                run_sudo apt-get install -y apt-transport-https ca-certificates curl gpg || true
                curl -fsSL https://download.sublimetext.com/sublimehq-pub.gpg | run_sudo gpg --dearmor -o /usr/share/keyrings/sublimehq-archive-keyring.gpg || true
                echo "deb [signed-by=/usr/share/keyrings/sublimehq-archive-keyring.gpg] https://download.sublimetext.com/ apt/stable/" | run_sudo tee /etc/apt/sources.list.d/sublime-text.list >/dev/null
                run_sudo apt-get update -qq && run_sudo apt-get install -y sublime-text || warn "Gagal memasang Sublime Text otomatis (cek koneksi internet)."
                ;;
            dnf)
                run_sudo rpm -v --import https://download.sublimetext.com/sublimehq-rpm-pub.gpg || true
                run_sudo dnf config-manager --add-repo https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo || true
                run_sudo dnf install -y sublime-text || warn "Gagal memasang Sublime Text otomatis."
                ;;
            pacman)
                curl -fsSL https://download.sublimetext.com/sublimehq-pub.gpg | run_sudo pacman-key --add - || true
                run_sudo pacman-key --lsign-key 8A8F901A || true
                if ! grep -q "\[sublime-text\]" /etc/pacman.conf; then
                    printf '\n[sublime-text]\nServer = https://download.sublimetext.com/arch/stable/$arch\n' | run_sudo tee -a /etc/pacman.conf >/dev/null
                fi
                run_sudo pacman -Syu --noconfirm sublime-text || warn "Gagal memasang Sublime Text otomatis."
                ;;
            *)
                warn "Pasang Sublime Text secara manual dari https://www.sublimetext.com/download"
                ;;
        esac
    fi

    # Pasang Ruff (linter & formatter offline)
    if ! command -v ruff >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/ruff" ]; then
        info "Memasang Ruff (pemeriksa & perapi kode Python offline)..."
        if command -v pipx >/dev/null 2>&1; then
            pipx install ruff || true
        else
            python3 -m pip install --user --break-system-packages ruff 2>/dev/null || python3 -m pip install --user ruff 2>/dev/null || warn "Ruff belum terpasang (butuh koneksi internet / pipx)."
        fi
    else
        ok "Ruff sudah tersedia."
    fi
fi

# 3. Salin seluruh paket Koding Penggalang (Modul PDF, Soal, Kunci, CLI, GUI)
info "Menyalin modul PDF, latihan soal, kunci jawaban, CLI & GUI ke $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
for item in modul latihan kunci_jawaban penguji cek_jawaban.py cek_jawaban_gui.py README.md; do
    if [ -e "$SRC_ROOT/$item" ]; then
        rm -rf "$INSTALL_DIR/$item"
        cp -a "$SRC_ROOT/$item" "$INSTALL_DIR/$item"
    fi
done
chmod +x "$INSTALL_DIR/cek_jawaban.py" "$INSTALL_DIR/cek_jawaban_gui.py"
ok "Paket Koding Penggalang terpasang di $INSTALL_DIR"

# 4. Pasang Helper Sublime Text + Runner Interaktif
mkdir -p "$HOME/.local/bin"
if [ "$INSTALL_SUBLIME" -eq 1 ] && [ -d "$SRC_ROOT/installer/sublime_bundle" ]; then
    info "Memasang konfigurasi Sublime Text Python Helper (F5/F6, Ctrl+., Shift+Alt+F)..."
    SUBL_USER="$HOME/.config/sublime-text/Packages/User"
    mkdir -p "$SUBL_USER"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/Adaptive.sublime-theme" "$SUBL_USER/"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/Default (Linux).sublime-keymap" "$SUBL_USER/"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/GitHub Dark Colorblind.sublime-color-scheme" "$SUBL_USER/"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/GitHub Dark.sublime-color-scheme" "$SUBL_USER/"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/Preferences.sublime-settings" "$SUBL_USER/"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/Python.sublime-settings" "$SUBL_USER/"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/python_ruff_helper.py" "$SUBL_USER/"
    cp -a "$SRC_ROOT/installer/sublime_bundle/User/PythonSnippets" "$SUBL_USER/"

    # Pasang py3-run & py3-run-interactive
    cp -a "$SRC_ROOT/installer/sublime_bundle/bin/py3-run" "$HOME/.local/bin/py3-run"
    cp -a "$SRC_ROOT/installer/sublime_bundle/bin/py3-run-interactive" "$HOME/.local/bin/py3-run-interactive"
    chmod +x "$HOME/.local/bin/py3-run" "$HOME/.local/bin/py3-run-interactive"

    # Deteksi terminal emulator yang terpasang untuk Python3.sublime-build
    TERM_BIN="xterm"
    for t in lxterminal xfce4-terminal gnome-terminal konsole mate-terminal x-terminal-emulator xterm; do
        if command -v "$t" >/dev/null 2>&1; then
            TERM_BIN="$t"
            break
        fi
    done

    cat > "$SUBL_USER/Python3.sublime-build" <<EOF
{
  "cmd": ["bash", "$HOME/.local/bin/py3-run", "\$file"],
  "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
  "selector": "source.python",
  "env": {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUNBUFFERED": "1"
  },
  "variants": [
    {
      "name": "Jalankan di Terminal Interaktif (untuk input() / Lomba)",
      "cmd": ["$TERM_BIN", "-e", "bash $HOME/.local/bin/py3-run-interactive \"\$file\""]
    },
    {
      "name": "Jalankan dengan Python 3 Sistem",
      "cmd": ["python3", "-u", "\$file"]
    }
  ]
}
EOF
    ok "Helper Sublime Text terpasang di $SUBL_USER"
fi

# 5. Pasang perintah global cek, cekall, cekgui
cat > "$HOME/.local/bin/cek" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/cek_jawaban.py" "\$@"
EOF
cat > "$HOME/.local/bin/cekall" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/cek_jawaban.py" all "\$@"
EOF
cat > "$HOME/.local/bin/cekgui" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/cek_jawaban_gui.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/cek" "$HOME/.local/bin/cekall" "$HOME/.local/bin/cekgui"

# Pastikan ~/.local/bin ada di PATH (.bashrc & .zshrc)
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rc" ]; then
        if ! grep -q '# Koding Penggalang PATH' "$rc"; then
            printf '\n# Koding Penggalang PATH\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
        fi
    fi
done
ok "Perintah terminal 'cek', 'cekall', dan 'cekgui' terpasang di ~/.local/bin"

# 6. Buat pintasan Menu Aplikasi & Desktop
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"
cat > "$APP_DIR/koding-penggalang-gui.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Penguji Koding Penggalang
Comment=Alat uji otomatis jawaban Lomba Coding Python Pramuka Penggalang
Exec=$HOME/.local/bin/cekgui
Icon=accessories-text-editor
Terminal=false
Categories=Education;Development;
StartupNotify=true
EOF

for dsk in "$HOME/Desktop" "$HOME/Dekstop"; do
    if [ -d "$dsk" ]; then
        cp -f "$APP_DIR/koding-penggalang-gui.desktop" "$dsk/Penguji-Koding-Penggalang.desktop"
        chmod +x "$dsk/Penguji-Koding-Penggalang.desktop" || true
        ln -sfn "$INSTALL_DIR/modul" "$dsk/Modul-PDF-Koding-Penggalang" || true
        break
    fi
done
ok "Pintasan Menu Aplikasi & Desktop selesai dibuat."

echo
echo "================================================================"
echo "  INSTALASI SELESAI 100%!"
echo "================================================================"
echo "  Folder Modul PDF : $INSTALL_DIR/modul/"
echo "  Folder Latihan   : $INSTALL_DIR/latihan/"
echo "  Kunci Jawaban    : $INSTALL_DIR/kunci_jawaban/"
echo "  Buka GUI Penguji : cekgui  (atau klik 'Penguji Koding Penggalang')"
echo "  Cek via Terminal : cek 1  |  cekall"
echo "================================================================"
if [ -t 0 ] && [ "$ASSUME_YES" -eq 0 ]; then
    read -r -p "Tekan Enter untuk menutup..."
fi
