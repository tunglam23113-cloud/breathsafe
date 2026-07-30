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
                      ngờ, HOẶC có một chỉ số đã ở mức bất thường (SpO2 < 92,
                      nhiệt độ > 39), thì nâng lên TRUNG BÌNH

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
# NGƯỠNG NHỊP THỞ THEO TUỔI — dùng chung cho cả hệ thống
# ---------------------------------------------------------------------------
# Đây là hai bảng tra y khoa, KHÔNG phải quy tắc. Mọi file khác (tao_du_lieu.py,
# app.py) đều lấy từ đây, nên bác sĩ chỉ phải ký duyệt MỘT chỗ và không bao giờ
# có chuyện file này ghi một ngưỡng còn file kia ghi ngưỡng khác.
#
# Vì sao phải chia theo tuổi? Trẻ càng nhỏ thở càng nhanh. Một bé 2 tuổi thở 30
# lần/phút là HOÀN TOÀN BÌNH THƯỜNG, nhưng người lớn thở 30 lần/phút là dấu hiệu
# suy hô hấp. Dùng một ngưỡng cố định cho mọi lứa tuổi sẽ báo động giả với gần
# như mọi trẻ nhỏ — xem bài học của ca TC19 trong ca_kinh_dien.py.


def nhip_tho_binh_thuong(tuoi):
    """Nhịp thở BÌNH THƯỜNG theo tuổi (lần/phút).

    Nguồn: bảng nhịp thở theo tuổi của WHO (cần bác sĩ xác nhận lại).
    """
    if tuoi < 1:
        return 40
    if tuoi < 3:
        return 30
    if tuoi < 6:
        return 25
    if tuoi < 12:
        return 20
    return 16


def nguong_tho_nhanh_nguy_hiem(tuoi):
    """Ngưỡng thở nhanh ĐÁNG BÁO ĐỘNG ĐỎ theo tuổi (lần/phút).

    Lấy theo tiêu chí "thở nhanh" (fast breathing) của WHO trong hướng dẫn xử
    trí nhiễm khuẩn hô hấp cấp ở trẻ em, ghép với ngưỡng người lớn:

        dưới 1 tuổi : > 50
        1 – 4 tuổi  : > 40
        từ 5 tuổi   : > 30

    Cần bác sĩ xác nhận lại.
    """
    if tuoi < 1:
        return 50
    if tuoi < 5:
        return 40
    return 30


