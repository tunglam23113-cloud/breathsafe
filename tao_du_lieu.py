"""Sinh bộ dữ liệu mô phỏng 2.000 ca để huấn luyện mô hình.

Chạy:  python tao_du_lieu.py

================================================================================
ĐỌC KỸ PHẦN NÀY TRƯỚC KHI DÙNG — GIỚI HẠN LỚN NHẤT CỦA ĐỀ TÀI
================================================================================
Dữ liệu này là MÔ PHỎNG, không phải bệnh nhân thật. Điều đó dẫn tới một vấn đề
gọi là "lập luận vòng tròn" (circular reasoning):

    Em viết quy tắc để sinh nhãn → Mô hình học từ nhãn đó
    → Mô hình học lại chính quy tắc của em
    → Mô hình đạt điểm cao KHÔNG chứng minh nó giỏi y khoa,
      nó chỉ chứng minh nó học thuộc được quy tắc em viết.

Giám khảo cấp quốc gia CHẮC CHẮN sẽ hỏi câu này. Đừng né. Câu trả lời trung thực:

    "Đúng ạ, đây là giới hạn lớn nhất của đề tài em. Kết quả trên tập test mô
     phỏng chỉ chứng minh mô hình học được quy tắc, KHÔNG chứng minh nó đúng về
     y khoa. Vì vậy em có thêm HAI cách kiểm chứng độc lập với dữ liệu mô phỏng:
       (1) Bộ 20 ca lâm sàng kinh điển do bác sĩ duyệt và ký — các ca này KHÔNG
           được sinh ra từ quy tắc của em.
       (2) Dataset công khai bên ngoài (Kaggle/Coswara) — dữ liệu thật, không
           phải em tạo ra.
     Con số đáng tin nhất trong báo cáo của em là kết quả trên hai nguồn đó,
     không phải con số trên tập test mô phỏng."

Vì lý do trên, script này CỐ TÌNH làm dữ liệu khó hơn thay vì sạch đẹp:
  - Nhãn sinh bằng THANG ĐIỂM có trọng số (mượt), còn Rule Engine chỉ dùng
    ngưỡng nhị phân (thô). Nhờ vậy so sánh Rule vs AI mới có ý nghĩa — nếu cả
    hai dùng chung một bộ quy tắc thì kết quả so sánh là vô nghĩa.
  - Có 5% ca nhiễu (dữ liệu mâu thuẫn), giống thực tế đo sai / khai sai.
  - Ngưỡng nhịp thở thay đổi theo tuổi, vì trẻ nhỏ thở nhanh hơn người lớn.
================================================================================
"""

from pathlib import Path

import numpy as np
import pandas as pd

from dac_trung import DAC_TRUNG
# Bảng nhịp thở bình thường theo tuổi nằm ở quy_tac.py để cả hệ thống dùng chung
# MỘT bảng duy nhất. Trước đây file này giữ một bản sao riêng, nên sửa bảng ở một
# nơi mà quên nơi kia là dữ liệu và quy tắc lệch nhau mà không ai biết.
from quy_tac import nhip_tho_binh_thuong
from tieng_viet import bat_tieng_viet

# Cố định số ngẫu nhiên → chạy lại luôn ra bộ dữ liệu y hệt.
# Đây là yêu cầu "reproducibility" của nghiên cứu khoa học.
RANDOM_STATE = 42

# Ghi ra THƯ MỤC CHỨA FILE NÀY, không phải thư mục hiện hành. Chạy script từ một
# thư mục khác mà ghi theo đường dẫn tương đối trần thì file dữ liệu rơi ra chỗ
# khác, còn huan_luyen.py và app.py vẫn tìm trong thư mục của chúng — hai bên
# lệch nhau mà không có lỗi nào báo ra.
THU_MUC = Path(__file__).resolve().parent
FILE_DU_LIEU = THU_MUC / "du_lieu_mo_phong.csv"


# ---------------------------------------------------------------------------
# BƯỚC 1: Các hàm y khoa cơ bản
# ---------------------------------------------------------------------------


