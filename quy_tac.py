"""Bộ quy tắc cảnh báo đỏ (Rule Engine) — Lớp an toàn số 1.

Đây là phần em tự viết hoàn toàn, không dùng học máy, chỉ dùng câu lệnh if.

Vì sao cần lớp này khi đã có AI?
--------------------------------
Vì AI không bao giờ được phép một mình quyết định rằng một ca là an toàn.
Có những dấu hiệu mà sách y khoa nói rõ là nguy hiểm, không cần bàn cãi.
Với những dấu hiệu đó, hệ thống cảnh báo NGAY, không hỏi ý kiến AI.

Hệ thống có 3 lớp:
    Lớp 1 (file này): Quy tắc cảnh báo đỏ → nếu trúng thì CAO ngay lập tức
    Lớp 2 (mô hình):  AI phân loại 3 mức
    Lớp 3 (file này): Hậu kiểm — nếu AI nói THẤP nhưng có >= 2 dấu hiệu đáng
                      ngờ thì nâng lên TRUNG BÌNH

QUAN TRỌNG: Bộ quy tắc này phải được BÁC SĨ DUYỆT VÀ KÝ XÁC NHẬN trước khi dùng.
Em không tự nghĩ ra các ngưỡng này — em lấy từ tài liệu y khoa và hỏi bác sĩ.

Nguồn của các ngưỡng (cần bác sĩ xác nhận lại):
    SpO2 < 92%          : ngưỡng thiếu oxy theo hướng dẫn hô hấp tuyến cơ sở
    Nhịp thở > 24 l/p    : thở nhanh ở người lớn
    Nhiệt độ > 39°C      : sốt cao
    Trẻ < 5 tuổi         : nhóm nguy cơ cao theo WHO
    Người > 65 tuổi      : nhóm nguy cơ cao theo WHO
"""

# ---------------------------------------------------------------------------
# LỚP 1 — CÁC QUY TẮC CẢNH BÁO ĐỎ
# ---------------------------------------------------------------------------


def kiem_tra_canh_bao_do(ca):
    """Kiểm tra một ca có trúng quy tắc cảnh báo đỏ nào không.

    Tham số:
        ca: dict thông tin bệnh nhân, ví dụ {"age": 78, "spo2": 91, ...}

    Trả về:
        Danh sách các lý do cảnh báo. Danh sách RỖNG nghĩa là không trúng
        quy tắc nào.

    Ví dụ:
        >>> kiem_tra_canh_bao_do({"age": 40, "spo2": 89, "dyspnea": 1, ...})
        ['SpO2 = 89% (dưới ngưỡng 92%) kèm khó thở']
    """
    ly_do = []

    # Quy tắc 1: Thiếu oxy kèm khó thở.
    # Đây là dấu hiệu suy hô hấp — nguy hiểm nhất trong nhóm bệnh hô hấp.
    if ca["spo2"] < 92 and ca["dyspnea"] == 1:
        ly_do.append(
            f"SpO2 = {ca['spo2']}% (dưới ngưỡng 92%) kèm khó thở "
            f"→ dấu hiệu suy hô hấp"
        )

    # Quy tắc 1b: SpO2 rất thấp thì nguy hiểm kể cả khi bệnh nhân chưa thấy khó thở.
    # Bài học y khoa: có bệnh nhân thiếu oxy nặng mà vẫn tỉnh táo, không thấy
    # khó thở ("silent hypoxia"). Không được bỏ sót nhóm này.
    if ca["spo2"] < 90:
        ly_do.append(
            f"SpO2 = {ca['spo2']}% rất thấp (dưới 90%) → nguy hiểm kể cả khi "
            f"bệnh nhân chưa thấy khó thở"
        )

    # Quy tắc 2: Đau ngực kèm khó thở xuất hiện đột ngột.
    # "Đột ngột" ở đây hiểu là bệnh mới bắt đầu (days_sick <= 1).
    # Bài học y khoa: đây có thể là thuyên tắc phổi hoặc tràn khí màng phổi,
    # cả hai đều là cấp cứu và phổi nghe có thể vẫn sạch.
    if ca["chest_pain"] == 1 and ca["dyspnea"] == 1 and ca["days_sick"] <= 1:
        ly_do.append(
            "Đau ngực kèm khó thở xuất hiện đột ngột → cần loại trừ thuyên tắc "
            "phổi hoặc tràn khí màng phổi"
        )

    # Quy tắc 3: Trẻ nhỏ bị khó thở.
    # Trẻ dưới 5 tuổi suy hô hấp rất nhanh, không thể chờ theo dõi.
    if ca["age"] < 5 and ca["dyspnea"] == 1:
        ly_do.append(
            f"Trẻ {ca['age']} tuổi (dưới 5) có khó thở → nhóm nguy cơ cao theo WHO"
        )

    # Quy tắc 4: Người cao tuổi sốt kèm thở nhanh.
    # Bài học y khoa: người già viêm phổi có thể KHÔNG sốt cao rõ, nên chỉ cần
    # có sốt (dù nhẹ) kèm thở nhanh là đã đáng lo.
    if ca["age"] > 65 and ca["fever"] == 1 and ca["respiratory_rate"] > 24:
        ly_do.append(
            f"Người {ca['age']} tuổi (trên 65) có sốt kèm thở nhanh "
            f"{ca['respiratory_rate']} lần/phút"
        )

    # Quy tắc 5: Sốt cao kéo dài kèm mệt nhiều.
    if ca["temperature"] > 39 and ca["days_sick"] > 3 and ca["fatigue"] == 1:
        ly_do.append(
            f"Sốt {ca['temperature']}°C kéo dài {ca['days_sick']} ngày kèm mệt nhiều"
        )

    # Quy tắc 6: Thở rất nhanh — dấu hiệu suy hô hấp bất kể nguyên nhân.
    if ca["respiratory_rate"] > 30 and ca["age"] >= 12:
        ly_do.append(
            f"Nhịp thở {ca['respiratory_rate']} lần/phút (trên 30) ở người lớn "
            f"→ dấu hiệu suy hô hấp"
        )

    return ly_do