def nguong_tho_hoi_nhanh(tuoi):
    """Ngưỡng nhịp thở "HƠI nhanh" — chưa báo động đỏ nhưng đáng chú ý (lớp 3).

    Công thức: mức bình thường của tuổi đó CỘNG 6, nhưng luôn phải nằm THẤP HƠN
    ngưỡng báo động đỏ của cùng tuổi đó.

    Vì sao cần phần kẹp (`min`)? Vì hai bảng tra chia nhóm tuổi KHÁC NHAU, nên ở
    đúng mốc 5 tuổi chúng chồng chéo ngược nhau:

        trẻ 5 tuổi: bình thường 25 → "hơi nhanh" = 25 + 6 = 31
                    nhưng ngưỡng BÁO ĐỘNG ĐỎ của tuổi này chỉ là 30

    Tức là ngưỡng "hơi nhanh" còn CAO HƠN ngưỡng báo động — dải "Cần chú ý" của
    trẻ 5 tuổi rỗng hoàn toàn. Hậu quả đo được: một bé 5 tuổi thở 30 lần/phút
    (bình thường của tuổi này là 25) KHÔNG trúng quy tắc đỏ (cần > 30) và cũng
    KHÔNG được đếm là dấu hiệu đáng ngờ (cần > 31) — nên lớp hậu kiểm không nhìn
    thấy nó, còn thẻ chỉ số trên màn hình tô XANH "Bình thường".

    Với mọi lứa tuổi khác, phần kẹp không đổi gì: người từ 12 tuổi vẫn là 22,
    nhũ nhi vẫn 46, trẻ 1–2 tuổi vẫn 36, trẻ 3–4 tuổi vẫn 31, trẻ 6–11 tuổi vẫn 26.
    """
    return min(
        nhip_tho_binh_thuong(tuoi) + 6,
        nguong_tho_nhanh_nguy_hiem(tuoi) - 1,
    )


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

    # Quy tắc 1: SpO2 rất thấp thì nguy hiểm kể cả khi bệnh nhân chưa thấy khó thở.
    # Bài học y khoa: có bệnh nhân thiếu oxy nặng mà vẫn tỉnh táo, không thấy
    # khó thở ("silent hypoxia"). Không được bỏ sót nhóm này.
    #
    # Quy tắc 1b: thiếu oxy nhẹ hơn (90–91%) nhưng KÈM khó thở — cũng là suy hô hấp.
    #
    # Hai nhánh dùng elif chứ không phải hai if riêng: một ca SpO2 88% có khó thở
    # trúng cả hai điều kiện, và bản trước in ra hai dòng lý do gần trùng nhau
    # ("SpO2 88% kèm khó thở" + "SpO2 88% rất thấp"), làm loãng phần giải thích.
    if ca["spo2"] < 90:
        # Phần đuôi câu phải đổi theo ca. Bản trước luôn ghi "nguy hiểm kể cả khi
        # bệnh nhân chưa thấy khó thở" ngay cả khi vừa ghi "kèm khó thở" ở đầu
        # câu, nên dòng lý do tự nói ngược chính nó ngay trên màn hình và trên
        # phiếu in: "SpO2 = 88% rất thấp (dưới 90%) kèm khó thở → nguy hiểm kể
        # cả khi bệnh nhân chưa thấy khó thở".
        if ca["dyspnea"] == 1:
            ly_do.append(
                f"SpO2 = {ca['spo2']}% rất thấp (dưới 90%) kèm khó thở "
                f"→ dấu hiệu suy hô hấp nặng"
            )
        else:
            ly_do.append(
                f"SpO2 = {ca['spo2']}% rất thấp (dưới 90%) → nguy hiểm kể cả "
                f"khi bệnh nhân chưa thấy khó thở"
            )
    elif ca["spo2"] < 92 and ca["dyspnea"] == 1:
        ly_do.append(
            f"SpO2 = {ca['spo2']}% (dưới ngưỡng 92%) kèm khó thở "
            f"→ dấu hiệu suy hô hấp"
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
    # Ngưỡng phải theo TUỔI. Bản trước dùng cố định "> 30 và tuổi >= 12", nên có
    # hai lỗi: trẻ 5–11 tuổi thở 45 lần/phút KHÔNG trúng quy tắc nào (bỏ sót),
    # còn trẻ nhỏ thì bị ngưỡng người lớn áp lên (báo động thừa).
    nguong_nguy_hiem = nguong_tho_nhanh_nguy_hiem(ca["age"])
    if ca["respiratory_rate"] > nguong_nguy_hiem:
        ly_do.append(
            f"Nhịp thở {ca['respiratory_rate']} lần/phút (trên ngưỡng "
            f"{nguong_nguy_hiem} của tuổi {ca['age']}) → dấu hiệu suy hô hấp"
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

    # Điều kiện là spo2 < 95, KHÔNG phải 92 <= spo2 < 95.
    #
    # Bản trước bỏ trống khoảng 90–91%, và chỉ khoảng đó thôi: SpO2 dưới 90% thì
    # quy tắc cảnh báo đỏ đã bắt, SpO2 90–91% KÈM khó thở cũng bị quy tắc 1b bắt,
    # nhưng SpO2 90–91% mà KHÔNG khó thở thì không trúng quy tắc nào — và cũng
    # không được đếm là dấu hiệu đáng ngờ. Hậu quả là thang đánh giá bị NGƯỢC:
    #
    #     SpO2 93% + sốt 38.6°C  →  2 dấu hiệu  →  hậu kiểm nâng lên Trung bình
    #     SpO2 91% + sốt 38.6°C  →  1 dấu hiệu  →  vẫn để nguyên mức Thấp
    #
    # Bệnh nhân thiếu oxy NẶNG HƠN lại được xếp nhẹ hơn. Đó đúng là loại sai mà
    # lớp hậu kiểm được dựng ra để chặn.
    if ca["spo2"] < 95:
        if ca["spo2"] < 92:
            dau_hieu.append(
                f"SpO2 = {ca['spo2']}% thấp (dưới ngưỡng 92%), chưa kèm khó thở "
                f"nên chưa trúng quy tắc cảnh báo đỏ"
            )
        else:
            dau_hieu.append(f"SpO2 = {ca['spo2']}% hơi thấp (bình thường >= 95%)")

    # Ngưỡng "hơi nhanh" = mức bình thường CỦA TUỔI ĐÓ cộng 6, có kẹp để không
    # bao giờ vượt ngưỡng báo động đỏ của cùng tuổi — xem nguong_tho_hoi_nhanh().
    # Với người từ 12 tuổi: 16 + 6 = 22, đúng bằng ngưỡng cũ nên người lớn không
    # đổi gì. Nhưng bản cũ dùng số 22 cố định cho mọi lứa tuổi, nên 98% trẻ dưới
    # 6 tuổi có nhãn nguy cơ THẤP vẫn bị gắn cờ "thở nhanh", và 48% trong số đó
    # bị lớp hậu kiểm nâng oan từ Thấp lên Trung bình.
    nguong_chu_y = nguong_tho_hoi_nhanh(ca["age"])
    if ca["respiratory_rate"] > nguong_chu_y:
        dau_hieu.append(
            f"Nhịp thở {ca['respiratory_rate']} lần/phút hơi nhanh "
            f"(bình thường ở tuổi {ca['age']} là khoảng "
            f"{nhip_tho_binh_thuong(ca['age'])})"
        )
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


def dau_hieu_nang_don_doc(ca):
    """Các chỉ số đã ở MỨC BẤT THƯỜNG mà một mình nó cũng không được bỏ qua.

    Vì sao cần hàm này?
    -------------------
    Lớp hậu kiểm cũ chỉ nâng mức khi có TỪ 2 dấu hiệu đáng ngờ trở lên. Nhưng
    một chỉ số bất thường nặng mà đứng MỘT MÌNH thì chỉ được đếm là 1 dấu hiệu,
    nên không đủ để nâng — và nếu bộ quy tắc cảnh báo đỏ cũng không bắt được thì
    AI được toàn quyền kết luận ca đó AN TOÀN. Đúng cái điều mà nguyên tắc cốt
    lõi của hệ thống nói KHÔNG BAO GIỜ được phép xảy ra.

    Hai ca đo được thật, trên đúng mô hình đang chạy:

        Nhiệt độ 42.0°C, mọi thứ khác bình thường  →  hệ thống kết luận "Thấp"
        SpO2 90%, người 30 tuổi, không khó thở      →  hệ thống kết luận "Thấp"

    Với 42°C thì quy tắc cảnh báo đỏ số 5 không bắt (nó còn đòi thêm "bệnh > 3
    ngày" VÀ "mệt nhiều"), còn hậu kiểm chỉ đếm được 1 dấu hiệu. Trên màn hình,
    thẻ chỉ số ghi "Nhiệt độ 42.0°C — Bất thường" màu ĐỎ ngay bên cạnh dòng chữ
    "Nguy cơ THẤP" màu XANH: hai kết luận trái ngược nhau trên cùng một khung.

    Hai ngưỡng dùng ở đây KHÔNG phải ngưỡng mới: chúng đúng bằng ngưỡng đã có
    trong PHẦN 1 của phiếu duyệt (SpO2 < 92 ở quy tắc 2, nhiệt độ > 39 ở quy tắc
    6) — cũng chính là hai ngưỡng khiến thẻ chỉ số trên màn hình chuyển sang màu
    đỏ "Bất thường". Nhờ vậy màu của thẻ chỉ số và mức nguy cơ không bao giờ còn
    nói ngược nhau, mà không phải tự nghĩ ra con số y khoa nào mới.

    Đây CHỈ nâng lên Trung bình ("cần nhân viên y tế xem trong hôm nay"), KHÔNG
    nâng lên Cao — vì thiếu các dấu hiệu đi kèm nên chưa đủ căn cứ báo động đỏ.

    Trả về danh sách mô tả; danh sách rỗng nghĩa là không có dấu hiệu nào loại này.
    """
    nang = []
    if ca["spo2"] < 92:
        nang.append(
            f"SpO2 = {ca['spo2']}% đã dưới ngưỡng 92% — không được xếp mức Thấp "
            f"dù chưa có dấu hiệu nào khác"
        )
    if ca["temperature"] > 39:
        nang.append(
            f"Nhiệt độ {ca['temperature']}°C là sốt cao (trên 39°C) — không được "
            f"xếp mức Thấp dù chưa có dấu hiệu nào khác"
        )
    return nang


def hau_kiem(muc_ai, ca):
    """Lớp an toàn cuối: không cho AI nói "Thấp" quá dễ dàng.

    Nâng lên TRUNG BÌNH khi AI nói THẤP mà ca thuộc một trong hai trường hợp:
        1. Có TỪ 2 dấu hiệu đáng ngờ trở lên (dem_dau_hieu_dang_ngo), hoặc
        2. Có ÍT NHẤT MỘT chỉ số đã ở mức bất thường nặng (dau_hieu_nang_don_doc)

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

    nang_don_doc = dau_hieu_nang_don_doc(ca)
    if nang_don_doc:
        ly_do = (
            "AI đánh giá mức Thấp, nhưng có chỉ số đã ở mức bất thường nên hệ "
            "thống nâng lên mức Trung bình cho an toàn: "
            + "; ".join(nang_don_doc)
        )
        return 1, ly_do

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
            else:
                # Dùng ĐÚNG hau_kiem() của lớp 3 thay vì chép lại điều kiện
                # "len(...) >= 2" ở đây. Bản trước chép tay, nên khi lớp 3 học
                # thêm cách nâng mức mới (dấu hiệu nặng đơn độc) thì baseline này
                # vẫn dùng luật cũ — hai chỗ lệch nhau mà không có lỗi nào báo ra,
                # và bảng so sánh mô hình trong báo cáo thành so sánh sai.
                muc, _ = hau_kiem(0, ca)
                ket_qua.append(muc)

        return np.array(ket_qua)
