# Kunci Jawaban Soal 12 — Rekap Juara Umum Lomba Tingkat (Penalti & Diskualifikasi)
n = int(input())
lolos = []
diskualifikasi = []

for _ in range(n):
    bagian = input().split()
    nama = bagian[0]
    pbb, pionering, sandi, p3k = map(int, bagian[1:5])
    telat = int(bagian[5])
    pelanggaran = bagian[6].upper()

    if pelanggaran == "YA":
        diskualifikasi.append(nama)
    else:
        rata = (pbb + pionering + sandi + p3k) / 4.0
        skor = max(0.0, rata - 0.5 * telat)
        lolos.append((nama, skor, sandi))

lolos.sort(key=lambda r: (-round(r[1], 6), -r[2], r[0]))
diskualifikasi.sort()

for idx, (nama, skor, _sandi) in enumerate(lolos, start=1):
    print(f"{idx}. {nama} - {skor:.2f}")

for nama in diskualifikasi:
    print(f"DISKUALIFIKASI: {nama}")