# ---------------------------------------------------------------------------
# LỚP 3 — HẬU KIỂM
# ---------------------------------------------------------------------------


def dem_dau_hieu_dang_ngo(ca):
    """Đếm các dấu hiệu "hơi đáng lo" — chưa đủ để báo động đỏ nhưng nên chú ý.

    Trả về danh sách mô tả các dấu hiệu tìm thấy.
    """
    dau_hieu = []

    if 92 <= ca["spo2"] < 95:
        dau_hieu.append(f"SpO2 = {ca['spo2']}% hơi thấp (bình thường >= 95%)")
    if ca["respiratory_rate"] > 22:
        dau_hieu.append(f"Nhịp thở {ca['respiratory_rate']} lần/phút hơi nhanh")
    if ca["temperature"] > 38.5:
        dau_hieu.append(f"Sốt {ca['temperature']}°C khá cao")
    if ca["comorbidity"] == 1:
        dau_hieu.append("Có bệnh nền → nguy cơ diễn tiến nặng hơn")
    if ca["days_sick"] > 5:
        dau_hieu.append(f"Bệnh đã {ca['days_sick']} ngày mà chưa đỡ")
    if ca["age"] > 65:
        dau_hieu.append(f"Tuổi {ca['age']} (trên 65) → nhóm nguy cơ")
    if ca["fatigue"] == 1 and ca["dyspnea"] == 1:
        dau_hieu.append("Vừa mệt nhiều vừa khó thở")

    return dau_hieu


def hau_kiem(muc_ai, ca):
    """Lớp an toàn cuối: không cho AI nói "Thấp" quá dễ dàng.

    Nếu AI nói THẤP nhưng ca có từ 2 dấu hiệu đáng ngờ trở lên, nâng lên
    TRUNG BÌNH.

    Vì sao? Vì trong y khoa, sai lầm bỏ sót nguy hiểm hơn nhiều so với báo động
    giả. Nâng một ca từ Thấp lên Trung bình chỉ khiến nhân viên y tế nhìn kỹ
    hơn một chút — cái giá rất rẻ so với bỏ sót một ca viêm phổi.

    Tham số:
        muc_ai: mức nguy cơ AI đưa ra (0, 1 hoặc 2)
        ca: dict thông tin bệnh nhân

    Trả về:
        (muc_moi, ly_do_nang)  — ly_do_nang là None nếu không nâng
    """
    if muc_ai != 0:
        return muc_ai, None  # AI đã nói Trung bình hoặc Cao rồi, không cần can thiệp

    dau_hieu = dem_dau_hieu_dang_ngo(ca)
    if len(dau_hieu) >= 2:
        ly_do = (
            f"AI đánh giá mức Thấp, nhưng hệ thống phát hiện "
            f"{len(dau_hieu)} dấu hiệu đáng chú ý nên nâng lên mức Trung bình "
            f"cho an toàn: " + "; ".join(dau_hieu)
        )
        return 1, ly_do

    return 0, None


# ---------------------------------------------------------------------------
# MÔ HÌNH BASELINE — CHỈ DÙNG QUY TẮC, KHÔNG DÙNG AI
# ---------------------------------------------------------------------------


class MoHinhChiQuyTac:
    """Baseline 0: chỉ dùng quy tắc, không có học máy.

    Vì sao cần cái này? Để trả lời câu hỏi quan trọng nhất: "AI có thật sự cần
    thiết không, hay chỉ vài câu if là đủ?" Nếu mô hình học máy không tốt hơn
    baseline này, thì đề tài không cần đến AI.

    Lớp này có .predict() giống hệt mô hình sklearn nên có thể đem so sánh
    trực tiếp bằng compare_models().
    """

    # Để health_core biết mô hình này phân loại 3 lớp nào.
    classes_ = [0, 1, 2]

    def __init__(self, dac_trung):
        """Tham số: dac_trung — danh sách tên cột, đúng thứ tự."""
        self.dac_trung = list(dac_trung)

    def fit(self, X, y=None):
        """Không học gì cả — quy tắc là cố định. Có hàm này để giống sklearn."""
        return self

    def _thanh_dict(self, hang):
        """Đổi một hàng số thành dict {tên: giá trị} để quy tắc đọc được."""
        return {ten: gia_tri for ten, gia_tri in zip(self.dac_trung, hang)}

    def predict(self, X):
        """Dự đoán mức nguy cơ cho nhiều ca."""
        import numpy as np

        X = np.asarray(X, dtype=float)
        ket_qua = []

        for hang in X:
            ca = self._thanh_dict(hang)
            if kiem_tra_canh_bao_do(ca):
                ket_qua.append(2)  # trúng cảnh báo đỏ → Cao
            elif len(dem_dau_hieu_dang_ngo(ca)) >= 2:
                ket_qua.append(1)  # có vài dấu hiệu → Trung bình
            else:
                ket_qua.append(0)  # không có gì → Thấp

        return np.array(ket_qua)
