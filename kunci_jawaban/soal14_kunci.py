# Kunci Jawaban Soal 14 — Jejak Langkah Penjelajahan (Koordinat & Jarak)
import math

n = int(input())
x, y = 0, 0
for _ in range(n):
    arah, langkah_str = input().split()
    arah = arah.upper()
    langkah = int(langkah_str)
    if arah == "U":
        y += langkah
    elif arah == "S":
        y -= langkah
    elif arah == "T":
        x += langkah
    elif arah == "B":
        x -= langkah

manhattan = abs(x) + abs(y)
lurus = math.hypot(x, y)

print(f"Posisi: ({x}, {y})")
print(f"Jarak Langkah: {manhattan}")
print(f"Jarak Lurus: {lurus:.2f}")
