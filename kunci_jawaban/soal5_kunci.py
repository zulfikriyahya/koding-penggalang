# Kunci Jawaban Soal 5 — Penerjemah Sandi AN & Sandi AZ
mode = input().strip().upper()
teks = input().strip()

hasil = []
for ch in teks:
    if "A" <= ch <= "Z":
        if mode == "AN":
            hasil.append(chr((ord(ch) - ord("A") + 13) % 26 + ord("A")))
        else:
            hasil.append(chr(ord("Z") - (ord(ch) - ord("A"))))
    elif "a" <= ch <= "z":
        if mode == "AN":
            hasil.append(chr((ord(ch) - ord("a") + 13) % 26 + ord("a")))
        else:
            hasil.append(chr(ord("z") - (ord(ch) - ord("a"))))
    else:
        hasil.append(ch)

print("".join(hasil))
