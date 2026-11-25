# Kunci Jawaban Soal 10 — Sandi Geser (Caesar) Multi-Baris
mode = input().strip().upper()
k = int(input())
n = int(input())

geser = k if mode == "ENKRIPSI" else -k

for _ in range(n):
    baris = input()
    keluaran = []
    for ch in baris:
        if "A" <= ch <= "Z":
            keluaran.append(chr((ord(ch) - ord("A") + geser) % 26 + ord("A")))
        elif "a" <= ch <= "z":
            keluaran.append(chr((ord(ch) - ord("a") + geser) % 26 + ord("a")))
        else:
            keluaran.append(ch)
    print("".join(keluaran))
