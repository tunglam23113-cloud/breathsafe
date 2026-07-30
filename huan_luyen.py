"""Huấn luyện và đánh giá mô hình BreathSafe.

Chạy:  python huan_luyen.py

Script này làm 6 việc, đúng theo phương pháp trong kế hoạch:
    1. Đọc dữ liệu và chia 70% train / 15% validation / 15% test
    2. Huấn luyện 4 mô hình để so sánh
    3. So sánh chúng bằng bảng chỉ số
    4. Đo mức độ hiệu chuẩn (ECE) trước và sau khi hiệu chuẩn
    5. Kiểm tra trên bộ 20 ca lâm sàng kinh điển
    6. Lưu mô hình tốt nhất ra file

Toàn bộ phần tính toán khó nằm trong thư viện health-core (cài bằng
pip install health-core). File này chỉ ghép các bước lại theo đúng thứ tự.
"""

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

from health_core import (
    RiskScreeningModel,
    compare_models,
    evaluate_textbook_cases,
    plot_reliability_diagram,
)

from ca_kinh_dien import CA_KINH_DIEN, da_duyet_hop_le
from dac_trung import DAC_TRUNG
from he_thong import HeThongBreathSafe
from quy_tac import MoHinhChiQuyTac
from tieng_viet import bat_tieng_viet

RANDOM_STATE = 42  # cố định để chạy lại ra kết quả y hệt

# Mọi đường dẫn neo vào THƯ MỤC CHỨA FILE NÀY, không phải thư mục hiện hành —
# cùng lý do đã ghi trong app.py. Trước đây chạy `python D:\...\huan_luyen.py`
# từ một thư mục khác thì script báo "không tìm thấy du_lieu_mo_phong.csv" dù
# file nằm ngay cạnh, và nếu có dữ liệu thì nó rải mô hình cùng các file kết quả
# ra thư mục hiện hành — app.py lại chỉ đọc trong thư mục của chính nó, nên app
# vẫn dùng mô hình cũ mà không có lỗi nào báo ra.
THU_MUC = Path(__file__).resolve().parent


def doc_du_lieu(duong_dan=None):
    """Đọc file CSV. Báo lỗi rõ ràng nếu chưa sinh dữ liệu."""
    duong_dan = THU_MUC / "du_lieu_mo_phong.csv" if duong_dan is None else Path(duong_dan)
    try:
        return pd.read_csv(duong_dan)
    except FileNotFoundError:
        raise SystemExit(
            f"Không tìm thấy file {duong_dan}.\n"
            f"Hãy chạy lệnh này trước:  python tao_du_lieu.py"
        )


