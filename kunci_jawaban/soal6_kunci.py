# Kunci Jawaban Soal 6 — Menaksir Tinggi Pohon (Metode Bayangan)
t_tongkat, b_tongkat, b_pohon = map(float, input().split())

if b_tongkat <= 0 or t_tongkat <= 0 or b_pohon <= 0:
    print("TIDAK VALID")
else:
    tinggi = (t_tongkat * b_pohon) / b_tongkat
    if tinggi < 5.0:
        kategori = "RENDAH"
    elif tinggi <= 15.0:
        kategori = "SEDANG"
    else:
        kategori = "TINGGI"
    print(f"Tinggi: {tinggi:.2f} m")
    print(f"Kategori: {kategori}")
