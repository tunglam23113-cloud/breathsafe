"""Huấn luyện lại mô hình sau khi đã thu đủ phản hồi của bác sĩ.

Chạy:  python retrain.py

Đây là phần "Physician-in-the-loop" — điểm khác biệt của BreathSafe so với các
app AI y tế thông thường (nhập triệu chứng → ra kết quả → hết).

Ý tưởng: mỗi lần bác sĩ không đồng ý với AI, ý kiến đó được lưu lại kèm lý do
chuyên môn. Sau mỗi 30 ca, mô hình được huấn luyện lại với dữ liệu đó ở trọng số
CAO GẤP 5 LẦN dữ liệu mô phỏng — vì đó là kiến thức đã được người có chuyên môn
kiểm chứng, không nên bị "loãng" giữa 2.000 mẫu máy tự sinh.

Script này CHỈ chạy được sau khi đã có phản hồi thật. Nó không tự bịa dữ liệu.
"""

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from health_core import RiskScreeningModel, PhysicianFeedbackLoop, compare_models

from dac_trung import DAC_TRUNG
from huan_luyen import chia_du_lieu, doc_du_lieu
from tieng_viet import bat_tieng_viet

FILE_MO_HINH = "mo_hinh_breathsafe.joblib"
FILE_PHAN_HOI = "phan_hoi_bac_si.json"
SO_CA_TOI_THIEU = 30  # không retrain khi chưa đủ, xem lý do bên dưới
RANDOM_STATE = 42


def boc_hieu_chuan(mo_hinh_goc, X_val, y_val, method="sigmoid"):
    """Bọc lại lớp hiệu chuẩn quanh một mô hình gốc VỪA ĐƯỢC HUẤN LUYỆN LẠI.

    Vì sao cần hàm này?
    -------------------
    RiskScreeningModel giữ hai thứ: `base_model_` (Random Forest thô) và
    `calibrated_model_` (lớp hiệu chuẩn bọc ngoài). Mọi hàm .predict() đều đi
    qua `calibrated_model_`, KHÔNG đi thẳng vào `base_model_`.

    Lớp hiệu chuẩn được khớp với phân phối xác suất của ĐÚNG mô hình gốc lúc đó.
    Khi ta huấn luyện lại `base_model_` với dữ liệu bác sĩ, phân phối đó đổi,
    nhưng lớp hiệu chuẩn cũ vẫn giữ nguyên — nên nó đang "dịch" xác suất của một
    mô hình khác. Con số phần trăm app hiển thị không còn là xác suất đã hiệu
    chuẩn nữa, mà chính lời hứa "khi hệ thống nói 80% thì đúng khoảng 80%" là
    điểm bán hàng của đề tài. Phải hiệu chuẩn lại thì con số đó mới còn giá trị.
    """
    try:
        from sklearn.frozen import FrozenEstimator

        hieu_chuan = CalibratedClassifierCV(
            FrozenEstimator(mo_hinh_goc), method=method
        )
    except ImportError:  # sklearn < 1.6
        hieu_chuan = CalibratedClassifierCV(mo_hinh_goc, method=method, cv="prefit")
    hieu_chuan.fit(X_val, y_val)
    return hieu_chuan