def diem_nguy_co(ca):
    """Tính điểm nguy cơ của một ca bằng thang điểm có trọng số.

    Đây là "sự thật" mà mô hình phải học được. Khác với Rule Engine ở chỗ:
    thang điểm này MƯỢT (cứ thiếu 1% SpO2 là cộng thêm điểm), còn Rule Engine
    chỉ có ngưỡng CỨNG (dưới 92% thì báo, 92.1% thì không).

    Điểm càng cao càng nguy hiểm.
    """
    diem = 0.0

    # --- SpO2: yếu tố quan trọng nhất -------------------------------------
    # Càng dưới 95% càng nguy hiểm, và mức độ tăng nhanh dần chứ không đều.
    if ca["spo2"] < 95:
        thieu = 95 - ca["spo2"]
        diem += thieu * 1.2
        if ca["spo2"] < 90:
            diem += 4.0  # dưới 90% là mốc nguy hiểm rõ rệt

    # --- Khó thở ----------------------------------------------------------
    if ca["dyspnea"] == 1:
        diem += 3.5
        if ca["spo2"] < 93:
            diem += 2.0  # khó thở KÈM thiếu oxy nguy hiểm hơn tổng của hai cái riêng lẻ

    # --- Nhịp thở: so với mức bình thường CỦA TUỔI ĐÓ ---------------------
    binh_thuong = nhip_tho_binh_thuong(ca["age"])
    tho_nhanh = ca["respiratory_rate"] - binh_thuong
    if tho_nhanh > 0:
        diem += tho_nhanh * 0.25

    # --- Sốt --------------------------------------------------------------
    if ca["temperature"] > 38.5:
        diem += (ca["temperature"] - 38.5) * 1.5
    if ca["temperature"] > 39 and ca["days_sick"] > 3:
        diem += 2.0  # sốt cao mà kéo dài thì đáng lo hơn sốt cao mới 1 ngày

    # --- Tuổi -------------------------------------------------------------
    if ca["age"] > 65:
        diem += 1.5
        if ca["age"] > 80:
            diem += 1.0
    if ca["age"] < 5:
        diem += 1.5

    # --- Bệnh nền ---------------------------------------------------------
    if ca["comorbidity"] == 1:
        diem += 2.0
        if ca["dyspnea"] == 1:
            diem += 1.5  # bệnh nền + khó thở = dễ diễn tiến nặng

    # --- Đau ngực ---------------------------------------------------------
    if ca["chest_pain"] == 1:
        diem += 1.0
        if ca["dyspnea"] == 1 and ca["days_sick"] <= 1:
            diem += 3.5  # đột ngột đau ngực + khó thở = nghi thuyên tắc phổi

    # --- Mệt nhiều --------------------------------------------------------
    if ca["fatigue"] == 1:
        diem += 1.0

    # --- Thời gian bệnh ---------------------------------------------------
    # Bệnh kéo dài nhiều tuần là dấu hiệu bệnh mạn tính nặng (lao, ung thư).
    # NHƯNG chỉ đáng lo khi CÓ KÈM dấu hiệu khác — ho kéo dài đơn thuần mà mọi
    # chỉ số bình thường thì thường lành tính (ví dụ ho do trào ngược).
    if ca["days_sick"] > 14 and (ca["fever"] == 1 or ca["fatigue"] == 1):
        diem += 2.5

    return diem


def diem_thanh_nhan(diem):
    """Đổi điểm nguy cơ thành nhãn 0 / 1 / 2.

    Hai ngưỡng 5.6 và 11.95 KHÔNG phải em chọn bừa. Em sinh thử 60.000 ca, tính
    điểm cho từng ca, rồi lấy phân vị 50% và 80% của dãy điểm đó — nhờ vậy tỉ lệ
    3 lớp ra đúng 50 : 30 : 20 như kế hoạch.

    Đây là lựa chọn KỸ THUẬT để cân bằng lớp, không phải ngưỡng y khoa. Bác sĩ
    cần xem lại: một ca 11.9 điểm và một ca 12.0 điểm gần như giống hệt nhau,
    nhưng bị xếp vào hai mức khác nhau. Ranh giới giữa các mức nguy cơ trong
    thực tế là mờ, không sắc nét như vậy — đây là một giới hạn cần ghi vào
    phần Thảo luận của báo cáo.
    """
    if diem >= 11.95:
        return 2  # Cao
    if diem >= 5.6:
        return 1  # Trung bình
    return 0  # Thấp


# ---------------------------------------------------------------------------
# BƯỚC 2: Sinh một ca ngẫu nhiên
# ---------------------------------------------------------------------------


