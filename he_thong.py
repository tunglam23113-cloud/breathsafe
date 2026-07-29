"""Hệ thống BreathSafe hoàn chỉnh — ghép 3 lớp an toàn lại với nhau.

Đây là trái tim của đề tài. Mô hình AI chỉ là MỘT trong ba lớp.

    Đầu vào
       ↓
    [LỚP 1] Rule Engine cảnh báo đỏ ──trúng quy tắc──→ CAO ngay, không hỏi AI
       ↓ (không trúng)
    [LỚP 0] Kiểm tra ca lạ (OOD) ──ca quá lạ──→ Từ chối dự đoán, khuyến cáo
       ↓                                          chuyển tuyến
    [LỚP 2] AI phân loại 3 mức
       ↓
    [LỚP 3] Hậu kiểm ──AI nói Thấp nhưng có >= 2 dấu hiệu đáng ngờ──→ nâng lên
       ↓                                                              Trung bình
    Kết quả + giải thích

Vì sao phải làm phức tạp thế, sao không để AI quyết hết?
--------------------------------------------------------
Vì AI không bao giờ được phép một mình kết luận rằng một ca là AN TOÀN.
Bỏ sót một ca viêm phổi nặng có thể khiến một người chết. Báo động giả chỉ khiến
nhân viên y tế mất vài phút xem lại. Hai sai lầm đó KHÔNG ngang nhau, nên hệ
thống cố tình lệch về phía cẩn thận.

Ví dụ có thật từ chính đề tài này: khi em thử chỉ dùng AI trên bộ 20 ca kinh
điển, mô hình xếp ca croup (bé 3 tuổi khó thở, SpO2 95%) vào mức Trung bình,
vì SpO2 95% trông vẫn ổn. Nhưng sách y khoa nói trẻ nhỏ khó thở là cấp cứu.
Rule Engine bắt được ca này còn AI thì không — đó chính là lý do lớp 1 tồn tại.
"""

import numpy as np

from dac_trung import MUC_NGUY_CO, TEN_TIENG_VIET
from quy_tac import dem_dau_hieu_dang_ngo, hau_kiem, kiem_tra_canh_bao_do


class KetQua:
    """Kết quả sàng lọc của một ca, kèm đầy đủ lý do để hiển thị."""

    def __init__(self, muc, do_tin_cay, nguon, ly_do, xac_suat=None, ood=None):
        self.muc = muc                    # 0 / 1 / 2
        self.ten_muc = MUC_NGUY_CO[muc]   # "Thấp" / "Trung bình" / "Cao"
        self.do_tin_cay = do_tin_cay      # xác suất đã hiệu chuẩn (0.0 - 1.0)
        self.nguon = nguon                # "quy_tac" / "ai" / "hau_kiem"
        self.ly_do = ly_do                # danh sách câu giải thích
        self.xac_suat = xac_suat or {}    # xác suất cả 3 mức
        self.ood = ood                    # kết quả kiểm tra ca lạ

    @property
    def la_ca_la(self):
        """Ca này có lạ so với dữ liệu training không?"""
        return self.ood is not None and self.ood.is_ood

    @property
    def nen_tin_ai(self):
        """Có nên tin kết quả AI cho ca này không?

        Nếu ca trúng quy tắc cảnh báo đỏ thì kết quả KHÔNG đến từ AI, nên
        chuyện AI đáng tin hay không cũng không còn quan trọng.
        """
        if self.nguon == "quy_tac":
            return True
        return not self.la_ca_la


