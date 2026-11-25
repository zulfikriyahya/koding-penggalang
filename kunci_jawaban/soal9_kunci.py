# Kunci Jawaban Soal 9 — Penerjemah Sandi Angka Pramuka
teks = input().strip().replace("-", " ")
token_list = teks.split()

hasil = []
for tok in token_list:
    if tok.isdigit():
        angka = int(tok)
        if angka == 0:
            hasil.append(" ")
        elif 1 <= angka <= 26:
            hasil.append(chr(ord("A") + angka - 1))
        else:
            hasil.append("?")
    else:
        hasil.append("?")

print("".join(hasil))
