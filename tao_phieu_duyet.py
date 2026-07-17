"""Sinh phiếu duyệt để bác sĩ đọc và ký.

Chạy:  python tao_phieu_duyet.py

Sinh ra 2 file trong thư mục ho_so/:
    phieu_duyet_bo_quy_tac.md  — bộ quy tắc cảnh báo đỏ + ngưỡng
    phieu_duyet_20_ca.md       — 20 ca lâm sàng kinh điển

Vì sao phải sinh bằng script mà không gõ tay?
---------------------------------------------
Vì bác sĩ ký vào cái gì thì cái đó phải ĐÚNG là cái hệ thống đang chạy. Nếu gõ
tay, chỉ cần sau này sửa một ngưỡng trong quy_tac.py mà quên sửa phiếu, thì chữ
ký của bác sĩ đang xác nhận cho một phiên bản không còn tồn tại. Sinh tự động
thì phiếu và code không bao giờ lệch nhau.

Sau khi in và xin chữ ký:
    1. Scan bản đã ký, lưu vào ho_so/
    2. Mở ca_kinh_dien.py, điền TEN_BAC_SI_DUYET và NGAY_DUYET (tên thật)
    3. Đổi BS_DA_KY = True
"""

from pathlib import Path

from ca_kinh_dien import CA_KINH_DIEN
from dac_trung import TEN_TIENG_VIET
from tieng_viet import bat_tieng_viet

THU_MUC = Path("ho_so")

O_TRONG = "\n\n_Bác sĩ sửa lại nếu chưa hợp lý:_ ................................................\n"