class HeThongBreathSafe:
    """Hệ thống hoàn chỉnh: Rule Engine + AI + Hậu kiểm.

    Ví dụ dùng:
        from health_core import RiskScreeningModel

        mo_hinh = RiskScreeningModel.load("mo_hinh_breathsafe.joblib")
        he_thong = HeThongBreathSafe(mo_hinh)

        ket_qua = he_thong.danh_gia({"age": 3, "spo2": 95, "dyspnea": 1, ...})
        print(ket_qua.ten_muc)   # "Cao"
        print(ket_qua.nguon)     # "quy_tac" — do Rule Engine bắt được, không phải AI
    """

    # Cho health_core biết hệ thống này phân loại 3 lớp nào.
    classes_ = [0, 1, 2]

    def __init__(self, mo_hinh_ai):
        """Tham số: mo_hinh_ai — một RiskScreeningModel đã huấn luyện."""
        self.mo_hinh_ai = mo_hinh_ai
        self.dac_trung = mo_hinh_ai.feature_names

    # ------------------------------------------------------------------
    # Đánh giá một ca — dùng cho giao diện
    # ------------------------------------------------------------------

    def danh_gia(self, ca):
        """Sàng lọc một ca qua đủ 3 lớp. Trả về KetQua.

        Tham số:
            ca: dict thông tin bệnh nhân
        """
        thieu = set(self.dac_trung) - set(ca.keys())
        if thieu:
            raise ValueError(
                f"Ca bệnh thiếu các thông tin: "
                f"{', '.join(TEN_TIENG_VIET.get(t, t) for t in sorted(thieu))}"
            )

        # Có ĐỦ TÊN cột chưa đủ — giá trị bên trong cũng phải là số thật.
        #
        # Vì sao phải chặn ở đây? Vì Random Forest của scikit-learn từ bản 1.4
        # xử lý được giá trị thiếu (NaN) mà KHÔNG báo lỗi: nó tự chọn một nhánh
        # rồi trả về một dự đoán trông hoàn toàn bình thường, kèm cả phần trăm
        # độ tin cậy. Thử thật trên ca TC01 bỏ trống SpO2: hệ thống vẫn kết luận
        # "Cao" — đúng đáp án, nhưng là đúng do may, vì nó không hề đọc được chỉ
        # số quan trọng nhất. Với một ca khác, nó sẽ tự tin sai y như vậy.
        #
        # Ở một công cụ sàng lọc, "không biết" phải khác "bình thường". Thiếu
        # số đo thì từ chối trả lời, để người dùng đi đo lại.
        rong = []
        for ten in self.dac_trung:
            gia_tri = ca[ten]
            try:
                so = float(gia_tri)
            except (TypeError, ValueError):
                rong.append(TEN_TIENG_VIET.get(ten, ten))
                continue
            if so != so:  # NaN là giá trị duy nhất khác chính nó
                rong.append(TEN_TIENG_VIET.get(ten, ten))
        if rong:
            raise ValueError(
                f"Các thông tin sau đang để trống hoặc không phải số: "
                f"{', '.join(rong)}. Hệ thống không đoán thay khi thiếu số đo — "
                f"hãy đo lại rồi nhập đầy đủ."
            )

        # --- LỚP 1: Quy tắc cảnh báo đỏ -------------------------------
        # Chạy TRƯỚC AI. Nếu trúng, kết luận CAO ngay và không cần hỏi AI.
        canh_bao_do = kiem_tra_canh_bao_do(ca)
        if canh_bao_do:
            # Vẫn chạy AI để lấy xác suất hiển thị tham khảo, nhưng KHÔNG dùng
            # kết quả của nó để quyết định. Quy tắc y khoa thắng.
            du_doan_ai = self.mo_hinh_ai.predict(ca)
            return KetQua(
                muc=2,
                do_tin_cay=1.0,  # quy tắc y khoa là chắc chắn, không phải xác suất
                nguon="quy_tac",
                ly_do=canh_bao_do,
                xac_suat=du_doan_ai.probabilities,
                ood=du_doan_ai.ood,
            )

        # --- LỚP 2: AI phân loại --------------------------------------
        du_doan_ai = self.mo_hinh_ai.predict(ca)

        # --- LỚP 3: Hậu kiểm ------------------------------------------
        muc_cuoi, ly_do_nang = hau_kiem(du_doan_ai.risk_index, ca)

        if ly_do_nang:
            return KetQua(
                muc=muc_cuoi,
                do_tin_cay=du_doan_ai.confidence,
                nguon="hau_kiem",
                ly_do=[ly_do_nang],
                xac_suat=du_doan_ai.probabilities,
                ood=du_doan_ai.ood,
            )

        return KetQua(
            muc=muc_cuoi,
            do_tin_cay=du_doan_ai.confidence,
            nguon="ai",
            ly_do=self._giai_thich_ai(ca, du_doan_ai),
            xac_suat=du_doan_ai.probabilities,
            ood=du_doan_ai.ood,
        )

    def _giai_thich_ai(self, ca, du_doan):
        """Sinh câu giải thích khi kết quả đến từ AI.

        LƯU Ý VỀ TÍNH TRUNG THỰC: đây KHÔNG phải lời giải thích thật sự của mô
        hình. Random Forest có 200 cây, không thể nói chính xác vì sao nó chọn
        mức này cho ca này. Những gì hiển thị ở đây là các dấu hiệu bất thường
        mà em tự kiểm tra bằng quy tắc, cộng với danh sách thông tin mà mô hình
        nói chung dựa vào nhiều nhất.

        Muốn giải thích đúng từng ca thì phải dùng SHAP — nằm ngoài phạm vi đề
        tài này. Trong báo cáo phải ghi rõ điều này, đừng nói quá.
        """
        ly_do = dem_dau_hieu_dang_ngo(ca)

        if not ly_do:
            if du_doan.risk_index == 0:
                return ["Các dấu hiệu sinh tồn đều trong giới hạn bình thường."]
            ly_do = ["Mô hình nhận thấy tổ hợp các dấu hiệu đáng chú ý."]

        quan_trong = ", ".join(
            TEN_TIENG_VIET.get(ten, ten) for ten, _ in self.mo_hinh_ai.top_features(3)
        )
        ly_do.append(
            f"(Nói chung, mô hình dựa nhiều nhất vào: {quan_trong}. "
            f"Đây là mức quan trọng trung bình của mô hình, không phải lý do "
            f"riêng cho ca này.)"
        )
        return ly_do

    # ------------------------------------------------------------------
    # Đánh giá nhiều ca — dùng cho chấm điểm tập test
    # ------------------------------------------------------------------

    def predict(self, X):
        """Dự đoán mức nguy cơ cho nhiều ca (giống giao diện sklearn).

        Nhờ hàm này, hệ thống 3 lớp có thể đem so sánh trực tiếp với các mô hình
        khác bằng compare_models().
        """
        X = np.asarray(X.values if hasattr(X, "values") else X, dtype=float)
        ket_qua = []
        for hang in X:
            ca = dict(zip(self.dac_trung, hang))
            ket_qua.append(self.danh_gia(ca).muc)
        return np.array(ket_qua)


