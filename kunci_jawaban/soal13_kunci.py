# Kunci Jawaban Soal 13 — Simulasi Tali Pionering (Pemotongan & Sisa)
n, panjang_potong, target = map(int, input().split())
gulungan = list(map(int, input().split()))

total_potongan = 0
total_sisa = 0
for g in gulungan:
    total_potongan += g // panjang_potong
    total_sisa += g % panjang_potong

print(f"Potongan: {total_potongan}")
print(f"Sisa Tali: {total_sisa} cm")
if total_potongan >= target:
    print("Status: CUKUP")
else:
    print(f"Status: KURANG {target - total_potongan}")
