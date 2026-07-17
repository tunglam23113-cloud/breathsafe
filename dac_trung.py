"""Danh sách các thông tin (đặc trưng) mà BreathSafe dùng.

File này chỉ chứa DANH SÁCH TÊN, không có tính toán gì. Mục đích: mọi file khác
đều lấy thứ tự cột từ đây, nên không bao giờ bị lệch cột.

Vì sao thứ tự quan trọng? Mô hình học máy chỉ nhìn thấy các con số, không thấy
tên cột. Nếu lúc train cột thứ 6 là SpO2 mà lúc dự đoán cột thứ 6 lại là nhịp
thở, mô hình sẽ đọc nhầm hoàn toàn mà không báo lỗi.
"""

# 11 thông tin mà mô hình dùng để dự đoán, ĐÚNG THỨ TỰ NÀY.
DAC_TRUNG = [
    "age",               # Tuổi (năm)
    "fever",             # Có sốt không (0 = không, 1 = có)
    "temperature",       # Nhiệt độ đo được (°C)
    "cough",             # Có ho không (0/1)
    "dyspnea",           # Có khó thở không (0/1)
    "spo2",              # Nồng độ oxy trong máu (%)
    "respiratory_rate",  # Nhịp thở (lần/phút)
    "chest_pain",        # Có đau ngực không (0/1)
    "fatigue",           # Có mệt nhiều không (0/1)
    "days_sick",         # Số ngày đã mắc bệnh
    "comorbidity",       # Có bệnh nền không (0/1)
]

# Tên tiếng Việt để hiển thị lên màn hình.
TEN_TIENG_VIET = {
    "age": "Tuổi",
    "fever": "Sốt",
    "temperature": "Nhiệt độ",
    "cough": "Ho",
    "dyspnea": "Khó thở",
    "spo2": "SpO2 (oxy trong máu)",
    "respiratory_rate": "Nhịp thở",
    "chest_pain": "Đau ngực",
    "fatigue": "Mệt nhiều",
    "days_sick": "Số ngày bệnh",
    "comorbidity": "Bệnh nền",
}

# Ba mức nguy cơ mà hệ thống phân loại.
MUC_NGUY_CO = {0: "Thấp", 1: "Trung bình", 2: "Cao"}

# Ghi chú về giới tính (gender):
# Dữ liệu có thu thập giới tính để phân tích, NHƯNG mô hình KHÔNG dùng nó làm
# đặc trưng. Hai lý do:
#   1. Các tài liệu y khoa em tham khảo không cho thấy giới tính làm thay đổi
#      ngưỡng nguy hiểm của SpO2 hay nhịp thở.
#   2. Đưa vào mà không có cơ sở rõ ràng thì mô hình có thể học ra thiên lệch
#      (bias) — ví dụ cảnh báo nhẹ hơn cho một giới nào đó chỉ vì tình cờ trong
#      dữ liệu mô phỏng. Không đưa vào là lựa chọn an toàn hơn.
