"""Biến metadata của COUGHVID thành file nhãn `nhan_tieng_ho.csv`.

Vì sao cần file này?
--------------------
COUGHVID không cho sẵn file "filename,label" mà `huan_luyen_tieng_ho.py` cần. Nó
cho một file `metadata_compiled.csv` với rất nhiều cột, trong đó có phần các bác
sĩ hô hấp nghe rồi gán nhãn (cột `diagnosis_1`, `diagnosis_2`, ...). Script này
đọc phần đó và tạo ra nhãn nhị phân: 0 = ho bình thường, 1 = ho bất thường.

QUY TẮC GÁN NHÃN (em phải HIỂU và bảo vệ được quy tắc này):
    - Với mỗi đoạn ghi, gom tất cả chẩn đoán của các chuyên gia đã nghe nó.
    - Nếu KHÔNG chuyên gia nào nghe → bỏ qua (chỉ dùng đoạn có nhãn chuyên gia,
      không dùng nhãn tự khai — vì nhãn tự khai kém tin cậy hơn nhiều).
    - "Bình thường" = chẩn đoán 'healthy_cough'. Mọi chẩn đoán khác = "bất thường".
    - Lấy theo ĐA SỐ chuyên gia. Nếu số phiếu HÒA (các bác sĩ bất đồng 50-50) →
      BỎ QUA đoạn đó, vì chính "đáp án đúng" cũng không rõ ràng.

Điểm quan trọng để phản biện: script ĐẾM số đoạn mà các chuyên gia BẤT ĐỒNG với
nhau. Con số này cho thấy ngay cả bác sĩ nghe cùng một tiếng ho cũng không luôn
thống nhất — nghĩa là không nên kỳ vọng mô hình đạt độ chính xác cao. Đây là một
điểm trung thực rất giá trị, hãy đưa vào báo cáo.

CÁCH DÙNG:
    1. Tải và giải nén COUGHVID. Đặt `metadata_compiled.csv` cạnh file này, và
       tất cả file âm thanh (.webm/.ogg) vào thư mục `du_lieu_ho/`.
    2. python chuan_bi_coughvid.py
    3. Kiểm tra `nhan_tieng_ho.csv` sinh ra, rồi: python huan_luyen_tieng_ho.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tieng_viet import bat_tieng_viet

FILE_METADATA = "metadata_compiled.csv"
THU_MUC_AUDIO = "du_lieu_ho"
FILE_NHAN = "nhan_tieng_ho.csv"

NGUONG_HO = 0.8  # chỉ lấy đoạn mà bộ dò của COUGHVID chắc chắn >=80% là tiếng ho
CHAN_DOAN_BINH_THUONG = "healthy_cough"  # mọi chẩn đoán khác coi là bất thường
DUOI_FILE = (".webm", ".ogg", ".wav")  # COUGHVID lưu .webm hoặc .ogg tùy trình duyệt


def tim_cot_chan_doan(metadata: pd.DataFrame) -> list[str]:
    """Tìm các cột chẩn đoán của chuyên gia: diagnosis_1, diagnosis_2, ..."""
    return [c for c in metadata.columns if c.lower().startswith("diagnosis")]


def nhan_tu_chuyen_gia(dong, cot_chan_doan):
    """Gán nhãn 0/1 cho một đoạn dựa trên chẩn đoán các chuyên gia.

    Trả về:
        0  = bình thường (đa số chuyên gia nói healthy_cough)
        1  = bất thường (đa số nói khác)
        None = không dùng được (không có chuyên gia nào, hoặc hòa phiếu)
    """
    chan_doan = [
        str(dong[c]).strip()
        for c in cot_chan_doan
        if pd.notna(dong[c]) and str(dong[c]).strip() != ""
    ]
    if not chan_doan:
        return None  # không có nhãn chuyên gia

    so_binh_thuong = sum(cd == CHAN_DOAN_BINH_THUONG for cd in chan_doan)
    so_bat_thuong = len(chan_doan) - so_binh_thuong

    if so_bat_thuong > so_binh_thuong:
        return 1
    if so_binh_thuong > so_bat_thuong:
        return 0
    return None  # hòa phiếu → chuyên gia bất đồng → bỏ qua


def tim_file_am_thanh(thu_muc: Path, uuid: str):
    """Tìm file âm thanh của một uuid (thử các đuôi .webm/.ogg/.wav)."""
    for duoi in DUOI_FILE:
        p = thu_muc / f"{uuid}{duoi}"
        if p.exists():
            return p.name
    return None


def main():
    bat_tieng_viet()

    meta_path = Path(FILE_METADATA)
    thu_muc = Path(THU_MUC_AUDIO)

    if not meta_path.exists():
        raise SystemExit(
            f"Không thấy {FILE_METADATA}. Hãy tải COUGHVID, giải nén, và đặt file "
            f"metadata_compiled.csv cạnh script này."
        )
    if not thu_muc.exists():
        raise SystemExit(
            f"Không thấy thư mục {THU_MUC_AUDIO}/. Hãy đặt các file âm thanh COUGHVID "
            f"(.webm/.ogg) vào đó."
        )

    metadata = pd.read_csv(meta_path)
    print(f"Đọc metadata: {len(metadata)} dòng, {len(metadata.columns)} cột.")

    cot_uuid = "uuid" if "uuid" in metadata.columns else metadata.columns[0]
    print(f"Cột định danh dùng: '{cot_uuid}'")

    cot_chan_doan = tim_cot_chan_doan(metadata)
    if not cot_chan_doan:
        raise SystemExit(
            "Không tìm thấy cột chẩn đoán chuyên gia (diagnosis_1, ...). File "
            "metadata này có thể là bản không kèm nhãn chuyên gia. Cần bản "
            "metadata_compiled.csv đầy đủ của COUGHVID."
        )
    print(f"Cột chẩn đoán chuyên gia: {cot_chan_doan}")

    co_cot_ho = "cough_detected" in metadata.columns
    if not co_cot_ho:
        print("(Không có cột cough_detected — bỏ qua bước lọc theo độ tin cậy tiếng ho.)")

    cac_dong = []
    dem = {"binh_thuong": 0, "bat_thuong": 0}
    bo_khong_nhan = bo_hoa = bo_thieu_ho = bo_khong_file = 0

    for _, dong in metadata.iterrows():
        # Lọc: đoạn phải thật sự là tiếng ho.
        if co_cot_ho and pd.notna(dong["cough_detected"]):
            if float(dong["cough_detected"]) < NGUONG_HO:
                bo_thieu_ho += 1
                continue

        nhan = nhan_tu_chuyen_gia(dong, cot_chan_doan)
        if nhan is None:
            # phân biệt: không có chuyên gia nào vs hòa phiếu
            co_chuyen_gia = any(
                pd.notna(dong[c]) and str(dong[c]).strip() != "" for c in cot_chan_doan
            )
            if co_chuyen_gia:
                bo_hoa += 1
            else:
                bo_khong_nhan += 1
            continue

        ten_file = tim_file_am_thanh(thu_muc, str(dong[cot_uuid]))
        if ten_file is None:
            bo_khong_file += 1
            continue

        cac_dong.append({"filename": ten_file, "label": nhan})
        dem["binh_thuong" if nhan == 0 else "bat_thuong"] += 1

    if not cac_dong:
        raise SystemExit(
            "Không tạo được dòng nhãn nào. Kiểm tra: file âm thanh đã ở trong "
            f"{THU_MUC_AUDIO}/ chưa, và tên file có khớp uuid không."
        )

    df = pd.DataFrame(cac_dong)
    df.to_csv(FILE_NHAN, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print("ĐÃ TẠO FILE NHÃN")
    print("=" * 60)
    print(f"  Tổng số đoạn dùng được:      {len(df)}")
    print(f"    - Ho bình thường (0):      {dem['binh_thuong']}")
    print(f"    - Ho bất thường (1):       {dem['bat_thuong']}")
    print(f"\n  Bỏ qua vì không có nhãn chuyên gia: {bo_khong_nhan}")
    print(f"  Bỏ qua vì CHUYÊN GIA BẤT ĐỒNG (hòa): {bo_hoa}   <-- con số đáng bàn!")
    print(f"  Bỏ qua vì không chắc là tiếng ho:    {bo_thieu_ho}")
    print(f"  Bỏ qua vì không tìm thấy file:       {bo_khong_file}")
    print("=" * 60)
    print(f"Đã lưu: {FILE_NHAN}")

    if bo_hoa:
        print(
            f"\nGHI VÀO BÁO CÁO: có {bo_hoa} đoạn mà các chuyên gia không thống nhất "
            f"với nhau.\nĐiều này cho thấy 'đáp án đúng' của bài toán vốn đã không "
            f"chắc chắn — một lý do\nchính đáng để mô hình không thể đạt độ chính xác cao."
        )
    if dem["binh_thuong"] and dem["bat_thuong"]:
        ty_le = min(dem.values()) / max(dem.values())
        if ty_le < 0.3:
            print(
                f"\nLƯU Ý: hai lớp lệch nhau nhiều ({dem}). Mô hình đã dùng "
                f"class_weight='balanced' để bù, nhưng hãy nhìn RECALL từng lớp "
                f"khi đánh giá, đừng chỉ nhìn accuracy."
            )


if __name__ == "__main__":
    main()
