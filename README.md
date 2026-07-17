# BreathSafe — phần dự án dự thi

Trợ lý AI hỗ trợ nhân viên y tế tuyến xã sàng lọc sớm nguy cơ bệnh hô hấp.

> **Không phải thiết bị y tế.** Hệ thống chỉ hỗ trợ sàng lọc — không chẩn đoán, không kê đơn, không thay thế bác sĩ.

## Chạy thử trong 3 lệnh

```bash
pip install -r requirements.txt
python tao_du_lieu.py      # sinh 2.000 ca mô phỏng
python huan_luyen.py       # huấn luyện + đánh giá + lưu mô hình
streamlit run app.py       # mở giao diện
```

## Các file trong thư mục này

| File | Việc nó làm | Độ khó |
|---|---|:---:|
| `dac_trung.py` | Danh sách 11 thông tin mà mô hình dùng | Dễ |
| `quy_tac.py` | **Rule Engine** — bộ quy tắc cảnh báo đỏ, viết bằng `if` | Dễ |
| `ca_kinh_dien.py` | 20 ca lâm sàng kinh điển để kiểm tra hệ thống | Dễ |
| `tao_du_lieu.py` | Sinh dữ liệu mô phỏng theo thang điểm nguy cơ | Vừa |
| `he_thong.py` | **Ghép 3 lớp an toàn** lại với nhau | Vừa |
| `huan_luyen.py` | Chia dữ liệu, train 5 mô hình, so sánh, đánh giá | Vừa |
| `app.py` | Giao diện Streamlit 5 trang | Vừa |
| `retrain.py` | Huấn luyện lại từ phản hồi bác sĩ | Vừa |
| `tieng_viet.py` | Giúp cửa sổ lệnh Windows in được tiếng Việt | Dễ |

Toàn bộ **phần kỹ thuật khó** (hiệu chuẩn xác suất, phát hiện ca lạ bằng khoảng cách Mahalanobis, xử lý âm thanh MFCC, cơ chế trọng số khi retrain) nằm trong thư viện [`health-core`](../health-core) — cài bằng `pip install health-core`, dùng như `numpy` hay `pandas`.

> **Về thư viện `health-core`:** thư viện này **do phụ huynh viết và đăng lên PyPI**, không phải học sinh viết. Học sinh dùng nó như dùng `scikit-learn` hay `pandas` — gọi hàm, hiểu hàm đó làm gì và vì sao cần, nhưng không tự cài đặt lại thuật toán bên trong.
>
> Điều này **đã được ghi rõ trong bảng "ai làm gì"** ở cuối tài liệu này, và học sinh cần trả lời đúng như vậy nếu giám khảo hỏi. Việc người lớn hỗ trợ phần kỹ thuật là chuyện bình thường và được chấp nhận ở KHKT — thứ bị cấm là **giấu** sự hỗ trợ đó, không phải bản thân sự hỗ trợ.

## Ba lớp an toàn

```
Người bệnh đến trạm y tế
        ↓
[LỚP 1] Quy tắc cảnh báo đỏ ──trúng quy tắc──→ CAO ngay (không hỏi AI)
        ↓ (không trúng)
[LỚP 0] Kiểm tra ca lạ (OOD) ──ca quá lạ────→ Từ chối dự đoán,
        ↓                                       khuyến cáo chuyển tuyến
[LỚP 2] AI phân loại 3 mức (Random Forest đã hiệu chuẩn)
        ↓
[LỚP 3] Hậu kiểm ──AI nói Thấp mà có ≥2 dấu hiệu đáng ngờ──→ nâng lên Trung bình
        ↓
Kết quả + lý do (2 cấp độ: nhân viên y tế / gia đình)
```

**Nguyên tắc cốt lõi:** AI không bao giờ được một mình kết luận rằng một ca là AN TOÀN.

## Kết quả (dữ liệu mô phỏng, tập test 300 ca)

