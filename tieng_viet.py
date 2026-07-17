"""Giúp cửa sổ lệnh (Command Prompt / PowerShell) in được tiếng Việt.

Vì sao cần file này?
--------------------
Trên Windows, cửa sổ lệnh mặc định dùng bảng mã cp1252 (chỉ có tiếng Anh và vài
ký tự châu Âu). Khi Python cố in chữ "Tổng" ra màn hình, nó bị lỗi:

    UnicodeEncodeError: 'charmap' codec can't encode character '\\u1ed5'

Lỗi này KHÔNG phải do code sai — chỉ là màn hình không biết vẽ chữ tiếng Việt.
Hàm dưới đây bảo Python: "hãy in ra bằng bảng mã UTF-8" (bảng mã có đủ mọi
ngôn ngữ, kể cả tiếng Việt).

Cách dùng: gọi bat_tieng_viet() ở đầu mỗi script có in tiếng Việt.
"""

import sys


def bat_tieng_viet():
    """Chuyển màn hình sang bảng mã UTF-8 để in được tiếng Việt.

    An toàn khi gọi nhiều lần. Nếu môi trường không cho đổi (ví dụ khi output
    đang bị chuyển hướng vào file), hàm lặng lẽ bỏ qua thay vì làm chương trình
    dừng — vì không in được dấu tiếng Việt thì khó chịu, nhưng không đáng để
    làm hỏng cả chương trình.
    """
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass
