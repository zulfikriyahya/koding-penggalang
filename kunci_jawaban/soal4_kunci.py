# Kunci Jawaban Soal 4 — Klasemen Lomba Tingkat (LT) Penggalang


def main() -> None:
    n = int(input())
    regu = []
    for _ in range(n):
        nama, pbb_s, pio_s, sem_s = input().split()
        pbb = int(pbb_s)
        pio = int(pio_s)
        sem = int(sem_s)
        total_x10 = 3 * pbb + 4 * pio + 3 * sem
        nilai_akhir = total_x10 / 10.0
        regu.append((nama, total_x10, pio, nilai_akhir))

    regu.sort(key=lambda r: (-r[1], -r[2], r[0]))
    for idx, (nama, _tx10, _pio, nilai) in enumerate(regu, start=1):
        print(f"{idx}. {nama} - {nilai:.2f}")


if __name__ == "__main__":
    main()