def phieu_bo_quy_tac():
    """Phiếu duyệt bộ quy tắc cảnh báo đỏ."""
    return f"""# PHIẾU DUYỆT CHUYÊN MÔN — BỘ QUY TẮC CẢNH BÁO ĐỎ

**Đề tài:** BreathSafe — Trợ lý AI hỗ trợ nhân viên y tế tuyến xã sàng lọc sớm
nguy cơ bệnh hô hấp

**Người thực hiện:** ......................................  **Lớp:** ..............

**Trường:** ................................................................

---

## Kính gửi bác sĩ

Cháu là học sinh THCS đang làm một đề tài khoa học kỹ thuật. Hệ thống của cháu
phân loại nguy cơ bệnh hô hấp thành 3 mức (Thấp / Trung bình / Cao) để hỗ trợ
nhân viên y tế tuyến xã quyết định có cần chuyển tuyến hay không.

**Hệ thống này KHÔNG chẩn đoán bệnh, KHÔNG kê đơn, và KHÔNG dùng trên bệnh nhân
thật.** Đây là bài tập nghiên cứu.

Trong hệ thống có một bộ quy tắc do cháu tự viết dựa trên tài liệu y khoa phổ
thông. **Cháu không có chuyên môn y khoa để tự khẳng định các ngưỡng này đúng.**
Cháu kính mong bác sĩ dành khoảng 20 phút đọc và cho ý kiến.

Bác sĩ **không cần đồng ý** với mọi mục. Chỗ nào bác sĩ thấy sai, xin gạch bỏ và
ghi lại — ý kiến phản đối cũng có giá trị khoa học như ý kiến đồng ý, và cháu sẽ
ghi đúng vào báo cáo.

---

## PHẦN 1 — Các quy tắc cảnh báo đỏ

Nếu một ca trúng **bất kỳ** quy tắc nào dưới đây, hệ thống kết luận **nguy cơ CAO
ngay lập tức**, không cần hỏi ý kiến mô hình AI.

| # | Quy tắc | Lý do cháu đưa vào | Bác sĩ đồng ý? |
|:-:|---|---|:-:|
| 1 | SpO2 < 92% **và** có khó thở | Dấu hiệu suy hô hấp | ☐ Đồng ý ☐ Không |
| 2 | SpO2 < 90% (kể cả không khó thở) | "Silent hypoxia" — có bệnh nhân thiếu oxy nặng mà vẫn tỉnh táo | ☐ Đồng ý ☐ Không |
| 3 | Đau ngực **và** khó thở **và** mới bệnh ≤ 1 ngày | Nghi thuyên tắc phổi / tràn khí màng phổi | ☐ Đồng ý ☐ Không |
| 4 | Tuổi < 5 **và** có khó thở | Trẻ nhỏ suy hô hấp rất nhanh | ☐ Đồng ý ☐ Không |
| 5 | Tuổi > 65 **và** có sốt **và** nhịp thở > 24 | Người già viêm phổi có thể không sốt cao rõ | ☐ Đồng ý ☐ Không |
| 6 | Nhiệt độ > 39°C **và** bệnh > 3 ngày **và** mệt nhiều | Sốt cao kéo dài | ☐ Đồng ý ☐ Không |
| 7 | Nhịp thở > 30 **và** tuổi ≥ 12 | Suy hô hấp ở người lớn | ☐ Đồng ý ☐ Không |

**Bác sĩ có thấy thiếu quy tắc nào quan trọng không?**

.....................................................................................

.....................................................................................

.....................................................................................

---

## PHẦN 2 — Các dấu hiệu "đáng chú ý" (chưa đủ báo động đỏ)

Nếu AI đánh giá mức Thấp nhưng ca có **từ 2 dấu hiệu trở lên** trong bảng này,
hệ thống tự nâng lên mức **Trung bình** cho an toàn.

| # | Dấu hiệu | Bác sĩ đồng ý? |
|:-:|---|:-:|
| 1 | SpO2 trong khoảng 92–94% | ☐ Đồng ý ☐ Không |
| 2 | Nhịp thở > 22 lần/phút | ☐ Đồng ý ☐ Không |
| 3 | Nhiệt độ > 38.5°C | ☐ Đồng ý ☐ Không |
| 4 | Có bệnh nền | ☐ Đồng ý ☐ Không |
| 5 | Bệnh đã > 5 ngày chưa đỡ | ☐ Đồng ý ☐ Không |
| 6 | Tuổi > 65 | ☐ Đồng ý ☐ Không |
| 7 | Vừa mệt nhiều vừa khó thở | ☐ Đồng ý ☐ Không |

**Ngưỡng "từ 2 dấu hiệu trở lên" có hợp lý không, hay nên là 3?**

.....................................................................................

---

## PHẦN 3 — Bảng nhịp thở bình thường theo tuổi

Hệ thống dùng bảng này để biết một người thở nhanh hay không (trẻ nhỏ thở nhanh
hơn người lớn là bình thường).

| Tuổi | Nhịp thở bình thường (lần/phút) | Bác sĩ đồng ý? |
|---|:-:|:-:|
| Dưới 1 tuổi | 40 | ☐ Đồng ý ☐ Sửa: ......... |
| 1 – 2 tuổi | 30 | ☐ Đồng ý ☐ Sửa: ......... |
| 3 – 5 tuổi | 25 | ☐ Đồng ý ☐ Sửa: ......... |
| 6 – 11 tuổi | 20 | ☐ Đồng ý ☐ Sửa: ......... |
| Từ 12 tuổi | 16 | ☐ Đồng ý ☐ Sửa: ......... |

---

## PHẦN 4 — Ý kiến chung

**1. Bài toán này có thật ở tuyến y tế cơ sở không?** (trạm y tế xã có thiếu công
cụ hỗ trợ quyết định chuyển tuyến không?)

.....................................................................................

.....................................................................................

**2. Nếu có một công cụ như thế này, bác sĩ có lo ngại gì?**

.....................................................................................

.....................................................................................

**3. Bác sĩ thấy nguy hiểm lớn nhất của một hệ thống như thế này là gì?**

.....................................................................................

.....................................................................................

---

## XÁC NHẬN

Tôi đã đọc bộ quy tắc trên. Ý kiến của tôi được ghi trong phiếu này.

☐ Tôi **đồng ý** rằng bộ quy tắc (sau khi sửa theo ghi chú của tôi, nếu có) là
hợp lý ở mức một công cụ sàng lọc hỗ trợ, phục vụ mục đích học tập.

☐ Tôi **không đồng ý** — lý do: ....................................................

**Lưu ý:** Chữ ký này xác nhận tôi đã xem xét bộ quy tắc về mặt chuyên môn. Nó
KHÔNG phải là phê duyệt để sử dụng trên bệnh nhân thật, và tôi không chịu trách
nhiệm pháp lý về việc sử dụng phần mềm này.

Họ tên: ..............................................................

Chức danh / Nơi công tác: ............................................

Số chứng chỉ hành nghề (nếu có): ....................................

Ngày: ........./........./..............

Chữ ký: ..............................................................
"""