def main():
    bat_tieng_viet()

    print("=" * 70)
    print("BREATHSAFE — HUẤN LUYỆN LẠI TỪ PHẢN HỒI BÁC SĨ")
    print("=" * 70)

    vong_lap = PhysicianFeedbackLoop(FILE_PHAN_HOI, feature_names=DAC_TRUNG)
    so_bat_dong = len(vong_lap.disagreements)

    print(f"\nTổng số lượt phản hồi:      {len(vong_lap)}")
    print(f"Số lượt bác sĩ KHÔNG đồng ý: {so_bat_dong}")

    if so_bat_dong == 0:
        raise SystemExit(
            "\nChưa có ca bất đồng nào — không có gì để học.\n"
            "Hãy dùng Trang 2 của app để thu thập phản hồi trước."
        )

    if so_bat_dong < SO_CA_TOI_THIEU:
        print(
            f"\nCẢNH BÁO: mới có {so_bat_dong} ca, chưa đủ {SO_CA_TOI_THIEU} ca.\n"
            f"Retrain với quá ít ca rất rủi ro: mô hình có thể bị lệch theo ý kiến\n"
            f"riêng của một người thay vì học được quy luật chung. Trong nghiên cứu\n"
            f"thật, con số này phải do bác sĩ và giáo viên hướng dẫn thống nhất."
        )
        tra_loi = input("Vẫn muốn retrain? (go/khong): ").strip().lower()
        if tra_loi != "go":
            raise SystemExit("Đã hủy.")

    print(vong_lap.report())

    # ------------------------------------------------------------------
    # Chuẩn bị dữ liệu
    # ------------------------------------------------------------------
    df = doc_du_lieu()
    X_train, X_val, X_test, y_train, y_val, y_test = chia_du_lieu(df)

    X_train_val = pd.concat([X_train, X_val])
    y_train_val = pd.concat([y_train, y_val])

    # ------------------------------------------------------------------
    # So sánh: mô hình cũ vs mô hình sau khi học từ bác sĩ
    # ------------------------------------------------------------------
    print("\nĐang huấn luyện mô hình MỚI (dữ liệu gốc + phản hồi bác sĩ)...")

    mo_hinh_cu = RiskScreeningModel.load(FILE_MO_HINH)

    mo_hinh_moi = RiskScreeningModel(feature_names=DAC_TRUNG, random_state=RANDOM_STATE)
    mo_hinh_moi.train(X_train_val, y_train_val, verbose=False)

    # Tách riêng một phần để hiệu chuẩn lại SAU khi học từ bác sĩ. Phần này
    # KHÔNG được đưa vào bước huấn luyện lại bên dưới — hiệu chuẩn trên chính
    # dữ liệu vừa học sẽ cho ECE đẹp giả tạo (data leakage).
    X_hoc, X_hieu_chuan, y_hoc, y_hieu_chuan = train_test_split(
        X_train_val, y_train_val,
        test_size=0.2, random_state=RANDOM_STATE, stratify=y_train_val,
    )

    vong_lap.retrain(
        mo_hinh_moi.base_model_,
        X_hoc.values,
        y_hoc.values,
        feedback_weight=5.0,
    )
    # Bắt buộc: gắn lại lớp hiệu chuẩn cho mô hình gốc VỪA đổi (xem boc_hieu_chuan).
    mo_hinh_moi.calibrated_model_ = boc_hieu_chuan(
        mo_hinh_moi.base_model_, X_hieu_chuan.values, y_hieu_chuan.values
    )

    print("\nSo sánh trên tập test (tập test KHÔNG đổi, nên so sánh công bằng):\n")
    bang = compare_models(
        {"Mô hình cũ": mo_hinh_cu, "Sau khi học từ bác sĩ": mo_hinh_moi},
        X_test,
        y_test,
    )
    print(bang.to_string(index=False))

    # Dùng .iloc (theo VỊ TRÍ) chứ không phải .loc (theo NHÃN chỉ mục): nếu
    # compare_models đổi cách đánh chỉ mục, .loc[0] sẽ ném KeyError hoặc — tệ
    # hơn — trả về đúng một hàng khác mà không báo gì.
    recall_cu = bang.iloc[0]["Recall (Cao)"]
    recall_moi = bang.iloc[1]["Recall (Cao)"]

    print()
    if recall_moi > recall_cu:
        print(f"Recall nhóm Cao TĂNG: {recall_cu:.3f} → {recall_moi:.3f}")
    elif recall_moi < recall_cu:
        print(f"Recall nhóm Cao GIẢM: {recall_cu:.3f} → {recall_moi:.3f}")
        print(
            "  Kết quả xấu đi. Đây KHÔNG phải điều đáng giấu — hãy báo cáo trung\n"
            "  thực và tìm hiểu vì sao. Nguyên nhân thường gặp: quá ít ca phản hồi,\n"
            "  hoặc trọng số 5.0 quá cao khiến mô hình học lệch theo vài ca lẻ."
        )
    else:
        print(f"Recall nhóm Cao không đổi: {recall_cu:.3f}")

    # ------------------------------------------------------------------
    # Lưu — nhưng KHÔNG ghi đè mô hình cũ
    # ------------------------------------------------------------------
    # Giữ lại mô hình cũ để có thể so sánh và quay lui nếu mô hình mới tệ hơn.
    duong_dan = mo_hinh_moi.save("mo_hinh_breathsafe_moi.joblib")
    print(f"\nĐã lưu mô hình mới vào: {duong_dan}")
    print(
        "Mô hình CŨ vẫn được giữ nguyên. Nếu muốn dùng mô hình mới cho app, hãy\n"
        "tự đổi tên file — nhưng chỉ làm vậy SAU KHI đã xem bảng so sánh ở trên\n"
        "và thấy mô hình mới thật sự tốt hơn."
    )


if __name__ == "__main__":
    main()
