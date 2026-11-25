# Kunci Jawaban Soal 2 — Logistik Tenda & Air Perkemahan
import math


def main() -> None:
    bagian = input().split()
    p = int(bagian[0])
    k = int(bagian[1])
    h = int(bagian[2])
    stok = float(bagian[3])

    tenda = math.ceil(p / k)
    butuh_air = p * 2.5 * h

    print(f"Tenda: {tenda}")
    print(f"Air: {butuh_air:.2f} L")
    if stok + 1e-9 >= butuh_air:
        print("Status: CUKUP")
    else:
        selisih = butuh_air - stok
        print(f"Status: KURANG {selisih:.2f} L")


if __name__ == "__main__":
    main()