def phieu_20_ca():
    """Phiếu duyệt 20 ca lâm sàng — sinh trực tiếp từ CA_KINH_DIEN."""
    dong = [
        "# PHIẾU DUYỆT CHUYÊN MÔN — BỘ 20 CA LÂM SÀNG KINH ĐIỂN",
        "",
        "**Đề tài:** BreathSafe — Trợ lý AI sàng lọc sớm nguy cơ bệnh hô hấp",
        "",
        "**Người thực hiện:** ......................................  **Lớp:** ..............",
        "",
        "---",
        "",
        "## Kính gửi bác sĩ",
        "",
        "Cháu dùng 20 ca dưới đây để kiểm tra xem hệ thống của cháu có xử lý đúng các",
        "tình huống lâm sàng quan trọng không. Mỗi ca là một tình huống mà người không",
        "có chuyên môn dễ đánh giá sai.",
        "",
        "**Các ca này do cháu tự soạn từ tài liệu y khoa phổ thông.** Cột *Đáp án cháu",
        "đề xuất* là ý kiến của cháu, **chưa có giá trị chuyên môn**. Cháu kính mong bác",
        "sĩ xác nhận hoặc sửa lại.",
        "",
        "Nếu bác sĩ thấy các con số trong một ca không hợp lý (ví dụ SpO2 và nhịp thở",
        "không khớp nhau), xin gạch và sửa — cháu sẽ cập nhật vào hệ thống.",
        "",
        "Thời gian ước tính: khoảng 30 phút.",
        "",
        "---",
        "",
    ]

    for i, ca in enumerate(CA_KINH_DIEN, 1):
        dong.append(f"### {ca['id']} — {ca['name']}")
        dong.append("")
        dong.append(f"**Mô tả:** {ca['description']}")
        dong.append("")
        dong.append("**Số liệu đưa vào hệ thống:**")
        dong.append("")
        dong.append("| Thông tin | Giá trị |")
        dong.append("|---|:-:|")
        for ten, gia_tri in ca["input"].items():
            nhan = TEN_TIENG_VIET.get(ten, ten)
            if ten in ("fever", "cough", "dyspnea", "chest_pain", "fatigue", "comorbidity"):
                hien = "Có" if gia_tri == 1 else "Không"
            else:
                hien = gia_tri
            dong.append(f"| {nhan} | {hien} |")
        dong.append("")
        dong.append(f"**Đáp án cháu đề xuất:** `{ca['expected_label']}`")
        dong.append("")
        dong.append(f"**Bài học y khoa cháu muốn kiểm tra:** {ca['lesson']}")
        dong.append("")
        dong.append("**Ý kiến bác sĩ:**")
        dong.append("")
        dong.append("☐ Đồng ý với đáp án `" + ca["expected_label"] + "`")
        dong.append("")
        dong.append("☐ Không đồng ý — đáp án đúng là: ☐ Thấp  ☐ Trung bình  ☐ Cao")
        dong.append("")
        dong.append("☐ Số liệu của ca này chưa hợp lý — xin sửa: ..............................")
        dong.append("")
        dong.append("Ghi chú: ................................................................")
        dong.append("")
        dong.append("---")
        dong.append("")

    dong += [
        "## Ý kiến chung về cả bộ 20 ca",
        "",
        "**1. Bộ ca này có thiếu tình huống quan trọng nào không?**",
        "",
        ".....................................................................................",
        "",
        ".....................................................................................",
        "",
        "**2. Có ca nào bác sĩ thấy không nên đưa vào không? Vì sao?**",
        "",
        ".....................................................................................",
        "",
        "---",
        "",
        "## XÁC NHẬN",
        "",
        "Tôi đã đọc và cho ý kiến về từng ca trong bộ 20 ca trên. Các đáp án tôi đánh",
        "dấu đồng ý (hoặc sửa lại) phản ánh đánh giá chuyên môn của tôi.",
        "",
        "**Lưu ý:** Chữ ký này xác nhận tôi đã xem xét bộ ca về mặt chuyên môn cho mục",
        "đích học tập. Nó KHÔNG phải phê duyệt sử dụng trên bệnh nhân thật, và tôi không",
        "chịu trách nhiệm pháp lý về việc sử dụng phần mềm này.",
        "",
        "Họ tên: ..............................................................",
        "",
        "Chức danh / Nơi công tác: ............................................",
        "",
        "Số chứng chỉ hành nghề (nếu có): ....................................",
        "",
        "Ngày: ........./........./..............",
        "",
        "Chữ ký: ..............................................................",
        "",
    ]
    return "\n".join(dong)


def main():
    bat_tieng_viet()
    THU_MUC.mkdir(exist_ok=True)

    cac_phieu = {
        "phieu_duyet_bo_quy_tac.md": phieu_bo_quy_tac(),
        "phieu_duyet_20_ca.md": phieu_20_ca(),
    }

    for ten, noi_dung in cac_phieu.items():
        duong_dan = THU_MUC / ten
        duong_dan.write_text(noi_dung, encoding="utf-8")
        so_dong = len(noi_dung.splitlines())
        print(f"Đã tạo: {duong_dan}  ({so_dong} dòng)")

    print(f"\nBộ 20 ca trong phiếu: {len(CA_KINH_DIEN)} ca")
    print(
        "\nBước tiếp theo:\n"
        "  1. Mở file .md bằng VS Code / Typora, xuất ra PDF rồi in.\n"
        "     (Hoặc dán vào Word nếu quen hơn.)\n"
        "  2. In 2 bản: 1 cho bác sĩ giữ, 1 để xin chữ ký mang về.\n"
        "  3. Mang theo bút, và một tờ giấy trắng để bác sĩ ghi thêm nếu cần.\n"
        "  4. Sau khi ký: scan/chụp, lưu vào ho_so/, rồi cập nhật ca_kinh_dien.py."
    )


if __name__ == "__main__":
    main()
