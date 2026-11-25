# Kunci Jawaban Soal 16 — Optimasi Isi Ransel Perkemahan (Greedy Prioritas)
kapasitas, n = map(int, input().split())
barang = []
for _ in range(n):
    nama, berat_s, prio_s = input().split()
    barang.append((nama, int(berat_s), int(prio_s)))

# Urutkan: prioritas tertinggi, lalu berat paling ringan, lalu nama A-Z
barang.sort(key=lambda b: (-b[2], b[1], b[0]))

terpilih = []
total_berat = 0
total_prio = 0
for nama, berat, prio in barang:
    if total_berat + berat <= kapasitas:
        terpilih.append(nama)
        total_berat += berat
        total_prio += prio

if terpilih:
    print("Dibawa: " + ", ".join(terpilih))
else:
    print("Dibawa: TIDAK ADA")
print(f"Total Berat: {total_berat} kg")
print(f"Total Prioritas: {total_prio}")
