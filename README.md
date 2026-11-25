# Koding Penggalang — Modul & Penguji Lomba Coding Python 3 (SMP/MTs)

Paket lengkap belajar mandiri, latihan simulasi, dan alat penguji otomatis **CLI & GUI** untuk persiapan **Lomba Coding Python Pramuka Penggalang** (usia 11–15 tahun / jenjang SMP–MTs) di Indonesia.

Disusun secara faktual berdasarkan:
- Petunjuk Teknis (Juknis) Lomba Coding Python Penggalang
- **SK Kwarnas Gerakan Pramuka No. 198 Tahun 2011** (SKU Penggalang: Kompas, 16 Arah Mata Angin, Azimuth/Back Azimuth, Sandi, Morse Internasional, Semaphore, dan Lomba Tingkat)
- **Kurikulum Merdeka Informatika Fase D (SMP/MTs)** Kemendikbudristek
- **Bebras Indonesia** kategori Penggalang
- **Dokumentasi Resmi Python 3** (Python Software Foundation)

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
│   └── core.py               # Mesin penguji offline (20 kasus uji + validator Juknis)
├── cek_jawaban.py            # Penguji otomatis lewat terminal (CLI)
└── cek_jawaban_gui.py        # Aplikasi penguji grafis desktop (GTK 3 GUI)
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
# Uji 1 file jawaban
python3 cek_jawaban.py latihan/soal1_ELANG.py

# Uji 1 nomor soal cepat (1, 2, 3, atau 4)
python3 cek_jawaban.py 1

# Uji file dengan nomor soal manual (jika nama file tidak memuat 'soalN')
python3 cek_jawaban.py --soal 3 jawaban_morse.py

# Uji seluruh folder siswa sekaligus (rekap nilai 0–100)
python3 cek_jawaban.py latihan/
python3 cek_jawaban.py kunci_jawaban/
```

### 2. Mode Aplikasi Desktop (GUI — GTK 3)

Cocok untuk pembina maupun siswa agar bisa menguji file atau folder jawaban dengan satu klik, melihat status setiap kasus uji, serta membandingkan **Output Siswa** dan **Kunci Jawaban** secara berdampingan:

```bash
python3 cek_jawaban_gui.py
```

### Kebutuhan Sistem
- **Python 3.10+** (tanpa dependensi eksternal untuk mode CLI)
- **PyGObject / GTK 3** (`python3-gi`, `gir1.2-gtk-3.0`) untuk mode GUI di Linux

---

## Lisensi & Penggunaan
Bebas digunakan, dicetak, dan dimodifikasi untuk keperluan latihan ekstrakurikuler Pramuka Penggalang, pembinaan Informatika SMP/MTs, dan simulasi lomba koding di Indonesia.
