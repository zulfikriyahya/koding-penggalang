# Kunci Jawaban Soal 15 — Penerjemah Posisi Bendera Semaphore Resmi (7 Lingkaran)
SEMAPHORE = {
    (0, 1): "A", (0, 2): "B", (0, 3): "C", (0, 4): "D", (0, 5): "E", (0, 6): "F", (0, 7): "G",
    (1, 2): "H", (1, 3): "I", (1, 4): "K", (1, 5): "L", (1, 6): "M", (1, 7): "N",
    (2, 3): "O", (2, 4): "P", (2, 5): "Q", (2, 6): "R", (2, 7): "S",
    (3, 4): "T", (3, 5): "U", (3, 6): "Y",
    (4, 6): "J", (4, 7): "V",
    (5, 6): "W", (5, 7): "X",
    (6, 7): "Z",
}

baris = input().strip()
kata_list = baris.split("/")
hasil_kata = []

for kata in kata_list:
    huruf_kata = []
    for kode in kata.split():
        bagian = kode.split("-")
        if len(bagian) == 2 and bagian[0].isdigit() and bagian[1].isdigit():
            a, b = int(bagian[0]), int(bagian[1])
            pasangan = (min(a, b), max(a, b))
            huruf_kata.append(SEMAPHORE.get(pasangan, "?"))
        else:
            huruf_kata.append("?")
    hasil_kata.append("".join(huruf_kata))

print(" ".join(hasil_kata))