def sinh_mot_ca(rng):
    """Sinh ngẫu nhiên một ca bệnh với phân phối gần giống thực tế.

    Tham số:
        rng: bộ sinh số ngẫu nhiên của numpy

    Điểm quan trọng: các triệu chứng KHÔNG độc lập với nhau. Người bị viêm phổi
    nặng thì vừa sốt, vừa khó thở, vừa SpO2 thấp. Nếu sinh mỗi thứ độc lập, dữ
    liệu sẽ vô lý (ví dụ SpO2 = 99% mà thở 40 lần/phút) và mô hình học được sẽ
    vô nghĩa. Nên ở đây em sinh theo thứ tự: chọn "độ nặng ngầm" trước, rồi sinh
    các triệu chứng phụ thuộc vào độ nặng đó.
    """
    # "Độ nặng ngầm" — một con số 0 đến 1 mà thực tế không ai đo được,
    # nhưng nó là nguyên nhân chung gây ra tất cả các triệu chứng.
    do_nang = rng.beta(2, 4)  # lệch về phía nhẹ, giống thực tế ở trạm y tế xã

    # Tuổi: mô phỏng dân số đến trạm y tế xã — nhiều trẻ nhỏ và người già.
    nhom_tuoi = rng.choice(["tre", "nguoi_lon", "gia"], p=[0.25, 0.5, 0.25])
    if nhom_tuoi == "tre":
        # Bắt đầu từ 0, KHÔNG phải 1. Bản trước dùng integers(1, 12) nên trong
        # 2.000 ca không có lấy một trẻ dưới 1 tuổi nào — trong khi app cho nhập
        # tuổi từ 0, và bảng nhịp thở có hẳn một nhóm riêng cho lứa này (ngưỡng
        # 40 lần/phút). Hậu quả: mọi ca nhũ nhi đều là ca LẠ với mô hình, còn
        # nhánh "tuoi < 1" của nhip_tho_binh_thuong() thì không bao giờ được
        # dùng tới lúc sinh dữ liệu. Ca TC12 (bé 8 tháng) chính là nhóm này.
        tuoi = int(rng.integers(0, 12))
    elif nhom_tuoi == "nguoi_lon":
        tuoi = int(rng.integers(12, 65))
    else:
        tuoi = int(rng.integers(65, 95))

    # SpO2: người khỏe 96-100%, càng nặng càng thấp.
    spo2 = int(np.clip(round(99 - do_nang * 14 + rng.normal(0, 1.5)), 80, 100))

    # Khó thở: xác suất tăng theo độ nặng.
    dyspnea = int(rng.random() < do_nang * 1.3)

    # Nhịp thở: quanh mức bình thường của tuổi, cộng thêm theo độ nặng.
    rr = int(np.clip(
        round(nhip_tho_binh_thuong(tuoi) + do_nang * 16 + rng.normal(0, 2)),
        10, 60,
    ))

    # Sốt và nhiệt độ.
    fever = int(rng.random() < 0.25 + do_nang * 0.5)
    if fever:
        temperature = round(float(np.clip(37.5 + do_nang * 2.2 + rng.normal(0, 0.4), 37.5, 41.0)), 1)
    else:
        temperature = round(float(np.clip(rng.normal(36.8, 0.3), 35.5, 37.4)), 1)

    # Các triệu chứng còn lại.
    cough = int(rng.random() < 0.75)
    chest_pain = int(rng.random() < 0.1 + do_nang * 0.3)
    fatigue = int(rng.random() < 0.2 + do_nang * 0.6)

    # Bệnh nền: phụ thuộc tuổi, không phụ thuộc độ nặng đợt bệnh này.
    p_benh_nen = 0.05 if tuoi < 40 else (0.25 if tuoi < 65 else 0.5)
    comorbidity = int(rng.random() < p_benh_nen)

    # Số ngày bệnh.
    days_sick = int(np.clip(round(rng.exponential(4)), 0, 90))

    return {
        "age": tuoi,
        "fever": fever,
        "temperature": temperature,
        "cough": cough,
        "dyspnea": dyspnea,
        "spo2": spo2,
        "respiratory_rate": rr,
        "chest_pain": chest_pain,
        "fatigue": fatigue,
        "days_sick": days_sick,
        "comorbidity": comorbidity,
    }


# ---------------------------------------------------------------------------
# BƯỚC 3: Sinh cả bộ dữ liệu
# ---------------------------------------------------------------------------


