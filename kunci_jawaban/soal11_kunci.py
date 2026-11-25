# Kunci Jawaban Soal 11 — Penjadwalan Piket & Jaga Malam Perkemahan
jam_mulai, menit_mulai = map(int, input().strip().split(":"))
durasi = int(input())
n_anggota = int(input())
anggota = [input().strip() for _ in range(n_anggota)]
jumlah_shift = int(input())

mulai = jam_mulai * 60 + menit_mulai
for i in range(jumlah_shift):
    t1 = (mulai + i * durasi) % 1440
    t2 = (mulai + (i + 1) * durasi) % 1440
    nama = anggota[i % n_anggota]
    print(f"Shift {i + 1}: {t1 // 60:02d}:{t1 % 60:02d}-{t2 // 60:02d}:{t2 % 60:02d} - {nama}")
