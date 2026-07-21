"""Huấn luyện + đánh giá mô hình phân loại TIẾNG HO (một module RIÊNG).

================================================================================
ĐỌC KỸ — TÍNH TRUNG THỰC
================================================================================
Module này trả lời một câu hỏi HẸP và RIÊNG: "Chỉ nghe tiếng ho thôi, máy có
phân biệt được ho của người khỏe với ho bất thường không?"

Nó KHÔNG nối vào điểm nguy cơ của hệ thống chính (hệ thống chính dùng SpO2, nhịp
thở, triệu chứng). Đây là một thí nghiệm đứng riêng, và phải báo cáo riêng.

DỰ BÁO TRƯỚC KẾT QUẢ: nhiều khả năng chỉ ở mức TRUNG BÌNH, không cao. Sau đợt
2020–2021 rộ lên chuyện "chẩn đoán COVID qua tiếng ho", nhiều nghiên cứu lớn hơn
chỉ ra các mô hình này hoạt động kém khi đổi sang dữ liệu khác — chúng thường
học "đặc điểm của bộ dữ liệu" (micro, cách thu, phông nền) chứ không phải học
bệnh. PHẢI ghi đúng con số đo được, kể cả khi nó không đẹp. Một kết quả khiêm
tốn được báo cáo trung thực có giá trị khoa học hơn một con số đẹp gây hiểu lầm.

================================================================================
CÁCH DÙNG
================================================================================
Bước 1 — Kiểm tra pipeline chạy đúng (KHÔNG cần dữ liệu thật):
    python huan_luyen_tieng_ho.py --tu-kiem

Bước 2 — Lấy dữ liệu ho công khai (chạy trên máy của em, tải vài GB, KHÔNG làm
         trong lúc trình bày vì nặng và lâu):
    - Coswara (file .wav, KHÔNG cần cài thêm gì):
        https://github.com/iiscleap/Coswara-Data
    - COUGHVID (file .webm — phải cài thêm ffmpeg để đọc được):
        https://zenodo.org/records/7024894

Bước 3 — Tạo file nhãn `nhan_tieng_ho.csv` gồm 2 cột:
        filename,label
        ho_001.wav,0        <- 0 = ho của người KHỎE
        ho_002.wav,1        <- 1 = ho BẤT THƯỜNG (có triệu chứng / bệnh)
    Đặt các file .wav vào thư mục `du_lieu_ho/`.

Bước 4 — Huấn luyện thật:
    python huan_luyen_tieng_ho.py

Mô hình dùng Random Forest trên 35 đặc trưng âm thanh (MFCC...) — CÙNG loại mô
hình với hệ thống chính, để em giải thích được. KHÔNG dùng deep learning: với
lượng dữ liệu này, mạng nơ-ron dễ overfit và trở thành hộp đen không giải thích
được — không phù hợp đề tài.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from health_core import expected_calibration_error, fit_calibrated
from health_core.audio import FEATURE_NAMES, extract_features_from_array

from tieng_viet import bat_tieng_viet

THU_MUC_AUDIO = "du_lieu_ho"
FILE_NHAN = "nhan_tieng_ho.csv"
FILE_MO_HINH = "mo_hinh_tieng_ho.joblib"
FILE_KET_QUA = "ket_qua_tieng_ho.csv"
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# ĐỌC DỮ LIỆU THẬT
# ---------------------------------------------------------------------------

def doc_du_lieu_that(thu_muc=THU_MUC_AUDIO, file_nhan=FILE_NHAN):
    """Đọc file nhãn + trích đặc trưng cho từng file .wav trong thư mục.

    Trả về (X: DataFrame đặc trưng, y: mảng nhãn 0/1).
    """
    from health_core.audio import extract_features

    thu_muc = Path(thu_muc)
    file_nhan = Path(file_nhan)

    if not file_nhan.exists():
        raise SystemExit(
            f"Không thấy file nhãn {file_nhan}.\n"
            f"Hãy tạo file CSV 2 cột (filename,label) — xem hướng dẫn đầu file này."
        )

    nhan = pd.read_csv(file_nhan)
    if not {"filename", "label"}.issubset(nhan.columns):
        raise SystemExit("File nhãn phải có đúng 2 cột: filename,label")

    cac_dong = []
    y = []
    loi = 0
    tong = len(nhan)
    for i, (_, dong) in enumerate(nhan.iterrows(), start=1):
        duong_dan = thu_muc / str(dong["filename"])
        try:
            dt = extract_features(duong_dan)
            cac_dong.append(dt)
            y.append(int(dong["label"]))
        except Exception as e:
            loi += 1
            if loi <= 5:
                print(f"  Bỏ qua {dong['filename']}: {e}")
        if i % 50 == 0 or i == tong:
            print(f"  Đã xử lý {i}/{tong} file...", flush=True)

    if not cac_dong:
        raise SystemExit(
            "Không đọc được file âm thanh nào. Nếu dùng COUGHVID (.webm), phải cài "
            "ffmpeg. Nếu dùng Coswara (.wav) thì không cần."
        )
    if loi:
        print(f"  (Đã bỏ qua tổng cộng {loi} file lỗi.)")

    X = pd.DataFrame(cac_dong, columns=list(FEATURE_NAMES))
    return X, np.array(y)


# ---------------------------------------------------------------------------
# TỰ KIỂM: sinh âm thanh giả để kiểm tra pipeline chạy đúng
# ---------------------------------------------------------------------------

def sinh_du_lieu_tu_kiem(so_moi_lop=60, tan_so=22050):
    """Sinh 2 lớp âm thanh KHÁC NHAU THẬT về tần số, để kiểm tra pipeline.

    Đây KHÔNG phải dữ liệu ho thật và KHÔNG phải kết quả khoa học. Mục đích duy
    nhất: chứng minh cả chuỗi (trích đặc trưng → train → hiệu chuẩn → đánh giá →
    lưu → nạp → dự đoán) chạy đúng, và mô hình HỌC ĐƯỢC khi tín hiệu thật sự khác
    nhau. Nếu ngay cả bài toán dễ này mà mô hình cũng không học được thì code sai.

    Lớp 0: tiếng trầm (200–500 Hz). Lớp 1: tiếng cao (2000–4000 Hz).
    """
    rng = np.random.default_rng(RANDOM_STATE)
    t = np.linspace(0, 1.2, int(1.2 * tan_so), endpoint=False)
    cac_dong, y = [], []

    for lop, (f_thap, f_cao) in enumerate([(200, 500), (2000, 4000)]):
        for _ in range(so_moi_lop):
            f = rng.uniform(f_thap, f_cao)
            bao = np.exp(-3 * ((t % 0.3) / 0.3))  # các "cơn" bật lên rồi tắt dần
            song = np.sin(2 * np.pi * f * t) * bao
            song += rng.normal(0, 0.05, song.shape)  # thêm nhiễu cho giống thật
            song = (song / np.max(np.abs(song))).astype("float32")
            cac_dong.append(extract_features_from_array(song, tan_so))
            y.append(lop)

    X = pd.DataFrame(cac_dong, columns=list(FEATURE_NAMES))
    return X, np.array(y)


# ---------------------------------------------------------------------------
# HUẤN LUYỆN + ĐÁNH GIÁ
# ---------------------------------------------------------------------------

def huan_luyen_va_danh_gia(X, y, ten_lop=("Khỏe", "Bất thường")):
    """Chia dữ liệu, train Random Forest + hiệu chuẩn, in đánh giá TRUNG THỰC."""
    classes, counts = np.unique(y, return_counts=True)
    if len(classes) < 2:
        raise SystemExit("Dữ liệu phải có cả 2 lớp (0 và 1).")
    if counts.min() < 4:
        raise SystemExit(
            f"Mỗi lớp cần ít nhất vài mẫu để chia train/test. "
            f"Lớp ít nhất chỉ có {counts.min()} mẫu."
        )

    # Chia 70% train / 30% test, giữ tỉ lệ lớp. Test chỉ dùng để báo cáo.
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.3, random_state=RANDOM_STATE, stratify=y
    )
    # Tách thêm một phần train ra để hiệu chuẩn (không đụng vào test).
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_tr, y_tr, test_size=0.25, random_state=RANDOM_STATE, stratify=y_tr
    )

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        class_weight="balanced",  # cân bằng vì dữ liệu ho thường lệch nhiều lớp khỏe
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    base, cal = fit_calibrated(rf, X_fit, y_fit, X_val, y_val, method="sigmoid")

    # --- Đánh giá trên tập test ---
    y_pred = cal.predict(X_te)
    prob = cal.predict_proba(X_te)[:, list(cal.classes_).index(1)]

    print("\n" + "=" * 66)
    print("KẾT QUẢ PHÂN LOẠI TIẾNG HO (trên tập test)")
    print("=" * 66)
    print(classification_report(y_te, y_pred, target_names=list(ten_lop), zero_division=0))

    cm = confusion_matrix(y_te, y_pred)
    print("Ma trận nhầm lẫn (hàng = thật, cột = đoán):")
    print(f"            {ten_lop[0]:>10} {ten_lop[1]:>12}")
    for i, ten in enumerate(ten_lop):
        print(f"  {ten:<10} {cm[i][0]:>10} {cm[i][1]:>12}")

    try:
        auc = roc_auc_score(y_te, prob)
    except ValueError:
        auc = float("nan")
    ece = expected_calibration_error((np.array(y_te) == 1).astype(int), prob)

    print(f"\nAUC-ROC:  {auc:.3f}   (0.5 = đoán mò, 1.0 = hoàn hảo)")
    print(f"ECE:      {ece:.3f}   (càng nhỏ càng đáng tin về xác suất)")
    print("=" * 66)

    return base, cal, {
        "auc": float(auc),
        "ece": float(ece),
        "n_test": int(len(y_te)),
        "n_train": int(len(X_tr)),
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    bat_tieng_viet()
    tu_kiem = "--tu-kiem" in sys.argv

    print("=" * 66)
    print("HUẤN LUYỆN MÔ HÌNH PHÂN LOẠI TIẾNG HO")
    print("=" * 66)

    if tu_kiem:
        print(
            "\nCHẾ ĐỘ TỰ KIỂM — dùng âm thanh GIẢ để kiểm tra code.\n"
            "Đây KHÔNG phải kết quả khoa học. Con số cao ở đây chỉ chứng minh\n"
            "pipeline chạy đúng khi hai lớp thật sự khác nhau.\n"
        )
        X, y = sinh_du_lieu_tu_kiem()
        ten_lop = ("Trầm", "Cao")
    else:
        print(f"\nĐọc dữ liệu ho thật từ: {THU_MUC_AUDIO}/ và {FILE_NHAN}")
        X, y = doc_du_lieu_that()
        ten_lop = ("Khỏe", "Bất thường")

    print(f"Số mẫu: {len(y)}  |  Đặc trưng mỗi mẫu: {X.shape[1]}")

    base, cal, chi_so = huan_luyen_va_danh_gia(X, y, ten_lop=ten_lop)

    if tu_kiem:
        print(
            "\nTỰ KIỂM XONG. Nếu AUC ở trên gần 1.0 nghĩa là pipeline hoạt động.\n"
            "Giờ hãy tải dữ liệu ho thật và chạy lại KHÔNG kèm --tu-kiem."
        )
        return

    # Chỉ lưu mô hình khi train trên dữ liệu thật.
    import joblib

    joblib.dump(cal, FILE_MO_HINH)
    pd.DataFrame([chi_so]).to_csv(FILE_KET_QUA, index=False, encoding="utf-8-sig")
    print(f"\nĐã lưu mô hình: {FILE_MO_HINH}")
    print(f"Đã lưu chỉ số:  {FILE_KET_QUA}")
    print(
        "\nNHẮC LẠI: hãy báo cáo đúng AUC/ECE ở trên, kể cả khi khiêm tốn. Và ghi\n"
        "rõ trong báo cáo: mô hình tiếng ho là module RIÊNG, CHƯA nối vào điểm\n"
        "nguy cơ của hệ thống chính."
    )


if __name__ == "__main__":
    main()
