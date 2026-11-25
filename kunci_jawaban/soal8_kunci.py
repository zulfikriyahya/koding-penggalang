# Kunci Jawaban Soal 8 — Inventaris & Kekurangan Peralatan Regu
n = int(input())
butuh = {}
for _ in range(n):
    nama, jumlah = input().split()
    butuh[nama] = butuh.get(nama, 0) + int(jumlah)

m = int(input())
stok = {}
for _ in range(m):
    nama, jumlah = input().split()
    stok[nama] = stok.get(nama, 0) + int(jumlah)

kurang = []
for nama in sorted(butuh.keys()):
    selisih = butuh[nama] - stok.get(nama, 0)
    if selisih > 0:
        kurang.append((nama, selisih))

if not kurang:
    print("SEMUA LENGKAP")
else:
    for nama, selisih in kurang:
        print(f"{nama}: KURANG {selisih}")