| Mô hình | Recall (Cao) | Bỏ sót (Cao) | F1 macro | ECE | Accuracy |
|---|---:|---:|---:|---:|---:|
| Chỉ Rule Engine | 0.833 | 0.167 | 0.715 | — | 0.710 |
| Logistic Regression | 0.833 | 0.167 | 0.830 | 0.022 | 0.837 |
| Decision Tree | 0.933 | 0.067 | 0.874 | 0.024 | 0.877 |
| Chỉ AI (RF + hiệu chuẩn) | 0.917 | 0.083 | **0.915** | **0.020** | **0.917** |
| **HỆ THỐNG ĐẦY ĐỦ** | **0.950** | **0.050** | 0.764 | — | 0.753 |

**Bộ 20 ca kinh điển:** chỉ AI đạt 16/20 → hệ thống đầy đủ đạt **18/20** (vượt mục tiêu 17/20). Rule Engine bắt được 2 ca nhi khoa mà AI bỏ sót.

### Hai câu giám khảo chắc chắn sẽ hỏi về bảng này

**"Vì sao hệ thống đầy đủ có Accuracy THẤP HƠN chỉ dùng AI?"**
Vì Rule Engine cố tình đẩy nhiều ca lên mức Cao. Nó đánh đổi: bắt được nhiều ca nguy hiểm hơn (Recall 0.917 → 0.950) nhưng báo động giả nhiều hơn (Accuracy 0.917 → 0.753). Đây là **lựa chọn có chủ ý**, không phải lỗi. Bỏ sót một ca viêm phổi nặng có thể khiến một người chết; một báo động giả chỉ tốn của nhân viên y tế vài phút xem lại. Đề tài tối ưu Recall, không tối ưu Accuracy.

**"Vì sao cột ECE của Rule Engine và hệ thống đầy đủ để trống?"**
Vì hai mô hình đó không đưa ra xác suất. Khi Rule Engine kết luận "SpO2 = 88% kèm khó thở là nguy hiểm", đó là một quyết định y khoa dứt khoát, không phải con số xác suất — nên không có gì để hiệu chuẩn.

## Giới hạn — nêu thẳng

1. **Dữ liệu là mô phỏng, không phải bệnh nhân thật.** Đây là giới hạn lớn nhất. Học sinh viết quy tắc sinh nhãn, rồi mô hình học từ nhãn đó — nên điểm cao trên tập test chỉ chứng minh mô hình *học thuộc được quy tắc*, KHÔNG chứng minh nó đúng về y khoa (lập luận vòng tròn). Vì vậy có hai kiểm chứng độc lập: bộ 20 ca kinh điển do bác sĩ duyệt, và dataset công khai bên ngoài.
2. **Máy đo SpO2 có thể đánh lừa hệ thống.** Người ngộ độc khí CO vẫn hiện SpO2 98% — hệ thống bỏ sót ca TC16. Bằng chứng rõ nhất cho thấy AI không thay được bác sĩ hỏi bệnh sử.
3. **Phần "lý do" chưa phải giải thích thật của mô hình.** Random Forest có 200 cây, không thể nói chính xác vì sao nó chọn mức này cho ca này. Muốn làm đúng phải dùng SHAP — ngoài phạm vi đề tài.
4. **Có thể có thiên lệch.** Người sống lâu năm ở vùng núi cao thường có SpO2 nền thấp hơn — hệ thống có thể báo động thừa với nhóm này.
5. **Ranh giới 3 mức nguy cơ do học sinh chọn** để tỉ lệ ra 50:30:20. Thực tế ranh giới là mờ, không sắc nét.
6. **n = 3 nhân viên y tế không đủ để kết luận thống kê.** Đây là đánh giá định tính khám phá.

## Trước khi đem đi thi — bắt buộc

- [ ] Bác sĩ duyệt và **ký** bộ quy tắc trong `quy_tac.py`
- [ ] Bác sĩ duyệt và **ký** bộ 20 ca trong `ca_kinh_dien.py`, rồi đổi `BS_DA_KY = True`
- [ ] Đối chứng với ít nhất 1 dataset công khai (Kaggle / Coswara)
- [ ] Thu mẫu âm thanh ho **có phiếu đồng ý**
- [ ] Phỏng vấn 3 nhân viên y tế, ghi biên bản

