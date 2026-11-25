# Koding Penggalang — Modul, Installer & Penguji Lomba Coding Python 3 (SMP/MTs)

Paket lengkap belajar mandiri, latihan simulasi, installer 1-klik (**Linux & Windows**), serta alat penguji otomatis **CLI & GUI** untuk persiapan **Lomba Coding Python Pramuka Penggalang** (usia 11–15 tahun / jenjang SMP–MTs) di Indonesia.

Disusun secara faktual berdasarkan:
- Petunjuk Teknis (Juknis) Lomba Coding Python Penggalang
- **SK Kwarnas Gerakan Pramuka No. 198 Tahun 2011** (SKU Penggalang: Kompas, 16 Arah Mata Angin, Azimuth/Back Azimuth, Sandi, Morse Internasional, Semaphore, dan Lomba Tingkat)
- **Kurikulum Merdeka Informatika Fase D (SMP/MTs)** Kemendikbudristek
- **Bebras Indonesia** kategori Penggalang
- **Dokumentasi Resmi Python 3** (Python Software Foundation)

---

## Unduh & Pasang 1-Klik (GitHub Releases)

Buka halaman **[Releases (`v1.0.0`)](https://github.com/zulfikriyahya/koding-penggalang/releases/latest)** untuk mengunduh:

### 1. Installer Lengkap 1-Bundle (Python 3 + Sublime Text 4 + Helper Python + Modul PDF + Soal + Kunci + Penguji CLI & GUI)
- **Windows 10 / 11:** Unduh `koding-penggalang-v1.0.0-windows.zip` → ekstrak → klik dua kali **`INSTALL_KODING_PENGGALANG.bat`**.
- **Linux (Debian / Ubuntu / Mint / Fedora / Arch):** Unduh `KodingPenggalang-Installer-Linux-v1.0.0.run` (atau `koding-penggalang-v1.0.0-linux.tar.gz`) lalu jalankan:
  ```bash
  chmod +x KodingPenggalang-Installer-Linux-v1.0.0.run
  ./KodingPenggalang-Installer-Linux-v1.0.0.run
  ```
  *(Tambahkan `--no-sublime` di Linux atau `-NoSublime` di PowerShell jika hanya ingin memasang modul & penguji tanpa Sublime Text.)*

### 2. Unduh Langsung PDF, Contoh Soal & Kunci Jawaban (Tanpa Installer)
Di halaman **[Releases](https://github.com/zulfikriyahya/koding-penggalang/releases/latest)** tersedia langsung file siap unduh:
- `01_Modul_Belajar_Pemrograman_dan_Python3_Penggalang.pdf` *(7 halaman A4)*
- `02_Referensi_Cepat_Sintaks_Python3_Saat_Lomba.pdf` *(2 halaman A4 bolak-balik)*
- `03_Paket_Latihan_4_Soal_Lomba_Penggalang.pdf` *(2 halaman A4)*
- `Paket-Soal-dan-Kunci-Jawaban-v1.0.0.zip` *(semua PDF + HTML + template `latihan/` + `kunci_jawaban/` + penguji offline)*

---

## Struktur Proyek

```text
koding-penggalang/
├── modul/
│   ├── 01_Modul_Belajar_Pemrograman_dan_Python3_Penggalang.pdf   (7 hal. A4)
│   ├── 01_Modul_Belajar_Pemrograman_dan_Python3_Penggalang.html
│   ├── 02_Referensi_Cepat_Sintaks_Python3_Saat_Lomba.pdf         (2 hal. A4)
│   ├── 02_Referensi_Cepat_Sintaks_Python3_Saat_Lomba.html
│   ├── 03_Paket_Latihan_4_Soal_Lomba_Penggalang.pdf              (2 hal. A4)
│   └── 03_Paket_Latihan_4_Soal_Lomba_Penggalang.html
├── latihan/                  # Template file jawaban siswa (soal1_ELANG.py .. soal4_ELANG.py)
├── kunci_jawaban/            # Kunci jawaban terverifikasi 100% (soal1_kunci.py .. soal4_kunci.py)
├── penguji/
│   └── core.py               # Mesin penguji offline (20 kasus uji + validator Juknis AST)
├── installer/                # Installer 1-klik Linux & Windows + konfigurasi Sublime Text Python Helper
├── cek_jawaban.py            # Penguji otomatis lewat terminal (CLI)
└── cek_jawaban_gui.py        # Aplikasi penguji grafis desktop (GTK 3 Linux + Tkinter Windows)
```

---

## Paket 4 Soal Simulasi (120 Menit · Skor 0–100)

| Soal | Topik Kepramukaan | Tingkat | Bobot |
|---|---|---|---|
| **Soal 1** | Kompas, Azimuth, Back Azimuth & 8 Arah Mata Angin | Mudah | 25% |
| **Soal 2** | Logistik Tenda & Kebutuhan Air Perkemahan | Mudah–Menengah | 25% |
| **Soal 3** | Penerjemah Sandi Morse Internasional (`A`–`Z`, `0`–`9`) | Menengah | 25% |
| **Soal 4** | Klasemen Lomba Tingkat (LT) Penggalang | Menantang | 25% |

> **Aturan Penting Juknis:** Semua pemanggilan `input()` **wajib kosong** tanpa teks di dalam tanda kurung (tulis `x = input()`, bukan `x = input("Masukkan: ")`). Penguji otomatis akan langsung memberi peringatan jika aturan ini terlanggar.

---

## Cara Menggunakan Penguji Otomatis

### 1. Mode Terminal (CLI)
```bash
cek soal1_ELANG.py        # Uji 1 file jawaban (deteksi nomor soal otomatis)
cek 1                     # Uji cepat Soal 1 (atau 2, 3, 4)
cek 3 jawaban_morse.py    # Uji file dengan nomor soal manual
cekall                    # Uji semua soal 1–4 + rekap skor 0–100
cek folder_tim/           # Uji seluruh jawaban 1 tim + rekap skor 0–100
```

### 2. Mode Aplikasi Desktop (GUI — Linux GTK 3 & Windows Tkinter)
```bash
cekgui
```
Atau klik pintasan Desktop **"Penguji Koding Penggalang"** yang dibuat otomatis oleh installer.

---

## Lisensi & Penggunaan
Bebas digunakan, dicetak, dan dimodifikasi untuk keperluan latihan ekstrakurikuler Pramuka Penggalang, pembinaan Informatika SMP/MTs, dan simulasi lomba koding di Indonesia.
