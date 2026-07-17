"""Bộ 20 ca lâm sàng kinh điển — bằng chứng hệ thống hiểu y khoa.

Vì sao cần file này?
--------------------
Giám khảo không có thời gian đọc 2.000 dòng dữ liệu mô phỏng. Nhưng họ sẽ hỏi:
"Hệ thống của em có xử lý đúng các ca kinh điển trong sách y khoa không?"

Mỗi ca ở đây là một BÀI HỌC Y KHOA nổi tiếng — một tình huống mà người mới
thường đánh giá sai. Bộ này kiểm tra mô hình theo kiểu "clinical validation",
khác với đo accuracy trung bình trên tập test.

Bộ ca có cả ca nặng lẫn ĐỐI CHỨNG ÂM (ca nhẹ). Đối chứng âm rất quan trọng: nếu
chỉ toàn ca nặng, một mô hình luôn nói "Cao" sẽ đạt 100% — mà mô hình đó vô dụng.
Bộ này có 5 ca đối chứng âm (TC04, TC07, TC14, TC15, TC19).

================================================================================
CẢNH BÁO QUAN TRỌNG VỀ TÍNH TRUNG THỰC
================================================================================
Các con số và nhãn trong file này do HỌC SINH soạn dựa trên tài liệu y khoa phổ
thông. Chúng CHƯA CÓ GIÁ TRỊ CHUYÊN MÔN cho đến khi bác sĩ tư vấn:
    1. Đọc lại từng ca
    2. Sửa các giá trị chưa hợp lý
    3. Xác nhận cột 'expected_label'
    4. KÝ TÊN vào bản in

Khi giám khảo hỏi "ai bảo đó là đáp án đúng?", câu trả lời phải là tờ giấy có
chữ ký bác sĩ, KHÔNG phải "em tự nghĩ" hay "em hỏi AI".

Trước khi có chữ ký, hãy để BS_DA_KY = False. App sẽ hiển thị cảnh báo.
================================================================================
"""

# ---------------------------------------------------------------------------
# XÁC NHẬN CHUYÊN MÔN
# ---------------------------------------------------------------------------
# CHỈ đổi BS_DA_KY thành True SAU KHI đã cầm trong tay bản in có chữ ký thật.
# Điền TÊN THẬT và NGÀY THẬT của bác sĩ đã ký — không điền tên ví dụ.
#
# Khi BS_DA_KY = True, app sẽ gỡ mọi cảnh báo và hiển thị "Bộ ca đã được duyệt
# bởi: <tên>" cho người xem. Nếu tên đó không có thật, app đang nói dối thay bạn.
#
# Cú pháp Python: viết True / False (T và F hoa, phần còn lại thường).
# Viết TRUE hay true đều làm chương trình chết với lỗi NameError.
BS_DA_KY = False
TEN_BAC_SI_DUYET = ""  # Điền sau khi ký, ví dụ dạng: "BS. <họ tên> — <nơi công tác>"
NGAY_DUYET = ""  # Ngày ký thật, dạng YYYY-MM-DD