def tao_bo_du_lieu(so_ca=2000, ty_le_nhieu=0.05, random_state=RANDOM_STATE):
    """Sinh bộ dữ liệu hoàn chỉnh.

    Tham số:
        so_ca: số ca cần sinh
        ty_le_nhieu: tỉ lệ ca bị làm nhiễu (5% theo kế hoạch)

    Vì sao phải CỐ TÌNH thêm nhiễu? Vì dữ liệu thật không bao giờ sạch:
      - Máy đo SpO2 rẻ tiền có thể đo sai
      - Bệnh nhân khai không chính xác ("em không khó thở đâu" trong khi đang thở dốc)
      - Nhân viên y tế ghi nhầm số
    Nếu mô hình chỉ học trên dữ liệu sạch hoàn hảo, nó sẽ thất bại ngay khi gặp
    thực tế. Thêm nhiễu là cách làm cho mô hình bền hơn, và cũng làm cho kết quả
    báo cáo trung thực hơn (accuracy sẽ thấp hơn nhưng đáng tin hơn).
    """
    rng = np.random.default_rng(random_state)
    cac_ca = []

    for _ in range(so_ca):
        ca = sinh_mot_ca(rng)
        ca["risk_level"] = diem_thanh_nhan(diem_nguy_co(ca))
        # Ghi lại giới tính để phân tích, dù mô hình không dùng (xem dac_trung.py).
        ca["gender"] = int(rng.integers(0, 2))
        cac_ca.append(ca)

    df = pd.DataFrame(cac_ca)

    # --- Thêm nhiễu -------------------------------------------------------
    so_nhieu = int(so_ca * ty_le_nhieu)
    chi_so_nhieu = rng.choice(len(df), size=so_nhieu, replace=False)

    for i in chi_so_nhieu:
        kieu = rng.choice(["do_sai_spo2", "khai_sai_trieu_chung", "ghi_nham_nhiet_do"])
        if kieu == "do_sai_spo2":
            # Máy đo lỗi hoặc ngón tay lạnh → SpO2 lệch vài đơn vị.
            df.loc[i, "spo2"] = int(np.clip(df.loc[i, "spo2"] + rng.integers(-6, 7), 80, 100))
        elif kieu == "khai_sai_trieu_chung":
            # Bệnh nhân khai ngược một triệu chứng.
            cot = rng.choice(["dyspnea", "cough", "fatigue", "chest_pain"])
            df.loc[i, cot] = 1 - df.loc[i, cot]
        else:
            # Kẹp lại trong khoảng 35.0–42.0°C. Nhiễu không kẹp có thể sinh ra
            # nhiệt độ 34.1 hay 43.5 — vừa vô lý về sinh lý, vừa nằm NGOÀI dải
            # thanh trượt của app (35.0–42.0), nên mô hình được học trên những
            # giá trị mà lúc dùng thật không bao giờ nhập vào được.
            df.loc[i, "temperature"] = round(
                float(np.clip(
                    float(df.loc[i, "temperature"]) + float(rng.normal(0, 1.0)),
                    35.0, 42.0,
                )),
                1,
            )

    # LƯU Ý: nhãn risk_level KHÔNG được tính lại sau khi thêm nhiễu.
    # Đó chính là mục đích: nhãn phản ánh tình trạng THẬT của bệnh nhân, còn các
    # con số đo được thì bị sai. Mô hình phải học cách chịu đựng sai số đó — y
    # hệt như bác sĩ thật phải làm.

    df["la_ca_nhieu"] = 0
    df.loc[chi_so_nhieu, "la_ca_nhieu"] = 1

    # Sắp xếp cột: đặc trưng trước, rồi nhãn, rồi thông tin phụ.
    df = df[DAC_TRUNG + ["risk_level", "gender", "la_ca_nhieu"]]
    return df


def in_thong_ke(df):
    """In thống kê mô tả bộ dữ liệu — dùng để đưa vào báo cáo."""
    ten_muc = {0: "Thấp", 1: "Trung bình", 2: "Cao"}

    print("=" * 66)
    print("THỐNG KÊ BỘ DỮ LIỆU MÔ PHỎNG")
    print("=" * 66)
    print(f"Tổng số ca: {len(df)}")
    print(f"Số ca có nhiễu: {int(df['la_ca_nhieu'].sum())} "
          f"({100 * df['la_ca_nhieu'].mean():.1f}%)")

    print("\nPhân bố 3 mức nguy cơ (mục tiêu 50 : 30 : 20):")
    for muc, so_luong in df["risk_level"].value_counts().sort_index().items():
        print(f"  {ten_muc[muc]:<12} {so_luong:>5} ca  ({100 * so_luong / len(df):>5.1f}%)")

    print("\nGiá trị trung bình theo từng mức nguy cơ:")
    bang = df.groupby("risk_level")[
        ["age", "spo2", "respiratory_rate", "temperature", "dyspnea"]
    ].mean().round(1)
    bang.index = [ten_muc[i] for i in bang.index]
    print(bang.to_string())
    print("\n(Kiểm tra bằng mắt: SpO2 phải GIẢM dần và khó thở phải TĂNG dần khi")
    print(" mức nguy cơ tăng. Nếu không, quy tắc sinh dữ liệu có lỗi.)")
    print("=" * 66)


if __name__ == "__main__":
    bat_tieng_viet()

    df = tao_bo_du_lieu(so_ca=2000)
    in_thong_ke(df)

    df.to_csv(FILE_DU_LIEU, index=False, encoding="utf-8-sig")
    print(f"\nĐã lưu vào: {FILE_DU_LIEU}")
    print("(Dùng encoding utf-8-sig để mở bằng Excel không bị lỗi font tiếng Việt.)")