def in_ket_qua(ket_qua, ca):
    """In kết quả ra màn hình theo đúng mẫu trong kế hoạch.

    Dùng khi test nhanh bằng dòng lệnh. Giao diện Streamlit hiển thị đẹp hơn.
    """
    dong = "=" * 62
    print(dong)
    print("KẾT QUẢ SÀNG LỌC")
    print(dong)
    print(f"\nMức nguy cơ: {ket_qua.ten_muc.upper()}")

    if ket_qua.nguon == "quy_tac":
        print("Nguồn: Quy tắc cảnh báo đỏ (không dùng AI cho ca này)")
    elif ket_qua.nguon == "hau_kiem":
        print("Nguồn: Lớp hậu kiểm nâng mức (AI ban đầu đánh giá thấp hơn)")
        print(f"Độ tin cậy của AI: {ket_qua.do_tin_cay:.0%} (đã hiệu chuẩn)")
    else:
        print(f"Độ tin cậy: {ket_qua.do_tin_cay:.0%} (đã hiệu chuẩn)")

    if ket_qua.la_ca_la:
        print("\n*** CẢNH BÁO CA LẠ ***")
        print(ket_qua.ood.message)

    print("\nLý do:")
    for x in ket_qua.ly_do:
        print(f"  - {x}")

    print("\nKhuyến nghị:")
    if ket_qua.muc == 2:
        print("  - Cần nhân viên y tế kiểm tra NGAY")
        print("  - Cân nhắc hội chẩn hoặc chuyển tuyến")
        print("  - Không tự ý dùng thuốc")
    elif ket_qua.muc == 1:
        print("  - Nên được nhân viên y tế khám trong hôm nay")
        print("  - Theo dõi sát, nếu nặng lên phải đi khám ngay")
    else:
        print("  - Theo dõi tại nhà, nghỉ ngơi, uống đủ nước")
        print("  - Nếu xuất hiện khó thở hoặc sốt cao kéo dài, đi khám ngay")

    print(f"\n{dong}")
    print("Hệ thống chỉ hỗ trợ sàng lọc, KHÔNG thay thế chẩn đoán của bác sĩ.")
    print(dong)