def chia_du_lieu(df):
    """Chia dữ liệu thành 3 phần: 70% train, 15% validation, 15% test.

    Vì sao cần tận 3 phần, không phải 2?
      - train:      để mô hình học
      - validation: để hiệu chuẩn xác suất và chọn tham số
      - test:       CHỈ dùng đúng MỘT LẦN ở cuối để báo cáo kết quả

    Nếu dùng tập test để chỉnh tham số rồi lại báo cáo trên chính nó, kết quả sẽ
    đẹp giả tạo. Đó gọi là "data leakage" — lỗi phổ biến nhất trong các đề tài
    học sinh, và giám khảo sẽ hỏi.

    Dùng stratify để cả 3 phần đều giữ đúng tỉ lệ 50:30:20, nếu không tập test
    có thể tình cờ có rất ít ca nguy cơ Cao khiến Recall đo được vô nghĩa.
    """
    X = df[DAC_TRUNG]
    y = df["risk_level"]

    # Bước 1: cắt 15% ra làm test và KHÔNG ĐỘNG VÀO NÓ nữa cho đến cuối.
    X_conlai, X_test, y_conlai, y_test = train_test_split(
        X, y, test_size=0.15, random_state=RANDOM_STATE, stratify=y
    )
    # Bước 2: từ 85% còn lại, cắt tiếp ~17.6% để được 15% của tổng ban đầu.
    X_train, X_val, y_train, y_val = train_test_split(
        X_conlai, y_conlai, test_size=0.176, random_state=RANDOM_STATE,
        stratify=y_conlai,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def main():
    bat_tieng_viet()

    print("=" * 70)
    print("BREATHSAFE — HUẤN LUYỆN VÀ ĐÁNH GIÁ MÔ HÌNH")
    print("=" * 70)

    # ------------------------------------------------------------------
    # BƯỚC 1: Đọc và chia dữ liệu
    # ------------------------------------------------------------------
    df = doc_du_lieu()
    X_train, X_val, X_test, y_train, y_val, y_test = chia_du_lieu(df)

    print("\n[BƯỚC 1] Chia dữ liệu")
    print(f"  Train:      {len(X_train):>5} ca  ({100 * len(X_train) / len(df):.0f}%)")
    print(f"  Validation: {len(X_val):>5} ca  ({100 * len(X_val) / len(df):.0f}%)")
    print(f"  Test:       {len(X_test):>5} ca  ({100 * len(X_test) / len(df):.0f}%)")

    # ------------------------------------------------------------------
    # BƯỚC 2: Huấn luyện 4 mô hình
    # ------------------------------------------------------------------
    print("\n[BƯỚC 2] Huấn luyện các mô hình để so sánh")

    # Mô hình 0 — chỉ dùng quy tắc if/else, KHÔNG có học máy.
    # Đây là câu trả lời cho "AI có thật sự cần thiết không?".
    mo_hinh_quy_tac = MoHinhChiQuyTac(DAC_TRUNG).fit(X_train, y_train)
    print("  [1/4] Chỉ Rule Engine — xong (không cần học)")

    # Mô hình 1 — Logistic Regression: mô hình tuyến tính đơn giản nhất.
    # max_iter=1000 vì mặc định 100 vòng lặp không đủ để hội tụ với dữ liệu này.
    mo_hinh_lr = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE
    ).fit(X_train, y_train)
    print("  [2/4] Logistic Regression — xong")

    # Mô hình 2 — Decision Tree: vẽ được thành sơ đồ để giải thích.
    mo_hinh_dt = DecisionTreeClassifier(
        max_depth=6, class_weight={0: 1, 1: 3, 2: 10}, random_state=RANDOM_STATE
    ).fit(X_train, y_train)
    print("  [3/4] Decision Tree — xong")

    # Mô hình 3 — BreathSafe đầy đủ: Random Forest + cost-sensitive
    #             + hiệu chuẩn xác suất + phát hiện ca lạ.
    # Lưu ý: .train() tự cắt tập validation riêng bên trong để hiệu chuẩn,
    # nên ở đây ta gộp train + val lại rồi đưa vào.
    X_train_val = pd.concat([X_train, X_val])
    y_train_val = pd.concat([y_train, y_val])
    mo_hinh_breathsafe = RiskScreeningModel(
        feature_names=DAC_TRUNG, random_state=RANDOM_STATE
    )
    mo_hinh_breathsafe.train(X_train_val, y_train_val, verbose=False)
    print("  [4/4] BreathSafe (RF + cost-sensitive + calibration + OOD) — xong")

    # Hệ thống HOÀN CHỈNH = Rule Engine + AI + Hậu kiểm.
    # Đây mới là thứ đem đi thi. Bốn mô hình ở trên chỉ là các thành phần để
    # so sánh cho biết mỗi lớp đóng góp được bao nhiêu.
    he_thong = HeThongBreathSafe(mo_hinh_breathsafe)
    print("  [+]   Hệ thống 3 lớp đầy đủ (Rule + AI + Hậu kiểm) — đã ghép xong")

    # ------------------------------------------------------------------
    # BƯỚC 3: So sánh trên tập test
    # ------------------------------------------------------------------
    print("\n[BƯỚC 3] So sánh các mô hình trên tập test")
    print("  (Đọc cột 'Recall (Cao)' trước tiên — đó là chỉ số quan trọng nhất.")
    print("   Accuracy chỉ để tham khảo: mô hình luôn nói 'Thấp' vẫn đạt ~50%.)\n")

    bang = compare_models(
        {
            "Chỉ Rule Engine": mo_hinh_quy_tac,
            "Logistic Regression": mo_hinh_lr,
            "Decision Tree": mo_hinh_dt,
            "Chỉ AI (RF + hiệu chuẩn)": mo_hinh_breathsafe,
            "HỆ THỐNG ĐẦY ĐỦ (Rule + AI + Hậu kiểm)": he_thong,
        },
        X_test,
        y_test,
    )
    print(bang.to_string(index=False))
    bang.to_csv(THU_MUC / "ket_qua_so_sanh.csv", index=False, encoding="utf-8-sig")
    print("\n  Đã lưu bảng vào: ket_qua_so_sanh.csv")

    print("\n  CÁCH ĐỌC BẢNG NÀY — giám khảo sẽ hỏi hai câu sau:")
    print("\n  Câu 1: 'Vì sao HỆ THỐNG ĐẦY ĐỦ có Accuracy và F1 THẤP HƠN Chỉ AI?'")
    print("    Vì Rule Engine cố tình đẩy nhiều ca lên mức Cao. Nó đánh đổi:")
    print("    bắt được nhiều ca nguy hiểm hơn (Recall tăng) nhưng báo động giả")
    print("    nhiều hơn (Accuracy giảm). Đây là LỰA CHỌN CÓ CHỦ Ý, không phải lỗi.")
    print("    Trong y khoa, bỏ sót một ca viêm phổi nặng có thể khiến một người")
    print("    chết; một báo động giả chỉ tốn của nhân viên y tế vài phút xem lại.")
    print("    Em tối ưu Recall, không tối ưu Accuracy.")
    print("\n  Câu 2: 'Vì sao cột ECE của Rule Engine và Hệ thống đầy đủ là NaN?'")
    print("    Vì hai mô hình đó không đưa ra xác suất. Khi Rule Engine kết luận")
    print("    'SpO2 = 88% kèm khó thở là nguy hiểm', đó là một quyết định y khoa")
    print("    dứt khoát, không phải con số xác suất — nên không có gì để hiệu")
    print("    chuẩn. ECE chỉ có ý nghĩa với phần AI, và phần đó đã đạt mục tiêu.")

    # ------------------------------------------------------------------
    # BƯỚC 4: Kiểm tra độ ổn định bằng cross-validation
    # ------------------------------------------------------------------
    print("\n[BƯỚC 4] Cross-validation 5 fold (kiểm tra mô hình có ổn định không)")
    print("  Nếu độ lệch chuẩn lớn, kết quả chỉ là may mắn của một lần chia dữ liệu.")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    diem = cross_val_score(
        DecisionTreeClassifier(
            max_depth=6, class_weight={0: 1, 1: 3, 2: 10}, random_state=RANDOM_STATE
        ),
        X_train_val, y_train_val, cv=cv, scoring="f1_macro",
    )
    print(f"  F1 macro (Decision Tree): {diem.mean():.3f} ± {diem.std():.3f}")

    # ------------------------------------------------------------------
    # BƯỚC 5: Hiệu chuẩn xác suất
    # ------------------------------------------------------------------
    print("\n[BƯỚC 5] Hiệu chuẩn xác suất (calibration)")

    bao_cao = mo_hinh_breathsafe.training_report_
    if bao_cao.get("ece_before") is not None:
        truoc, sau = bao_cao["ece_before"], bao_cao["ece_after"]
        print(f"  ECE lớp 'Cao' trước hiệu chuẩn: {truoc:.4f}")
        print(f"  ECE lớp 'Cao' sau hiệu chuẩn:   {sau:.4f}")
        if truoc > 0:
            print(f"  → Thay đổi: {100 * (truoc - sau) / truoc:+.1f}%")
        print("  (Hai số trên đo trên tập validation nên có lợi cho mô hình.")
        print("   Số ĐỂ BÁO CÁO là cột ECE trong bảng ở Bước 3 — đo trên tập test.)")

    # Vẽ reliability diagram để đưa vào báo cáo.
    y_test_cao = (y_test.values == 2).astype(int)
    cot_cao = list(mo_hinh_breathsafe.base_model_.classes_).index(2)
    prob_truoc = mo_hinh_breathsafe.base_model_.predict_proba(X_test.values)[:, cot_cao]
    prob_sau = mo_hinh_breathsafe.predict_proba(X_test)[:, cot_cao]

    try:
        plot_reliability_diagram(
            y_test_cao, prob_truoc, prob_sau,
            save_path=str(THU_MUC / "reliability_diagram.png"),
        )
        print("  Đã lưu biểu đồ: reliability_diagram.png")
    except ImportError:
        print("  (Bỏ qua biểu đồ — chưa cài matplotlib: pip install matplotlib)")

    # ------------------------------------------------------------------
    # BƯỚC 6: Kiểm tra trên 20 ca lâm sàng kinh điển
    # ------------------------------------------------------------------
    print("\n[BƯỚC 6] Kiểm tra trên bộ 20 ca lâm sàng kinh điển")
    print("  Đây là phép thử QUAN TRỌNG NHẤT: các ca này KHÔNG sinh ra từ quy")
    print("  tắc của em, nên chúng kiểm tra mô hình thật sự chứ không phải kiểm")
    print("  tra xem mô hình có học thuộc quy tắc của em không.\n")

    # Chạy HAI lần: một lần chỉ AI, một lần hệ thống đầy đủ. So sánh hai kết quả
    # cho thấy Rule Engine đóng góp được bao nhiêu — bằng chứng cho thấy lớp 1
    # không thừa.
    print(">>> Chỉ dùng AI:")
    ca_chi_ai = evaluate_textbook_cases(
        mo_hinh_breathsafe, CA_KINH_DIEN, DAC_TRUNG, verbose=True
    )

    print("\n>>> Hệ thống đầy đủ (Rule + AI + Hậu kiểm):")
    ket_qua_ca = evaluate_textbook_cases(
        he_thong, CA_KINH_DIEN, DAC_TRUNG, verbose=True
    )
    ket_qua_ca.to_csv(
        THU_MUC / "ket_qua_ca_kinh_dien.csv", index=False, encoding="utf-8-sig"
    )
    print("\nĐã lưu vào: ket_qua_ca_kinh_dien.csv")

    # Dùng len(CA_KINH_DIEN) chứ không gõ cứng "20": thêm hay bớt một ca là
    # dòng kết luận in ra sai ngay, mà con số này đi thẳng vào báo cáo.
    n_ca = len(CA_KINH_DIEN)
    khop_ai = int(ca_chi_ai["match"].sum())
    khop_day_du = int(ket_qua_ca["match"].sum())
    print(
        f"\n  Rule Engine giúp tăng từ {khop_ai}/{n_ca} lên {khop_day_du}/{n_ca} ca."
        if khop_day_du > khop_ai
        else f"\n  Rule Engine không thay đổi kết quả ({khop_ai}/{n_ca})."
    )

    # Lưu lại cả hai con số để README và báo cáo trích đúng, không phải chép tay.
    pd.DataFrame(
        [{"so_ca": n_ca, "khop_chi_ai": khop_ai, "khop_he_thong_day_du": khop_day_du}]
    ).to_csv(
        THU_MUC / "ket_qua_ca_kinh_dien_tong_hop.csv",
        index=False,
        encoding="utf-8-sig",
    )

    if not da_duyet_hop_le():
        print(
            f"\n*** LƯU Ý: bộ {n_ca} ca CHƯA có chữ ký bác sĩ. ***\n"
            "Kết quả trên chưa có giá trị chuyên môn để đưa vào báo cáo.\n"
            "Xem hướng dẫn trong file ca_kinh_dien.py."
        )

    # ------------------------------------------------------------------
    # BƯỚC 7: Lưu mô hình
    # ------------------------------------------------------------------
    duong_dan = mo_hinh_breathsafe.save(str(THU_MUC / "mo_hinh_breathsafe.joblib"))
    print(f"\n[BƯỚC 7] Đã lưu mô hình vào: {duong_dan}")

    print("\n  Các thông tin mô hình dựa vào nhiều nhất (feature importance):")
    for ten, do_quan_trong in mo_hinh_breathsafe.top_features(5):
        thanh = "█" * int(do_quan_trong * 60)
        print(f"    {ten:<18} {do_quan_trong:.3f}  {thanh}")
    print("\n  (Đây là mức quan trọng TRUNG BÌNH của cả mô hình, KHÔNG phải lý do")
    print("   cho một ca cụ thể. Đừng nói 'mô hình cảnh báo ca NÀY vì SpO2'.)")

    print("\n" + "=" * 70)
    print("HOÀN THÀNH. Chạy giao diện bằng lệnh:  streamlit run app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
