"""Ghi âm và xử lý tiếng ho.

Vì sao tách riêng file này?
---------------------------
Để app.py chỉ lo phần giao diện. Mọi thứ liên quan tới micro và âm thanh nằm ở
đây, gọn một chỗ.

Vì sao bản desktop ghi âm dễ hơn bản web?
-----------------------------------------
Khi app chạy trên chính máy của mình (chế độ desktop), thư viện `sounddevice`
ghi âm THẲNG từ micro của máy — không phải xin quyền qua trình duyệt, không bị
Chrome chặn. Đây chính là lý do đề tài chọn đóng gói thành app desktop.

Phần trích đặc trưng âm thanh (MFCC...) dùng thư viện `health-core` — cùng thư
viện chứa các phần kỹ thuật nâng cao khác. Xem bảng "ai làm gì" trong README.

LƯU Ý TRUNG THỰC: mô hình quyết định mức nguy cơ hiện dùng DẤU HIỆU LÂM SÀNG
(SpO2, nhịp thở, triệu chứng). Phần phân tích âm thanh là một hướng nghiên cứu
riêng — app trích và hiển thị đặc trưng để chứng minh quy trình chạy được, chứ
CHƯA đưa âm thanh vào quyết định. Đừng nói quá về điều này khi trình bày.
"""

from __future__ import annotations

import io

import numpy as np

TAN_SO_MAU = 22050  # số mẫu mỗi giây; librosa mặc định dùng giá trị này


def co_micro() -> bool:
    """Máy có thiết bị thu âm (micro) không?

    Dùng để tắt nút ghi âm trên máy không có micro, thay vì để nó bấm rồi lỗi.
    """
    try:
        import sounddevice as sd

        thiet_bi = sd.query_devices()
        return any(d["max_input_channels"] > 0 for d in thiet_bi)
    except Exception:
        return False


def ghi_am(giay: int = 5, tan_so: int = TAN_SO_MAU):
    """Ghi âm `giay` giây từ micro của máy.

    Trả về (mảng biên độ sóng âm, tần số mẫu).

    Hàm này CHẶN chương trình trong lúc ghi (đứng chờ đủ số giây rồi mới trả về).
    Với một nút bấm ghi âm 5 giây thì chấp nhận được.
    """
    import sounddevice as sd

    so_mau = int(giay * tan_so)
    am = sd.rec(so_mau, samplerate=tan_so, channels=1, dtype="float32")
    sd.wait()  # đợi ghi xong
    return am.reshape(-1), tan_so


def doc_file(du_lieu_bytes: bytes):
    """Đọc một file âm thanh đã tải lên (.wav, .mp3, .ogg...).

    Trả về (mảng biên độ, tần số). File 2 kênh (stereo) được gộp thành 1 kênh
    (mono) để đồng nhất với dữ liệu ghi từ micro.
    """
    import soundfile as sf

    y, sr = sf.read(io.BytesIO(du_lieu_bytes), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    return y, int(sr)


def trich_dac_trung(y, sr) -> dict:
    """Trích 35 đặc trưng âm thanh (MFCC, spectral...) từ đoạn ghi.

    Dùng thư viện health-core. Trả về dict {tên đặc trưng: giá trị}.
    """
    from health_core import audio

    return audio.extract_features_from_array(y, sr)


def song_am_rut_gon(y, so_diem: int = 280):
    """Rút gọn sóng âm còn khoảng `so_diem` điểm để vẽ waveform cho nhẹ.

    Sóng âm gốc có hàng chục nghìn điểm — vẽ hết vừa chậm vừa rối. Ở đây chia
    thành `so_diem` đoạn, mỗi đoạn lấy biên độ lớn nhất, tạo thành "đường bao"
    (envelope) nhìn giống hình sóng trên các app ghi âm.
    """
    y = np.abs(np.asarray(y, dtype=float))
    if y.size == 0:
        return np.zeros(so_diem)
    buoc = max(1, y.size // so_diem)
    n = (y.size // buoc) * buoc
    return y[:n].reshape(-1, buoc).max(axis=1)


def luu_wav(y, sr, duong_dan) -> None:
    """Lưu đoạn ghi ra file .wav (để dành làm dữ liệu nghiên cứu nếu cần).

    Nhớ: chỉ lưu khi người được ghi đã ĐỒNG Ý, và không kèm tên hay thông tin
    định danh nào — xem phần đạo đức dữ liệu trong báo cáo.
    """
    import soundfile as sf

    sf.write(str(duong_dan), np.asarray(y, dtype="float32"), int(sr))