CA_KINH_DIEN = [
    # ======================================================================
    # NHÓM 1: Các ca mà dấu hiệu "kinh điển" lại VẮNG MẶT
    # ======================================================================
    {
        "id": "TC01",
        "name": "Viêm phổi không điển hình ở người già",
        "description": "Cụ ông 78 tuổi, KHÔNG sốt rõ (37.5°C), nhưng SpO2 91%, "
                       "thở 24 lần/phút, mệt nhiều, ho khan 4 ngày.",
        "input": {
            "age": 78, "fever": 0, "temperature": 37.5, "cough": 1,
            "dyspnea": 1, "spo2": 91, "respiratory_rate": 24,
            "chest_pain": 0, "fatigue": 1, "days_sick": 4, "comorbidity": 1,
        },
        "expected_label": "Cao",
        "lesson": "Người già có thể KHÔNG sốt rõ dù viêm phổi nặng. Mô hình "
                  "KHÔNG được dựa quá nhiều vào sốt.",
    },
    {
        "id": "TC03",
        "name": "Thuyên tắc phổi — phổi nghe sạch",
        "description": "Nữ 45 tuổi, đột ngột khó thở, đau ngực, SpO2 88%, "
                       "KHÔNG sốt, KHÔNG ho. Mới đi máy bay đường dài.",
        "input": {
            "age": 45, "fever": 0, "temperature": 36.8, "cough": 0,
            "dyspnea": 1, "spo2": 88, "respiratory_rate": 26,
            "chest_pain": 1, "fatigue": 1, "days_sick": 0, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Khó thở + đau ngực đột ngột mà KHÔNG sốt KHÔNG ho là dấu "
                  "hiệu thuyên tắc phổi — không được bỏ sót chỉ vì thiếu sốt và ho.",
    },
    {
        "id": "TC18",
        "name": "Lao kê — sốt kéo dài, ho rất ít",
        "description": "Nam 35 tuổi, sốt 38.6°C kéo dài 21 ngày, ho ít, "
                       "mệt nhiều, sụt cân. SpO2 93%.",
        "input": {
            "age": 35, "fever": 1, "temperature": 38.6, "cough": 1,
            "dyspnea": 0, "spo2": 93, "respiratory_rate": 22,
            "chest_pain": 0, "fatigue": 1, "days_sick": 21, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Sốt kéo dài trên 2 tuần là dấu hiệu bệnh nặng dù triệu chứng "
                  "hô hấp nhẹ. Thời gian bệnh quan trọng không kém mức độ nặng.",
    },

    # ======================================================================
    # NHÓM 2: Cấp cứu ở trẻ em
    # ======================================================================
    {
        "id": "TC02",
        "name": "Croup (viêm thanh quản) ở trẻ nhỏ",
        "description": "Bé 3 tuổi, ho ông ổng như chó sủa, khàn tiếng, khó thở "
                       "khi hít vào, sốt 38.5°C.",
        "input": {
            "age": 3, "fever": 1, "temperature": 38.5, "cough": 1,
            "dyspnea": 1, "spo2": 95, "respiratory_rate": 30,
            "chest_pain": 0, "fatigue": 0, "days_sick": 2, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Trẻ nhỏ khó thở thanh quản là cấp cứu, dù SpO2 còn 95%. "
                  "SpO2 bình thường KHÔNG loại trừ được nguy hiểm ở trẻ.",
    },
    {
        "id": "TC12",
        "name": "Ho gà ở trẻ chưa tiêm vaccine",
        "description": "Bé 8 tháng, ho thành cơn dài rồi tím tái, chưa tiêm "
                       "vaccine, ho 10 ngày, sốt nhẹ.",
        "input": {
            "age": 1, "fever": 1, "temperature": 38.0, "cough": 1,
            "dyspnea": 1, "spo2": 93, "respiratory_rate": 42,
            "chest_pain": 0, "fatigue": 1, "days_sick": 10, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Trẻ dưới 1 tuổi ho gà có thể ngừng thở. Nhịp thở bình thường "
                  "của trẻ nhũ nhi cao hơn người lớn — ngưỡng phải khác nhau.",
    },
    {
        "id": "TC13",
        "name": "Dị vật đường thở",
        "description": "Bé 2 tuổi đang ăn hạt thì đột ngột ho sặc sụa, khó thở, "
                       "KHÔNG sốt, hoàn toàn khỏe mạnh trước đó.",
        "input": {
            "age": 2, "fever": 0, "temperature": 36.8, "cough": 1,
            "dyspnea": 1, "spo2": 92, "respiratory_rate": 38,
            "chest_pain": 0, "fatigue": 0, "days_sick": 0, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Khó thở khởi phát đột ngột ở trẻ đang khỏe = nghĩ ngay đến "
                  "dị vật. Không sốt KHÔNG có nghĩa là không nguy hiểm.",
    },

    # ======================================================================
    # NHÓM 3: Bệnh nền hô hấp và tim mạch
    # ======================================================================
    {
        "id": "TC05",
        "name": "Hen phế quản đợt cấp",
        "description": "Nữ 28 tuổi tiền sử hen, lên cơn khó thở, SpO2 92%, "
                       "thở rít, không sốt.",
        "input": {
            "age": 28, "fever": 0, "temperature": 36.7, "cough": 1,
            "dyspnea": 1, "spo2": 92, "respiratory_rate": 28,
            "chest_pain": 0, "fatigue": 1, "days_sick": 0, "comorbidity": 1,
        },
        "expected_label": "Cao",
        "lesson": "Bệnh nhân có bệnh nền hô hấp + triệu chứng nặng = nguy cơ cao, "
                  "kể cả khi SpO2 mới chỉ chạm ngưỡng.",
    },
    {
        "id": "TC11",
        "name": "COPD đợt cấp",
        "description": "Nam 68 tuổi, hút thuốc 40 năm, COPD, khó thở tăng dần "
                       "3 ngày, đờm đổi màu, SpO2 89%.",
        "input": {
            "age": 68, "fever": 1, "temperature": 38.2, "cough": 1,
            "dyspnea": 1, "spo2": 89, "respiratory_rate": 28,
            "chest_pain": 0, "fatigue": 1, "days_sick": 3, "comorbidity": 1,
        },
        "expected_label": "Cao",
        "lesson": "COPD đợt cấp là nguyên nhân nhập viện hàng đầu. Người COPD có "
                  "thể sống chung với SpO2 thấp — cần so với mức nền của họ.",
    },
    {
        "id": "TC08",
        "name": "Phù phổi cấp do suy tim",
        "description": "Cụ bà 75 tuổi suy tim, đêm khó thở phải ngồi dậy, "
                       "ho khạc bọt hồng, SpO2 87%, KHÔNG sốt.",
        "input": {
            "age": 75, "fever": 0, "temperature": 36.9, "cough": 1,
            "dyspnea": 1, "spo2": 87, "respiratory_rate": 32,
            "chest_pain": 0, "fatigue": 1, "days_sick": 1, "comorbidity": 1,
        },
        "expected_label": "Cao",
        "lesson": "Không phải khó thở nào cũng do phổi — tim cũng gây khó thở. "
                  "Hệ thống chỉ sàng lọc NGUY CƠ, không xác định nguyên nhân.",
    },
    {
        "id": "TC09",
        "name": "Tràn khí màng phổi tự phát",
        "description": "Nam 22 tuổi cao gầy, đột ngột đau ngực dữ dội một bên "
                       "và khó thở khi đang ngồi yên. Không sốt, không ho.",
        "input": {
            "age": 22, "fever": 0, "temperature": 36.6, "cough": 0,
            "dyspnea": 1, "spo2": 93, "respiratory_rate": 26,
            "chest_pain": 1, "fatigue": 0, "days_sick": 0, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Người trẻ khỏe mạnh vẫn có thể gặp cấp cứu hô hấp. Mô hình "
                  "KHÔNG được cho rằng cứ trẻ tuổi là an toàn.",
    },
    {
        "id": "TC10",
        "name": "Viêm phổi hít sặc ở người già có Parkinson",
        "description": "Cụ ông 82 tuổi Parkinson, hay sặc khi ăn, sốt 38.3°C, "
                       "ho có đờm 3 ngày, SpO2 90%, lơ mơ.",
        "input": {
            "age": 82, "fever": 1, "temperature": 38.3, "cough": 1,
            "dyspnea": 1, "spo2": 90, "respiratory_rate": 26,
            "chest_pain": 0, "fatigue": 1, "days_sick": 3, "comorbidity": 1,
        },
        "expected_label": "Cao",
        "lesson": "Người già có bệnh thần kinh dễ viêm phổi hít sặc và diễn tiến "
                  "rất nhanh.",
    },

    # ======================================================================
    # NHÓM 4: Bệnh nhiễm trùng
    # ======================================================================
    {
        "id": "TC06",
        "name": "Lao phổi giai đoạn muộn",
        "description": "Nam 52 tuổi, ho kéo dài 8 tuần, sốt về chiều, sụt cân, "
                       "ra mồ hôi đêm, mệt nhiều. SpO2 92%.",
        "input": {
            "age": 52, "fever": 1, "temperature": 38.3, "cough": 1,
            "dyspnea": 1, "spo2": 92, "respiratory_rate": 24,
            "chest_pain": 1, "fatigue": 1, "days_sick": 56, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Ho trên 2 tuần ở Việt Nam phải nghĩ đến lao. Đây còn là vấn đề "
                  "y tế công cộng — bệnh nhân có thể lây cho người khác.",
    },
    {
        "id": "TC20",
        "name": "Ung thư phổi giai đoạn muộn",
        "description": "Nam 64 tuổi hút thuốc lâu năm, ho ra máu, sụt 8kg trong "
                       "3 tháng, đau ngực, khó thở tăng dần. SpO2 91%.",
        "input": {
            "age": 64, "fever": 0, "temperature": 37.0, "cough": 1,
            "dyspnea": 1, "spo2": 91, "respiratory_rate": 24,
            "chest_pain": 1, "fatigue": 1, "days_sick": 90, "comorbidity": 1,
        },
        "expected_label": "Cao",
        "lesson": "Triệu chứng kéo dài nhiều tháng + sụt cân = dấu hiệu báo động. "
                  "Hệ thống chỉ nói 'cần khám ngay', KHÔNG được nói 'ung thư'.",
    },

    # ======================================================================
    # NHÓM 5: Ngộ độc và phản ứng cấp
    # ======================================================================
    {
        "id": "TC16",
        "name": "Ngộ độc khí CO (SpO2 đánh lừa máy đo)",
        "description": "Nam 30 tuổi ngủ trong phòng kín có đốt than, sáng dậy "
                       "đau đầu dữ dội, buồn nôn, lơ mơ. Máy đo SpO2 hiện 98%.",
        "input": {
            "age": 30, "fever": 0, "temperature": 36.5, "cough": 0,
            "dyspnea": 1, "spo2": 98, "respiratory_rate": 24,
            "chest_pain": 0, "fatigue": 1, "days_sick": 0, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "GIỚI HẠN QUAN TRỌNG NHẤT CỦA ĐỀ TÀI: máy đo SpO2 thông thường "
                  "KHÔNG phân biệt được oxy với khí CO, nên vẫn hiện 98% dù bệnh "
                  "nhân đang thiếu oxy nặng. Hệ thống của em RẤT CÓ THỂ BỎ SÓT ca "
                  "này. Đây là bằng chứng cho thấy AI không thay được bác sĩ hỏi "
                  "bệnh sử. Nếu mô hình sai ca này, PHẢI báo cáo trung thực và "
                  "phân tích trong phần Thảo luận.",
    },
    {
        "id": "TC17",
        "name": "Phản vệ do thuốc",
        "description": "Nữ 25 tuổi vừa uống kháng sinh 15 phút, nổi mề đay toàn "
                       "thân, khó thở, thở rít, tụt huyết áp. SpO2 91%.",
        "input": {
            "age": 25, "fever": 0, "temperature": 36.8, "cough": 0,
            "dyspnea": 1, "spo2": 91, "respiratory_rate": 30,
            "chest_pain": 1, "fatigue": 1, "days_sick": 0, "comorbidity": 0,
        },
        "expected_label": "Cao",
        "lesson": "Phản vệ là cấp cứu tính bằng phút. Đây là ca cho thấy hệ thống "
                  "cần hỏi thêm 'vừa dùng thuốc gì không' — một thông tin em chưa "
                  "đưa vào mô hình.",
    },

    # ======================================================================
    # NHÓM 6: ĐỐI CHỨNG ÂM — kiểm tra mô hình KHÔNG báo động thừa
    # ======================================================================
    {
        "id": "TC04",
        "name": "Cảm cúm thông thường (đối chứng âm 1)",
        "description": "Học sinh 14 tuổi, ho nhẹ, sổ mũi, sốt 37.8°C, không khó "
                       "thở, SpO2 98%, đã 2 ngày.",
        "input": {
            "age": 14, "fever": 1, "temperature": 37.8, "cough": 1,
            "dyspnea": 0, "spo2": 98, "respiratory_rate": 16,
            "chest_pain": 0, "fatigue": 0, "days_sick": 2, "comorbidity": 0,
        },
        "expected_label": "Thấp",
        "lesson": "Mô hình KHÔNG được over-alert với mọi ca có sốt + ho. Nếu ca "
                  "này bị báo Cao, trạm y tế sẽ chuyển tuyến tràn lan.",
    },
    {
        "id": "TC07",
        "name": "COVID-19 thể nhẹ ở người trẻ (đối chứng âm 2)",
        "description": "Nam 24 tuổi đã tiêm đủ vaccine, test dương tính, sốt "
                       "38.0°C, ho khan, mất khứu giác, SpO2 97%, không khó thở.",
        "input": {
            "age": 24, "fever": 1, "temperature": 38.0, "cough": 1,
            "dyspnea": 0, "spo2": 97, "respiratory_rate": 18,
            "chest_pain": 0, "fatigue": 1, "days_sick": 3, "comorbidity": 0,
        },
        "expected_label": "Thấp",
        "lesson": "Tên bệnh đáng sợ KHÔNG có nghĩa là ca nặng. Hệ thống đánh giá "
                  "theo DẤU HIỆU, không theo nhãn bệnh.",
    },
    {
        "id": "TC14",
        "name": "Viêm họng đơn thuần (đối chứng âm 3)",
        "description": "Nữ 30 tuổi, đau họng, sốt 38.2°C, ho ít, nuốt vướng, "
                       "SpO2 99%, thở bình thường, 2 ngày.",
        "input": {
            "age": 30, "fever": 1, "temperature": 38.2, "cough": 1,
            "dyspnea": 0, "spo2": 99, "respiratory_rate": 16,
            "chest_pain": 0, "fatigue": 0, "days_sick": 2, "comorbidity": 0,
        },
        "expected_label": "Thấp",
        "lesson": "Sốt gần 38.5°C vẫn có thể là bệnh nhẹ nếu hô hấp hoàn toàn "
                  "bình thường.",
    },
    {
        "id": "TC15",
        "name": "Ho do trào ngược dạ dày (đối chứng âm 4)",
        "description": "Nam 40 tuổi, ho khan kéo dài 2 tháng, nặng hơn khi nằm, "
                       "ợ chua, KHÔNG sốt, SpO2 98%, không khó thở.",
        "input": {
            "age": 40, "fever": 0, "temperature": 36.7, "cough": 1,
            "dyspnea": 0, "spo2": 98, "respiratory_rate": 16,
            "chest_pain": 0, "fatigue": 0, "days_sick": 60, "comorbidity": 0,
        },
        "expected_label": "Thấp",
        "lesson": "Ca KHÓ nhất trong nhóm đối chứng âm: ho kéo dài 60 ngày trông "
                  "rất giống lao (TC06). Điểm khác biệt là KHÔNG sốt, KHÔNG sụt "
                  "cân, dấu hiệu sinh tồn hoàn toàn bình thường. Ca này kiểm tra "
                  "mô hình có phân biệt được 'kéo dài' với 'nguy hiểm' không.",
    },
    {
        "id": "TC19",
        "name": "Viêm phế quản cấp ở trẻ nhỏ (đối chứng âm 5)",
        "description": "Bé 18 tháng, ho có đờm, sốt 38.0°C, chơi bình thường, "
                       "ăn bú tốt, SpO2 97%, không rút lõm lồng ngực.",
        "input": {
            "age": 2, "fever": 1, "temperature": 38.0, "cough": 1,
            "dyspnea": 0, "spo2": 97, "respiratory_rate": 30,
            "chest_pain": 0, "fatigue": 0, "days_sick": 3, "comorbidity": 0,
        },
        "expected_label": "Thấp",
        "lesson": "Trẻ nhỏ thở 30 lần/phút là BÌNH THƯỜNG (người lớn thì nhanh). "
                  "Mô hình phải hiểu ngưỡng nhịp thở phụ thuộc tuổi, nếu không sẽ "
                  "báo động giả với mọi trẻ nhỏ.",
    },
]


def kiem_tra_bo_ca():
    """Kiểm tra bộ ca có hợp lệ không. Chạy file này trực tiếp để kiểm tra.

    Bắt các lỗi mà mắt thường dễ bỏ sót: trùng ID, thiếu cột, nhãn viết sai.
    """
    from dac_trung import DAC_TRUNG

    loi = []

    ids = [ca["id"] for ca in CA_KINH_DIEN]
    if len(ids) != len(set(ids)):
        trung = [i for i in set(ids) if ids.count(i) > 1]
        loi.append(f"ID bị trùng: {trung}")

    for ca in CA_KINH_DIEN:
        thieu = set(DAC_TRUNG) - set(ca["input"].keys())
        if thieu:
            loi.append(f"{ca['id']} thiếu đặc trưng: {sorted(thieu)}")
        thua = set(ca["input"].keys()) - set(DAC_TRUNG)
        if thua:
            loi.append(f"{ca['id']} có đặc trưng lạ: {sorted(thua)}")
        if ca["expected_label"] not in ("Thấp", "Trung bình", "Cao"):
            loi.append(f"{ca['id']} có nhãn không hợp lệ: {ca['expected_label']}")

    return loi


if __name__ == "__main__":
    from tieng_viet import bat_tieng_viet

    bat_tieng_viet()
    loi = kiem_tra_bo_ca()

    print(f"Tổng số ca kinh điển: {len(CA_KINH_DIEN)}")
    n_cao = sum(1 for c in CA_KINH_DIEN if c["expected_label"] == "Cao")
    n_thap = sum(1 for c in CA_KINH_DIEN if c["expected_label"] == "Thấp")
    print(f"  Nguy cơ Cao:            {n_cao}")
    print(f"  Đối chứng âm (Thấp):    {n_thap}")

    if loi:
        print("\nCÓ LỖI TRONG BỘ CA:")
        for x in loi:
            print(f"  - {x}")
    else:
        print("\nBộ ca hợp lệ về mặt kỹ thuật.")

    if not BS_DA_KY:
        print(
            "\n*** CHƯA CÓ CHỮ KÝ BÁC SĨ ***\n"
            "Bộ ca này chưa có giá trị chuyên môn. Hãy in ra, nhờ bác sĩ tư vấn\n"
            "duyệt từng ca và ký tên, rồi đổi BS_DA_KY = True trong file này."
        )
