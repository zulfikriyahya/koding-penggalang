# Kunci Jawaban Soal 1 — Kompas, Azimuth & Back Azimuth


def nama_arah(sudut: int) -> str:
    if sudut <= 22 or sudut >= 338:
        return "Utara"
    if sudut <= 67:
        return "Timur Laut"
    if sudut <= 112:
        return "Timur"
    if sudut <= 157:
        return "Tenggara"
    if sudut <= 202:
        return "Selatan"
    if sudut <= 247:
        return "Barat Daya"
    if sudut <= 292:
        return "Barat"
    return "Barat Laut"


def main() -> None:
    sudut = int(input()) % 360
    n = int(input())
    for _ in range(n):
        arah, derajat_str = input().split()
        derajat = int(derajat_str)
        if arah.upper() == "KANAN":
            sudut = (sudut + derajat) % 360
        else:
            sudut = (sudut - derajat) % 360

    back_azimuth = sudut + 180 if sudut < 180 else sudut - 180
    print(f"Azimuth: {sudut} ({nama_arah(sudut)})")
    print(f"Back Azimuth: {back_azimuth}")


if __name__ == "__main__":
    main()