> Không có chữ ký bác sĩ, các nhãn "đáp án đúng" chỉ là ý kiến của học sinh. Khi giám khảo hỏi *"ai bảo đó là đáp án đúng?"*, câu trả lời phải là tờ giấy có chữ ký — không phải "em tự nghĩ" hay "em hỏi AI".

## Bảng "ai làm gì" — tính trung thực học thuật

| Thành phần | HS tự làm | Có hỗ trợ | Dùng thư viện |
|---|:---:|:---:|:---:|
| Ý tưởng đề tài | ✅ | | |
| Bộ quy tắc lâm sàng (`quy_tac.py`) | ✅ viết | ✅ BS duyệt | |
| Thang điểm sinh dữ liệu (`tao_du_lieu.py`) | ✅ | ✅ BS duyệt | |
| 20 ca kinh điển (`ca_kinh_dien.py`) | ✅ soạn | ✅ BS duyệt + ký | |
| Ghép 3 lớp an toàn (`he_thong.py`) | ✅ | ✅ GV debug | |
| Train Random Forest | | | ✅ scikit-learn |
| **Thư viện `health-core`** (calibration, OOD, âm thanh, feedback loop) | | **❌ HS không viết — phụ huynh viết và đăng lên PyPI** | ✅ sklearn, scipy, librosa |
| Hiểu và gọi đúng `health-core` vào hệ thống | ✅ | | |
| Giao diện (`app.py`) | ✅ | | ✅ Streamlit |
| Phỏng vấn nhân viên y tế | ✅ | ✅ PH dẫn đi | |
| Viết báo cáo | ✅ | ✅ GV sửa văn | |

Câu trả lời mẫu khi bị hỏi **"em có tự viết hết không?"**:

> *"Em dùng thư viện scikit-learn để train Random Forest, giống như dùng máy tính bỏ túi để giải toán — em hiểu thuật toán hoạt động ra sao, nhưng không tự lập trình lại từ đầu vì điều đó không phải mục tiêu của đề tài."*

Câu trả lời mẫu khi bị hỏi **"health-core là thư viện của ai? Em có tự viết không?"**:

> *"Thư viện đó không phải em viết ạ. Bố em viết và đăng lên PyPI — em có ghi rõ trong bảng 'ai làm gì'. Em dùng nó giống như em dùng scikit-learn: em hiểu nó làm gì và vì sao đề tài em cần nó, nhưng em không tự lập trình lại các thuật toán bên trong.*
>
> *Phần em tự làm và chịu trách nhiệm hoàn toàn là: bộ quy tắc cảnh báo đỏ, kiến trúc 3 lớp an toàn, bộ 20 ca lâm sàng kinh điển, cách sinh dữ liệu, giao diện, và việc ghép tất cả lại. Nếu thầy cô muốn hỏi em bất kỳ dòng nào trong những phần đó, em xin trả lời ạ."*

Nếu bị hỏi tiếp **"vậy em có hiểu calibration là gì không?"** — cháu phải trả lời được, và câu trả lời có sẵn ở Trang 4 của app. Dùng thư viện mà không hiểu thì mới đáng trách; dùng thư viện của người khác mà hiểu rõ mình đang dùng gì thì hoàn toàn bình thường.

### Vì sao phải khai thật

Giám khảo tra PyPI mất 30 giây: package đăng gần ngày thi, tác giả là người lớn. Nếu bảng "ai làm gì" đã ghi sẵn điều đó thì **không có gì để bới** — người lớn hỗ trợ là chuyện được phép. Nhưng nếu bảng ghi "HS tự làm" mà thực tế không phải, thì lúc đó không chỉ mất điểm phần thư viện: **mọi phần khác trong đề tài đều bị nghi ngờ**, kể cả những phần cháu thật sự tự làm.

Nói cách khác, khai thật chính là thứ bảo vệ công sức thật của cháu.
"# breathsafe" 
