"""Mở BreathSafe như một app desktop (cửa sổ riêng, không có thanh địa chỉ).

Cách chạy:
    Nhấp đúp vào file BreathSafe.bat
    (hoặc gõ:  python chay_desktop.py)

Nó làm 3 việc:
    1. Khởi động Streamlit chạy ngầm trên máy (localhost).
    2. Mở Chrome hoặc Edge ở chế độ "app" — trỏ vào Streamlit, ẩn thanh địa
       chỉ và các nút của trình duyệt, nên nhìn như một phần mềm desktop thật.
    3. Khi đóng cửa sổ, tự động tắt Streamlit.

Vì sao cách này giải quyết được chuyện micro?
---------------------------------------------
App ghi âm bằng thư viện Python (sounddevice) — thu THẲNG từ micro của máy, xem
file am_thanh.py. Trình duyệt ở đây chỉ đóng vai "khung cửa sổ" để hiển thị, nó
KHÔNG cần xin quyền micro, nên không bị Chrome chặn.

Toàn ngoại tuyến: mọi thứ chạy trên localhost, không gửi gì ra Internet.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

CONG = 8520  # cổng localhost cho Streamlit (chọn số ít đụng với app khác)
DIA_CHI = f"http://localhost:{CONG}"
THU_MUC = Path(__file__).resolve().parent

# Các nơi Chrome/Edge thường được cài trên Windows.
NOI_CAI_TRINH_DUYET = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def cong_dang_mo(cong: int) -> bool:
    """Cổng đã có ai đó (Streamlit) lắng nghe chưa?"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", cong)) == 0


def tim_trinh_duyet():
    """Trả về đường dẫn Chrome/Edge đầu tiên tìm thấy, hoặc None."""
    for duong_dan in NOI_CAI_TRINH_DUYET:
        if os.path.exists(duong_dan):
            return duong_dan
    return None


def khoi_dong_streamlit():
    """Chạy Streamlit ngầm. Trả về tiến trình để sau này tắt đi.

    `--server.address 127.0.0.1` là BẮT BUỘC, không phải tuỳ chọn cho gọn.
    Mặc định Streamlit lắng nghe trên MỌI card mạng (0.0.0.0), nên nó in ra cả
    "Network URL" và "External URL" — tức là bất cứ ai trong cùng mạng LAN (và
    nếu router có mở cổng thì cả ngoài Internet) đều mở được app, nhập ca bệnh,
    và đọc trang Lịch sử ca của phiên đang chạy.
    """
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.port",
            str(CONG),
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(THU_MUC),
    )


def cho_streamlit_san_sang(giay_toi_da: int = 40) -> bool:
    """Đợi tới khi Streamlit mở cổng, tối đa `giay_toi_da` giây."""
    for _ in range(giay_toi_da * 2):
        if cong_dang_mo(CONG):
            return True
        time.sleep(0.5)
    return False


def main():
    server = None

    # Nếu cổng đã mở sẵn (đã chạy từ trước) thì không khởi động lần nữa.
    if not cong_dang_mo(CONG):
        print("Đang khởi động BreathSafe…")
        server = khoi_dong_streamlit()
        if not cho_streamlit_san_sang():
            print("Streamlit khởi động quá lâu. Hãy thử chạy tay: streamlit run app.py")
            if server:
                server.terminate()
            return

    trinh_duyet = tim_trinh_duyet()

    try:
        if trinh_duyet:
            # user-data-dir riêng → cửa sổ này là một phiên bản độc lập, nên
            # lệnh .wait() bên dưới đứng chờ tới khi người dùng đóng cửa sổ
            # (nếu dùng chung hồ sơ mặc định, Chrome sẽ mở tab rồi thoát ngay).
            ho_so = THU_MUC / ".trinh_duyet_data"
            cua_so = subprocess.Popen(
                [
                    trinh_duyet,
                    f"--app={DIA_CHI}",
                    f"--user-data-dir={ho_so}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-size=1280,860",
                ]
            )
            print("BreathSafe đang mở. Đóng cửa sổ app để thoát.")
            cua_so.wait()  # đứng chờ tới khi đóng cửa sổ
        else:
            # Không có Chrome/Edge — mở bằng trình duyệt mặc định và chờ Enter.
            import webbrowser

            print("Không tìm thấy Chrome/Edge. Mở bằng trình duyệt mặc định.")
            webbrowser.open(DIA_CHI)
            input("Nhấn Enter ở đây để tắt BreathSafe…")
    finally:
        if server is not None:
            print("Đang tắt BreathSafe…")
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    main()
