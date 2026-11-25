# Kunci Jawaban Soal 7 — Peta Perjalanan & Estimasi Waktu Tiba Pos
import math

jam_awal, menit_awal = map(int, input().strip().split(":"))
n = int(input())

total_jarak_m = 0
total_menit = 0
for _ in range(n):
    jarak_m, kecepatan, istirahat = map(int, input().split())
    total_jarak_m += jarak_m
    total_menit += math.ceil(jarak_m / kecepatan) + istirahat

waktu_tiba = (jam_awal * 60 + menit_awal + total_menit) % 1440
jam_tiba = waktu_tiba // 60
menit_tiba = waktu_tiba % 60

print(f"Jarak: {total_jarak_m / 1000:.2f} km")
print(f"Durasi: {total_menit} menit")
print(f"Tiba: {jam_tiba:02d}:{menit_tiba:02d}")
