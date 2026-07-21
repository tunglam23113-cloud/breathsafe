"""Giao diện BreathSafe.

Chạy:  streamlit run app.py

Thiết kế hướng đến người dùng thật ở trạm y tế xã:
  - Chữ to (font >= 18pt) cho người lớn tuổi
  - Màu tương phản cao: đỏ / vàng / xanh
  - Chạy hoàn toàn ngoại tuyến, không cần Internet
  - Mỗi kết quả đều có lý do, không bao giờ chỉ hiện một con số
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from health_core import PhysicianFeedbackLoop

import am_thanh
from ca_kinh_dien import BS_DA_KY, CA_KINH_DIEN, TEN_BAC_SI_DUYET
from dac_trung import DAC_TRUNG, MUC_NGUY_CO
from he_thong import HeThongBreathSafe

FILE_MO_HINH = "mo_hinh_breathsafe.joblib"
FILE_PHAN_HOI = "phan_hoi_bac_si.json"

st.set_page_config(
    page_title="BreathSafe — Sàng lọc nguy cơ hô hấp",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# BẢNG MÀU
# ---------------------------------------------------------------------------
# Đỏ / vàng / xanh lá được GIỮ RIÊNG cho 3 mức nguy cơ. Không dùng chúng cho
# nút bấm hay trang trí, nếu không màu cảnh báo sẽ mất tác dụng.
MAU = {
    2: {"chinh": "#DC2626", "nen": "#FEF2F2", "vien": "#FECACA", "icon": "🔴"},
    1: {"chinh": "#D97706", "nen": "#FFFBEB", "vien": "#FDE68A", "icon": "🟡"},
    0: {"chinh": "#16A34A", "nen": "#F0FDF4", "vien": "#BBF7D0", "icon": "🟢"},
}

st.markdown(
    """
    <style>
    /* --- Chữ to cho người lớn tuổi (yêu cầu >= 18px) --- */
    html, body, [class*="css"], .stMarkdown, p, li { font-size: 17px; }

    /* --- Giới hạn bề rộng: dòng chữ quá dài rất khó đọc --- */
    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* --- Tiêu đề --- */
    h1 {
        font-size: 2.1rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        color: #0F172A;
    }
    h2 { font-size: 1.4rem !important; font-weight: 650 !important; }

    /* h3 = tiêu đề từng thẻ ("Thông tin chung", "Dấu hiệu sinh tồn"...).
       Streamlit bọc chữ trong <span> con, nên phải nhắm cả span — đặt màu trên
       riêng h3 sẽ không xuống được tới chữ. */
    h3, h3 span {
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #0F766E !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    /* Ẩn cái móc xích "link to header" hiện ra khi rê chuột — thừa ở app này. */
    h3 [data-testid="stHeaderActionElements"] { display: none; }

    /* --- Nhãn của ô nhập: đậm và dễ đọc --- */
    .stSlider label, .stNumberInput label, .stRadio label,
    .stSelectbox label, .stCheckbox label, .stFileUploader label {
        font-size: 16px !important;
        font-weight: 550 !important;
        color: #1E293B !important;
    }

    /* --- Ghi chú dưới ô nhập --- */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #64748B !important;
        font-size: 14px !important;
    }

    /* --- Checkbox triệu chứng: to hơn, dễ bấm --- */
    .stCheckbox [data-testid="stMarkdownContainer"] p { font-size: 17px !important; }

    /* --- Nút chính --- */
    .stButton > button, .stFormSubmitButton > button {
        font-size: 17px !important;
        font-weight: 650 !important;
        letter-spacing: 0.03em;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        transition: transform 0.06s ease;
    }
    .stButton > button:active, .stFormSubmitButton > button:active {
        transform: translateY(1px);
    }

    /* --- Thẻ (container có viền) ---
       Streamlit 1.41 gắn viền vào chính stVerticalBlock, không phải một
       "BorderWrapper" riêng như các bản khác. Nhắm cả hai để phòng khi nâng
       cấp Streamlit thì giao diện không vỡ. */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlock"][class*="st-emotion"],
    [data-testid="stForm"] {
        border-radius: 12px !important;
    }
    [data-testid="stForm"] {
        border-color: #E2E8F0 !important;
        padding: 1.25rem !important;
        background: #FCFDFE;
    }

    /* --- THANH BÊN (dark teal, kiểu "clinical workspace") --- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10312E 0%, #0B2320 100%);
    }
    /* Chữ trong thanh bên đổi sang sáng màu để đọc được trên nền tối. */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] [role="radiogroup"] label p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #CBD5E1 !important;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem !important;
        color: #FFFFFF !important;
        letter-spacing: -0.01em;
    }
    /* Điều hướng: mỗi mục là một "viên" bấm được; mục đang chọn tô nền teal.
       :has() được Chrome/Edge hỗ trợ — app desktop chạy trong 2 trình duyệt này. */
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 3px; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        transition: background 0.12s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.06);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: #0F766E;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 650 !important;
    }

    /* --- Phụ đề nhỏ dưới tiêu đề trang --- */
    .bs-subtitle {
        color: #64748B;
        font-size: 15px;
        margin: -0.4rem 0 1.1rem 0;
    }

    /* --- Viên trạng thái (status pill) --- */
    .bs-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
        padding: 0.35rem 0.85rem;
        border-radius: 999px;
        font-size: 14px;
        font-weight: 600;
    }

    /* --- Đầu thẻ ghi âm tiếng ho --- */
    .bs-audio-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0.2rem;
    }
    .bs-audio-head .thoi-luong {
        font-variant-numeric: tabular-nums;
        font-weight: 700;
        color: #0F172A;
    }

    /* --- Banner kết quả (dựng bằng HTML riêng) --- */
    .bs-ketqua {
        border-radius: 14px;
        padding: 1.5rem 1.75rem;
        border: 2px solid;
        margin-bottom: 0.5rem;
    }
    .bs-ketqua .muc {
        font-size: 2rem;
        font-weight: 750;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }
    .bs-ketqua .phu { font-size: 15px; margin: 0.4rem 0 0 0; opacity: 0.85; }

    /* --- Thẻ chỉ số sinh tồn --- */
    .bs-chiso {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 650;
        margin-left: 0.4rem;
    }

    /* --- Nguồn kết luận (rule / ai / hậu kiểm) --- */
    .bs-nguon {
        border-left: 4px solid #0F766E;
        background: #F0FDFA;
        padding: 0.85rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 15px;
        margin-top: 0.75rem;
    }

    /* --- Bỏ khoảng trắng thừa của Streamlit --- */
    [data-testid="stVerticalBlock"] { gap: 0.7rem; }
    </style>
    """,
    unsafe_allow_html=True,
)



def the_chi_so(gia_tri, nguong_xau, nguong_vua, dao_nguoc=False):
    """Trả về (màu, nhãn) cho một chỉ số sinh tồn, để hiện ngay lúc nhập.

    Người dùng thấy ngay "SpO2 89% — Thấp" ngay khi kéo thanh trượt, không cần
    chờ bấm nút. Đây là thứ giúp nhân viên y tế tin vào công cụ: nó phản ứng
    tức thì và đồng ý với những gì họ đã biết.

    Tham số:
        dao_nguoc: True nếu GIÁ TRỊ CÀNG CAO CÀNG XẤU (nhịp thở, nhiệt độ).
                   False nếu càng THẤP càng xấu (SpO2).
    """
    if dao_nguoc:
        xau = gia_tri >= nguong_xau
        vua = gia_tri >= nguong_vua
    else:
        xau = gia_tri <= nguong_xau
        vua = gia_tri <= nguong_vua

    if xau:
        return "#DC2626", "#FEF2F2", "Bất thường"
    if vua:
        return "#D97706", "#FFFBEB", "Cần chú ý"
    return "#16A34A", "#F0FDF4", "Bình thường"


@st.cache_resource
def nap_he_thong():
    """Nạp mô hình một lần rồi giữ trong bộ nhớ (cache) cho nhanh."""
    from health_core import RiskScreeningModel

    if not Path(FILE_MO_HINH).exists():
        return None
    return HeThongBreathSafe(RiskScreeningModel.load(FILE_MO_HINH))


@st.cache_resource
def nap_mo_hinh_ho():
    """Nạp mô hình phân loại tiếng ho nếu đã huấn luyện, không thì trả về None.

    Mô hình này là MODULE RIÊNG (xem huan_luyen_tieng_ho.py). App chạy bình
    thường kể cả khi chưa có nó — phần âm thanh chỉ là thí nghiệm phụ.
    """
    import joblib

    duong_dan = Path("mo_hinh_tieng_ho.joblib")
    return joblib.load(duong_dan) if duong_dan.exists() else None


he_thong = nap_he_thong()


@st.fragment
def khoi_ghi_am_ho():
    """Khối ghi âm/tải file tiếng ho — tách thành fragment RIÊNG.

    Ghi âm chặn (blocking) vài giây; nếu để trong luồng rerun toàn trang,
    Streamlit sẽ hiện một bản "bóng ma" (stale/dimmed) của cả trang bên dưới
    trong lúc chờ, trông như khung bị nhân đôi. Tách fragment để chỉ khối
    này rerun, không kéo theo toàn bộ trang.
    """
    # key= cố định để Streamlit không tạo bản ghost/duplicate khi số phần tử
    # bên trong thay đổi giữa các lần rerun (ví dụ sau khi ghi âm xong).
    with st.container(border=True, key="the_ghi_am_ho"):
        st.markdown("### Ghi âm tiếng ho")
        st.markdown(
            '<p class="bs-subtitle">Bản desktop ghi âm thẳng từ micro của máy '
            "— không qua quyền micro của trình duyệt.</p>",
            unsafe_allow_html=True,
        )

        c_am_1, c_am_2 = st.columns([1, 1], gap="medium")
        with c_am_1:
            thoi_luong_ghi = st.slider(
                "Thời lượng ghi (giây)", 2, 10, 5, key="ho_thoi_luong_ghi"
            )
            co_micro = am_thanh.co_micro()
            if st.button(
                "🎙️  GHI TIẾNG HO",
                use_container_width=True,
                disabled=not co_micro,
                key="ho_nut_ghi_am",
            ):
                try:
                    with st.spinner(
                        f"Đang ghi {thoi_luong_ghi} giây… hãy ho vào micro"
                    ):
                        y_ho, sr_ho = am_thanh.ghi_am(thoi_luong_ghi)
                    st.session_state["ho_y"] = y_ho
                    st.session_state["ho_sr"] = sr_ho
                except Exception as loi:
                    st.error(
                        "Không ghi được từ micro. Kiểm tra quyền micro của Windows "
                        "và thiết bị Input."
                    )
                    st.caption(str(loi))
            if not co_micro:
                st.caption("Máy này chưa thấy micro — hãy dùng ô tải file bên phải.")

        with c_am_2:
            tep_ho = st.file_uploader(
                "Hoặc tải lên file tiếng ho",
                type=["wav", "mp3", "m4a", "ogg"],
                help="Chỉ dùng mẫu đã có sự đồng ý của người được ghi âm.",
                key="ho_tai_file",
            )
            if tep_ho is not None:
                try:
                    y_ho, sr_ho = am_thanh.doc_file(tep_ho.getvalue())
                    st.session_state["ho_y"] = y_ho
                    st.session_state["ho_sr"] = sr_ho
                except Exception as loi:
                    st.error("Không đọc được file âm thanh này.")
                    st.caption(str(loi))

        if "ho_y" in st.session_state:
            y_ho = st.session_state["ho_y"]
            sr_ho = st.session_state["ho_sr"]
            thoi_luong = len(y_ho) / sr_ho if sr_ho else 0.0

            st.markdown(
                f'<div class="bs-audio-head"><b>Tiếng ho đã ghi</b>'
                f'<span class="thoi-luong">{thoi_luong:0.1f}s</span></div>',
                unsafe_allow_html=True,
            )
            st.line_chart(
                am_thanh.song_am_rut_gon(y_ho), height=90, color="#0F766E"
            )
            st.audio(y_ho, sample_rate=sr_ho)

            try:
                dac_trung_ho = am_thanh.trich_dac_trung(y_ho, sr_ho)
                st.markdown(
                    f'<span class="bs-pill">● Đã trích {len(dac_trung_ho)} '
                    "đặc trưng âm thanh</span>",
                    unsafe_allow_html=True,
                )

                # Nếu đã huấn luyện mô hình tiếng ho thì hiện kết quả của nó —
                # nhưng là một Ô RIÊNG, KHÔNG cộng vào mức nguy cơ bên dưới.
                mo_hinh_ho = nap_mo_hinh_ho()
                if mo_hinh_ho is not None:
                    hang = pd.DataFrame([dac_trung_ho])  # đúng thứ tự cột FEATURE_NAMES
                    cot_1 = list(mo_hinh_ho.classes_).index(1)
                    p_bat_thuong = float(mo_hinh_ho.predict_proba(hang)[0][cot_1])
                    nhan = "Bất thường" if p_bat_thuong >= 0.5 else "Khỏe"
                    do_tin = p_bat_thuong if nhan == "Bất thường" else 1 - p_bat_thuong
                    st.markdown(
                        f'<div class="bs-nguon"><b>Phân loại tiếng ho (module riêng): '
                        f"{nhan} · {do_tin:.0%}</b><br>Đây là kết quả của một mô hình "
                        "ÂM THANH tách biệt, KHÔNG cộng vào mức nguy cơ bên dưới. "
                        "Độ chính xác thật của nó xem trong file "
                        "<code>ket_qua_tieng_ho.csv</code>.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption(
                        "(Chưa có mô hình tiếng ho. Muốn có, huấn luyện bằng lệnh: "
                        "python huan_luyen_tieng_ho.py — xem hướng dẫn trong file đó.)"
                    )
            except Exception as loi:
                st.caption(f"(Chưa xử lý được âm thanh: {loi})")

            st.caption(
                "Lưu ý trung thực: mức nguy cơ bên dưới dựa trên DẤU HIỆU LÂM SÀNG. "
                "Phân loại tiếng ho là module riêng, CHƯA đưa vào quyết định."
            )


if he_thong is None:
    st.error(
        f"### Chưa có mô hình\n\n"
        f"Không tìm thấy file `{FILE_MO_HINH}`. Hãy chạy hai lệnh này trước:\n\n"
        f"```\npython tao_du_lieu.py\npython huan_luyen.py\n```"
    )
    st.stop()


# ---------------------------------------------------------------------------
# THANH BÊN
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🫁 BreathSafe")
    st.caption("Sàng lọc nguy cơ hô hấp · trạm y tế xã")
    st.write("")

    # Giữ số thứ tự ở giá trị (để phần điều hướng phía dưới không phải sửa),
    # nhưng giấu số đi khi hiển thị cho gọn — dùng format_func.
    trang = st.radio(
        "Điều hướng",
        [
            "1. Sàng lọc",
            "2. Phản hồi bác sĩ",
            "3. Ca lâm sàng",
            "4. Về hệ thống",
            "5. Giới hạn",
        ],
        format_func=lambda s: s.split(". ", 1)[1],
        label_visibility="collapsed",
    )

    st.write("")
    # Dùng HTML tự vẽ thay cho st.warning/st.error: hai cái đó có nền sáng, đặt
    # trên thanh bên tối màu sẽ chói và khó đọc. HTML cho phép chọn màu hợp nền tối.
    st.markdown(
        '<div style="background:rgba(15,118,110,0.18);'
        "border:1px solid rgba(45,212,191,0.35);border-radius:8px;"
        'padding:0.7rem 0.8rem;color:#99F6E4;font-size:13px;line-height:1.5;">'
        "<b>Không phải thiết bị y tế.</b><br>Chỉ hỗ trợ sàng lọc. Không chẩn đoán, "
        "không kê đơn, không thay thế bác sĩ.</div>",
        unsafe_allow_html=True,
    )
    if not BS_DA_KY:
        st.markdown(
            '<div style="background:rgba(220,38,38,0.16);'
            "border:1px solid rgba(248,113,113,0.4);border-radius:8px;"
            "padding:0.7rem 0.8rem;color:#FCA5A5;font-size:13px;line-height:1.5;"
            'margin-top:0.6rem;">'
            "<b>Chưa có xác nhận chuyên môn.</b><br>Bộ quy tắc và 20 ca kinh điển "
            "chưa được bác sĩ ký duyệt. Bản nghiên cứu, chưa dùng với bệnh nhân "
            "thật.</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# TRANG 1 — SÀNG LỌC
# ---------------------------------------------------------------------------

if trang.startswith("1"):
    st.title("Sàng lọc nguy cơ bệnh hô hấp")
    st.caption(
        "Nhập thông tin bệnh nhân, hệ thống gợi ý mức nguy cơ và giải thích lý do. "
        "Kết quả chỉ để tham khảo — quyết định cuối cùng là của nhân viên y tế."
    )

    # Cho phép nạp sẵn một ca kinh điển để demo nhanh trước giám khảo.
    ten_ca_mau = st.selectbox(
        "Nạp sẵn một ca mẫu (để trống nếu muốn tự nhập)",
        ["— Tự nhập —"] + [f"{c['id']} — {c['name']}" for c in CA_KINH_DIEN],
    )
    ca_mau = None
    if ten_ca_mau != "— Tự nhập —":
        ma = ten_ca_mau.split(" — ")[0]
        ca_mau = next(c for c in CA_KINH_DIEN if c["id"] == ma)
        st.info(f"**{ca_mau['name']}**\n\n{ca_mau['description']}")

    def gia_tri(ten, mac_dinh):
        """Lấy giá trị từ ca mẫu nếu có, không thì dùng mặc định."""
        return ca_mau["input"][ten] if ca_mau else mac_dinh

    # Thẻ ghi âm tiếng ho — fragment RIÊNG (xem khoi_ghi_am_ho ở trên) để
    # rerun khi ghi âm không kéo theo toàn trang, tránh hiện khung bị nhân đôi.
    khoi_ghi_am_ho()

    with st.form("nhap_ca"):
        c1, c2, c3 = st.columns(3, gap="medium")

        with c1:
            with st.container(border=True):
                st.markdown("### Thông tin chung")
                age = st.number_input("Tuổi", 0, 120, int(gia_tri("age", 40)))
                days_sick = st.number_input(
                    "Số ngày đã bệnh", 0, 365, int(gia_tri("days_sick", 2))
                )
                comorbidity = st.radio(
                    "Có bệnh nền không?",
                    [0, 1],
                    index=int(gia_tri("comorbidity", 0)),
                    format_func=lambda x: "Có" if x else "Không",
                    horizontal=True,
                )
                st.caption("Hen, COPD, tim mạch, tiểu đường, ung thư…")

        with c2:
            with st.container(border=True):
                st.markdown("### Dấu hiệu sinh tồn")
                spo2 = st.slider(
                    "SpO2 — oxy trong máu (%)", 70, 100, int(gia_tri("spo2", 97))
                )
                st.caption("Bình thường ≥ 95%. Dưới 92% là đáng lo.")

                respiratory_rate = st.slider(
                    "Nhịp thở (lần/phút)", 8, 60, int(gia_tri("respiratory_rate", 18))
                )
                st.caption("Người lớn 12–20. Trẻ nhỏ thở nhanh hơn là bình thường.")

                temperature = st.slider(
                    "Nhiệt độ (°C)", 35.0, 42.0, float(gia_tri("temperature", 37.0)), 0.1
                )
                st.caption("Sốt khi > 37.5°C. Trên 39°C là sốt cao.")

        with c3:
            with st.container(border=True):
                st.markdown("### Triệu chứng")
                st.caption("Tích vào những dấu hiệu bệnh nhân đang có.")
                fever = st.checkbox("Sốt", bool(gia_tri("fever", 0)))
                cough = st.checkbox("Ho", bool(gia_tri("cough", 1)))
                dyspnea = st.checkbox("Khó thở", bool(gia_tri("dyspnea", 0)))
                chest_pain = st.checkbox("Đau ngực", bool(gia_tri("chest_pain", 0)))
                fatigue = st.checkbox("Mệt nhiều", bool(gia_tri("fatigue", 0)))

        st.write("")
        gui = st.form_submit_button(
            "SÀNG LỌC", type="primary", use_container_width=True
        )

    if gui:
        ca = {
            "age": age,
            "fever": int(fever),
            "temperature": temperature,
            "cough": int(cough),
            "dyspnea": int(dyspnea),
            "spo2": spo2,
            "respiratory_rate": respiratory_rate,
            "chest_pain": int(chest_pain),
            "fatigue": int(fatigue),
            "days_sick": days_sick,
            "comorbidity": int(comorbidity),
        }
        ket_qua = he_thong.danh_gia(ca)
        st.session_state["ca"] = ca
        st.session_state["ket_qua"] = ket_qua
        st.session_state["co_am_thanh_ho"] = "ho_y" in st.session_state

    if "ket_qua" in st.session_state:
        ket_qua = st.session_state["ket_qua"]
        ca = st.session_state["ca"]
        m = MAU[ket_qua.muc]

        st.write("")

        # --- Cảnh báo ca lạ đứng TRƯỚC kết quả -------------------------
        # Nếu hệ thống chưa từng gặp ca tương tự, người dùng phải biết điều đó
        # TRƯỚC khi nhìn thấy con số, nếu không họ đã tin con số đó mất rồi.
        if ket_qua.la_ca_la:
            st.error(
                f"### ⚠️ Ca lạ — không nên tin kết quả AI\n\n{ket_qua.ood.message}"
            )

        # --- Banner kết quả ---------------------------------------------
        # Tự dựng bằng HTML thay vì st.error/st.warning để kiểm soát được màu:
        # đỏ/vàng/xanh ở đây phải khớp đúng 3 mức nguy cơ.
        if ket_qua.nguon == "quy_tac":
            dong_phu = "Kết luận từ quy tắc y khoa — không dùng đến AI"
        elif ket_qua.nguon == "hau_kiem":
            dong_phu = f"Đã nâng mức cho an toàn · AI ban đầu: {ket_qua.do_tin_cay:.0%}"
        else:
            dong_phu = f"Độ tin cậy {ket_qua.do_tin_cay:.0%} (đã hiệu chuẩn)"

        st.markdown(
            f"""
            <div class="bs-ketqua" style="background:{m['nen']};border-color:{m['vien']};">
                <p class="muc" style="color:{m['chinh']};">
                    {m['icon']}&nbsp; Nguy cơ {ket_qua.ten_muc.upper()}
                </p>
                <p class="phu" style="color:{m['chinh']};">{dong_phu}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns([3, 2], gap="large")

        with c1:
            if ket_qua.nguon == "quy_tac":
                st.markdown(
                    '<div class="bs-nguon"><b>Kết luận này đến từ QUY TẮC Y KHOA, '
                    "không phải AI.</b><br>Ca có dấu hiệu nguy hiểm rõ ràng theo tài "
                    "liệu y khoa nên hệ thống cảnh báo ngay, không cần hỏi ý kiến "
                    "mô hình.</div>",
                    unsafe_allow_html=True,
                )
            elif ket_qua.nguon == "hau_kiem":
                st.markdown(
                    '<div class="bs-nguon"><b>Mức này đã được nâng lên cho an toàn.'
                    "</b><br>AI đánh giá mức Thấp, nhưng hệ thống thấy có nhiều dấu "
                    "hiệu đáng chú ý nên nâng lên Trung bình.</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("### Vì sao hệ thống kết luận như vậy")
            for x in ket_qua.ly_do:
                st.markdown(f"- {x}")

        with c2:
            st.markdown("### Chỉ số đã nhập")

            # Hiện lại các chỉ số kèm màu, để người dùng đối chiếu nhanh
            # mà không phải cuộn ngược lên form.
            for nhan, gt, don_vi, args in [
                ("SpO2", ca["spo2"], "%", (91, 94, False)),
                ("Nhịp thở", ca["respiratory_rate"], "l/p", (30, 22, True)),
                ("Nhiệt độ", ca["temperature"], "°C", (39.0, 38.5, True)),
            ]:
                chinh, nen, trang_thai = the_chi_so(gt, args[0], args[1], args[2])
                st.markdown(
                    f"""<div style="display:flex;justify-content:space-between;
                    align-items:center;padding:0.5rem 0.75rem;background:{nen};
                    border-radius:8px;margin-bottom:0.4rem;">
                    <span style="font-weight:600;">{nhan}</span>
                    <span><b style="color:{chinh};font-size:1.1rem;">{gt}{don_vi}</b>
                    <span class="bs-chiso" style="background:{chinh};color:white;">
                    {trang_thai}</span></span></div>""",
                    unsafe_allow_html=True,
                )

            if ket_qua.xac_suat:
                st.markdown("### Xác suất theo AI")
                st.bar_chart(
                    pd.DataFrame({"Xác suất": ket_qua.xac_suat}).reindex(
                        ["Thấp", "Trung bình", "Cao"]
                    ),
                    height=180,
                    color="#0F766E",
                )

        st.write("")
        k1, k2 = st.columns(2, gap="large")

        with k1:
            with st.container(border=True):
                st.markdown("### Khuyến nghị cho nhân viên y tế")
                khuyen_nghi = {
                    2: [
                        "**Cần nhân viên y tế kiểm tra NGAY**",
                        "Cân nhắc hội chẩn hoặc chuyển tuyến",
                        "Không tự ý dùng thuốc",
                    ],
                    1: [
                        "Nên được nhân viên y tế khám **trong hôm nay**",
                        "Theo dõi sát; nếu nặng lên phải đi khám ngay",
                    ],
                    0: [
                        "Theo dõi tại nhà, nghỉ ngơi, uống đủ nước",
                        "Nếu xuất hiện khó thở hoặc sốt cao kéo dài, đi khám ngay",
                    ],
                }[ket_qua.muc]
                for x in khuyen_nghi:
                    st.markdown(
                        f'<div style="border-left:3px solid {m["chinh"]};'
                        f'padding:0.35rem 0 0.35rem 0.7rem;margin-bottom:0.35rem;">'
                        f"{x}</div>",
                        unsafe_allow_html=True,
                    )

        with k2:
            with st.container(border=True):
                st.markdown("### Bản dành cho gia đình")
                st.caption("Lời dặn bằng câu đơn giản, để đọc cho người nhà nghe.")
                loi_gia_dinh = {
                    2: "Hiện tại người bệnh **có dấu hiệu nguy hiểm**. Anh/chị nên "
                       "đưa người bệnh đến bệnh viện huyện **ngay hôm nay**.",
                    1: "Người bệnh **cần được nhân viên y tế xem**. Anh/chị nên đưa "
                       "đến trạm y tế trong hôm nay để kiểm tra cho chắc.",
                    0: "Hiện tại **chưa thấy dấu hiệu nguy hiểm**. Anh/chị cho người "
                       "bệnh nghỉ ngơi, uống nhiều nước. Nếu thấy **khó thở** hoặc "
                       "**sốt cao không giảm**, hãy đưa đi khám ngay.",
                }[ket_qua.muc]
                st.markdown(
                    f'<div style="background:{m["nen"]};border-radius:10px;'
                    f'padding:1rem;font-size:18px;line-height:1.6;">'
                    f"{loi_gia_dinh}</div>",
                    unsafe_allow_html=True,
                )

        st.caption(
            "Hệ thống chỉ hỗ trợ sàng lọc, không thay thế chẩn đoán của bác sĩ."
        )


# ---------------------------------------------------------------------------
# TRANG 2 — PHẢN HỒI BÁC SĨ
# ---------------------------------------------------------------------------

elif trang.startswith("2"):
    st.title("Phản hồi của nhân viên y tế")
    st.write(
        "Đây là điểm khác biệt của BreathSafe: **AI học từ bác sĩ, không thay "
        "thế bác sĩ.** Mỗi lần anh/chị không đồng ý với hệ thống, ý kiến đó được "
        "ghi lại và dùng để cải thiện mô hình."
    )

    vong_lap = PhysicianFeedbackLoop(FILE_PHAN_HOI, feature_names=DAC_TRUNG)

    if "ket_qua" not in st.session_state:
        st.info("Hãy sàng lọc một ca ở Trang 1 trước, rồi quay lại đây để phản hồi.")
    else:
        ket_qua = st.session_state["ket_qua"]
        ca = st.session_state["ca"]

        st.subheader("Ca vừa sàng lọc")
        st.write(f"Hệ thống kết luận: **{ket_qua.ten_muc}**")
        st.json({k: ca[k] for k in DAC_TRUNG}, expanded=False)

        with st.form("phan_hoi"):
            hanh_dong = st.radio(
                "Ý kiến của anh/chị về kết quả này:",
                ["agree", "need_more_info", "disagree"],
                format_func=lambda x: {
                    "agree": "✅ Đồng ý với hệ thống",
                    "need_more_info": "❓ Đồng ý nhưng cần thêm thông tin/xét nghiệm",
                    "disagree": "❌ KHÔNG đồng ý — tôi đánh giá khác",
                }[x],
            )
            nhan_bs = st.selectbox(
                "Nếu không đồng ý, mức đúng theo anh/chị là:",
                ["Thấp", "Trung bình", "Cao"],
                index=ket_qua.muc,
            )
            ly_do = st.text_area(
                "Lý do chuyên môn (bắt buộc khi không đồng ý)",
                placeholder="Ví dụ: Bệnh nhân có tiền sử hen chưa khai báo, "
                            "năm ngoái đã từng lên cơn nặng phải nhập viện.",
            )
            ma_bs = st.text_input(
                "Mã người phản hồi (ẩn danh, ví dụ BS01)",
                placeholder="BS01",
                help="KHÔNG ghi tên thật — đề tài không thu thập thông tin định danh.",
            )
            luu = st.form_submit_button("Gửi phản hồi", type="primary")

        if luu:
            try:
                vong_lap.record(
                    case_input={k: ca[k] for k in DAC_TRUNG},
                    ai_prediction=ket_qua.ten_muc,
                    ai_confidence=ket_qua.do_tin_cay,
                    action=hanh_dong,
                    physician_label=nhan_bs if hanh_dong == "disagree" else None,
                    physician_reason=ly_do,
                    physician_id=ma_bs,
                )
                st.success("Đã ghi nhận phản hồi. Cảm ơn anh/chị.")
            except ValueError as loi:
                st.error(f"Chưa gửi được: {loi}")

    st.divider()
    st.subheader("Tổng hợp phản hồi đã thu được")
    thong_ke = vong_lap.stats()

    if thong_ke["n_total"] == 0:
        st.info("Chưa có phản hồi nào.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng phản hồi", thong_ke["n_total"])
        c2.metric("Không đồng ý", thong_ke["n_disagree"])
        c3.metric("AI bỏ sót", thong_ke["n_undercall"], help="AI đánh giá nhẹ hơn bác sĩ — loại sai nguy hiểm")
        c4.metric("AI báo động thừa", thong_ke["n_overcall"], help="AI đánh giá nặng hơn bác sĩ — an toàn hơn")

        st.text(vong_lap.report())

        if vong_lap.should_retrain(every=30):
            st.warning(
                "Đã đủ 30 ca phản hồi — nên retrain mô hình. "
                "Chạy: `python retrain.py`"
            )


# ---------------------------------------------------------------------------
# TRANG 3 — CA KINH ĐIỂN
# ---------------------------------------------------------------------------

elif trang.startswith("3"):
    st.title("Bộ 20 ca lâm sàng kinh điển")
    st.write(
        "Mỗi ca ở đây là một **bài học y khoa** — một tình huống mà người mới "
        "thường đánh giá sai. Bộ này kiểm tra hệ thống có hiểu y khoa không, "
        "chứ không chỉ đo độ chính xác trung bình trên dữ liệu mô phỏng."
    )

    if not BS_DA_KY:
        st.error(
            "**Bộ ca này CHƯA có chữ ký bác sĩ.** Các nhãn dưới đây do học sinh "
            "soạn từ tài liệu y khoa phổ thông và chưa có giá trị chuyên môn. "
            "Cần bác sĩ tư vấn duyệt và ký trước khi đưa vào báo cáo."
        )
    else:
        st.success(f"Bộ ca đã được duyệt bởi: {TEN_BAC_SI_DUYET}")

    duong_dan = Path("ket_qua_ca_kinh_dien.csv")
    if duong_dan.exists():
        df = pd.read_csv(duong_dan)
        n_khop = int(df["match"].sum())
        n_bo_sot = int((df["error_type"] == "under_alert").sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Khớp với bác sĩ", f"{n_khop}/{len(df)}")
        c2.metric("Tỉ lệ", f"{100 * n_khop / len(df):.0f}%")
        c3.metric("Bỏ sót (nguy hiểm)", n_bo_sot)

        st.dataframe(
            df[["id", "name", "ai_prediction", "expected", "match", "error_type"]],
            use_container_width=True,
            hide_index=True,
        )

        if n_bo_sot:
            st.error("### Các ca hệ thống BỎ SÓT — phải phân tích trung thực trong báo cáo")
            for _, r in df[df["error_type"] == "under_alert"].iterrows():
                with st.expander(f"{r['id']} — {r['name']}"):
                    st.write(f"**Hệ thống nói:** {r['ai_prediction']}")
                    st.write(f"**Bác sĩ nói:** {r['expected']}")
                    st.write(f"**Bài học:** {r['lesson']}")
    else:
        st.info("Chưa có kết quả. Chạy `python huan_luyen.py` để sinh ra.")

    st.divider()
    st.subheader("Chi tiết 20 ca")
    for c in CA_KINH_DIEN:
        with st.expander(f"{c['id']} — {c['name']}  (đáp án: {c['expected_label']})"):
            st.write(f"**Mô tả:** {c['description']}")
            st.write(f"**Bài học y khoa:** {c['lesson']}")
            st.json(c["input"], expanded=False)


# ---------------------------------------------------------------------------
# TRANG 4 — VỀ HỆ THỐNG
# ---------------------------------------------------------------------------

elif trang.startswith("4"):
    st.title("Hệ thống hoạt động thế nào")

    st.subheader("Ba lớp an toàn")
    st.code(
        """
Người bệnh đến trạm y tế
        ↓
[LỚP 1] Quy tắc cảnh báo đỏ  ──trúng quy tắc──→  CAO ngay (không hỏi AI)
        ↓ (không trúng)
[LỚP 0] Kiểm tra ca lạ (OOD) ──ca quá lạ────→  Từ chối dự đoán,
        ↓                                        khuyến cáo chuyển tuyến
[LỚP 2] AI phân loại 3 mức (Random Forest đã hiệu chuẩn)
        ↓
[LỚP 3] Hậu kiểm ──AI nói Thấp mà có ≥2 dấu hiệu đáng ngờ──→ nâng lên Trung bình
        ↓
Kết quả + lý do (2 cấp độ: nhân viên y tế / gia đình)
        """,
        language=None,
    )

    st.info(
        "**Nguyên tắc cốt lõi:** AI không bao giờ được một mình kết luận rằng "
        "một ca là AN TOÀN. Luôn có quy tắc chặn lại."
    )

    st.subheader("Bốn cơ chế an toàn")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "**1. Hiệu chuẩn xác suất (Calibration)**\n\n"
            "Khi hệ thống nói '80%', thì trong 100 ca tương tự phải có khoảng 80 "
            "ca thật sự nguy cơ cao. Nếu không, con số đó chỉ là trang trí.\n\n"
            "*Em không chỉ tối ưu Recall — em đảm bảo xác suất em đưa ra là xác "
            "suất thật.*"
        )
        st.markdown(
            "**3. Bộ 20 ca lâm sàng kinh điển**\n\n"
            "Các ca này KHÔNG sinh ra từ quy tắc của em, nên chúng kiểm tra hệ "
            "thống thật sự.\n\n"
            "*Em không chỉ test trên dữ liệu mô phỏng.*"
        )
    with c2:
        st.markdown(
            "**2. Phát hiện ca lạ (OOD Detection)**\n\n"
            "Gặp ca khác xa dữ liệu từng học, hệ thống từ chối dự đoán thay vì "
            "đoán bừa một cách tự tin.\n\n"
            "*AI của em biết khi nào nó không nên tin chính nó.*"
        )
        st.markdown(
            "**4. Học từ phản hồi bác sĩ**\n\n"
            "Bác sĩ có thể không đồng ý và ghi lý do. Ý kiến đó được đưa vào "
            "huấn luyện lại với trọng số cao hơn.\n\n"
            "*Em không xây AI thay bác sĩ — em xây AI học từ bác sĩ.*"
        )

    st.subheader("Ai đã làm phần nào")
    st.write(
        "Bốn cơ chế ở trên được cài đặt trong thư viện **health-core** — thư viện "
        "này **do phụ huynh của em viết** và đăng công khai lên PyPI, em không tự "
        "viết. Em dùng nó giống như dùng scikit-learn hay pandas: em hiểu nó làm "
        "gì và vì sao đề tài cần nó, nhưng không tự lập trình lại thuật toán bên trong."
    )
    st.write(
        "**Phần em tự làm và chịu trách nhiệm hoàn toàn:** bộ quy tắc cảnh báo đỏ, "
        "kiến trúc 3 lớp an toàn, bộ 20 ca lâm sàng kinh điển, cách sinh dữ liệu, "
        "giao diện này, và việc ghép tất cả lại với nhau."
    )
    st.caption(
        "Bảng 'ai làm gì' đầy đủ nằm trong phụ lục báo cáo."
    )

    st.subheader("Sai số bất đối xứng")
    st.write(
        "Trong y khoa, bỏ sót một ca nặng nguy hiểm hơn nhiều so với một báo động "
        "giả. Vì vậy hệ thống phạt hai loại sai lầm khác nhau:"
    )
    st.table(
        pd.DataFrame(
            {
                "Mức nguy cơ": ["Thấp", "Trung bình", "Cao"],
                "Mức phạt nếu bỏ sót": [1, 3, 10],
                "Ý nghĩa": [
                    "Bỏ sót ca nhẹ — hậu quả thấp",
                    "Bỏ sót ca vừa — cần chú ý",
                    "Bỏ sót ca nặng — có thể chết người",
                ],
            }
        )
    )

    duong_dan = Path("ket_qua_so_sanh.csv")
    if duong_dan.exists():
        st.subheader("So sánh các mô hình")
        st.dataframe(pd.read_csv(duong_dan), use_container_width=True, hide_index=True)
        st.caption(
            "Đọc cột **Recall (Cao)** trước tiên. Accuracy chỉ để tham khảo — một "
            "mô hình luôn nói 'Thấp' vẫn đạt Accuracy ~50% mà bỏ sót 100% ca nguy hiểm."
        )

    if Path("reliability_diagram.png").exists():
        st.subheader("Biểu đồ độ tin cậy (Reliability diagram)")
        st.image("reliability_diagram.png")
        st.caption(
            "Đường mô hình càng sát đường chéo đứt nét thì xác suất càng đáng tin."
        )


# ---------------------------------------------------------------------------
# TRANG 5 — GIỚI HẠN VÀ ĐẠO ĐỨC
# ---------------------------------------------------------------------------

else:
    st.title("Giới hạn và đạo đức")
    st.write(
        "Trang này liệt kê những gì hệ thống **không làm được**. Nêu ra trước là "
        "một lựa chọn có chủ ý — một nghiên cứu trung thực phải nói rõ giới hạn "
        "của chính nó."
    )

    st.error(
        "### Đề tài KHÔNG làm những việc sau\n"
        "- ❌ Chẩn đoán bệnh (đó là việc của bác sĩ)\n"
        "- ❌ Kê đơn thuốc\n"
        "- ❌ Đề xuất phác đồ điều trị\n"
        "- ❌ Dùng bệnh án thật có thông tin định danh\n"
        "- ❌ Triển khai trên bệnh nhân thật khi chưa qua kiểm định y khoa\n"
        "- ❌ Thay thế thiết bị y tế chuyên dụng"
    )

    st.subheader("Giới hạn khoa học — nêu thẳng")

    with st.expander("1. Dữ liệu là MÔ PHỎNG, không phải bệnh nhân thật", expanded=True):
        st.write(
            "Đây là giới hạn lớn nhất. Em viết quy tắc để sinh nhãn, rồi mô hình "
            "học từ nhãn đó — nên kết quả cao trên tập test chỉ chứng minh mô hình "
            "**học thuộc được quy tắc của em**, KHÔNG chứng minh nó đúng về y khoa. "
            "Đó gọi là lập luận vòng tròn (circular reasoning).\n\n"
            "Vì vậy em có hai cách kiểm chứng độc lập: bộ 20 ca kinh điển do bác sĩ "
            "duyệt, và dataset công khai bên ngoài. Con số đáng tin nhất trong báo "
            "cáo là kết quả trên hai nguồn đó."
        )

    with st.expander("2. Máy đo SpO2 có thể đánh lừa hệ thống"):
        st.write(
            "Máy đo SpO2 thông thường KHÔNG phân biệt được oxy với khí CO. Người "
            "ngộ độc khí than vẫn hiện SpO2 98% dù đang thiếu oxy nặng — hệ thống "
            "gần như chắc chắn bỏ sót (xem ca TC16).\n\n"
            "Đây là bằng chứng rõ nhất cho thấy AI không thay được bác sĩ hỏi bệnh sử."
        )

    with st.expander("3. Giải thích chưa phải giải thích thật của mô hình"):
        st.write(
            "Random Forest có 200 cây, không thể nói chính xác vì sao nó chọn mức "
            "này cho ca này. Phần 'lý do' mà hệ thống hiển thị là các dấu hiệu bất "
            "thường do quy tắc của em tìm ra, cộng với mức quan trọng trung bình của "
            "mô hình — **không phải** lý do riêng cho từng ca. Muốn làm đúng phải "
            "dùng SHAP, nằm ngoài phạm vi đề tài."
        )

    with st.expander("4. Có thể có thiên lệch (bias)"):
        st.write(
            "Dữ liệu mô phỏng dựa trên tài liệu y khoa chung, không phân biệt dân "
            "tộc. Nhưng một số chỉ số sinh tồn có thể khác nhau — ví dụ người sống "
            "lâu năm ở vùng núi cao thường có SpO2 nền thấp hơn người đồng bằng. "
            "Hệ thống có thể báo động thừa với nhóm này. Em chưa kiểm chứng được "
            "điều đó vì chưa có dữ liệu thật."
        )

    with st.expander("5. Ranh giới giữa 3 mức nguy cơ là do em chọn"):
        st.write(
            "Ngưỡng chia Thấp/Trung bình/Cao được chọn để tỉ lệ 3 lớp ra 50:30:20. "
            "Trong thực tế, ranh giới giữa các mức nguy cơ là mờ chứ không sắc nét: "
            "một ca 11.9 điểm và một ca 12.0 điểm gần như giống hệt nhau nhưng bị "
            "xếp khác mức."
        )

    with st.expander("6. Đánh giá người dùng có cỡ mẫu quá nhỏ"):
        st.write(
            "Em phỏng vấn 3 nhân viên y tế. n = 3 **không đủ để kết luận thống kê**. "
            "Đây là đánh giá định tính mang tính khám phá, không phải khẳng định. "
            "Nghiên cứu tiếp theo cần n ≥ 30."
        )

    st.subheader("Đạo đức dữ liệu")
    st.info(
        "- Mọi mẫu âm thanh ho phải có **phiếu đồng ý** của người thu\n"
        "- Tình nguyện viên dưới 18 tuổi phải có chữ ký phụ huynh\n"
        "- Tuyệt đối **không** thu thập tên, địa chỉ, số CCCD\n"
        "- Dữ liệu lưu trong máy local, **không** đưa lên cloud công khai"
    )

    st.subheader("Nếu hệ thống sai, ai chịu trách nhiệm?")
    st.write(
        "Trong giai đoạn nghiên cứu này, hệ thống **không được dùng để ra quyết "
        "định thật**, nên câu hỏi chưa đặt ra. Nếu sau này triển khai thật, trách "
        "nhiệm phải thuộc về: (1) cơ sở y tế, (2) bác sĩ ra quyết định cuối cùng, "
        "(3) nhà phát triển nếu phần mềm có lỗi. Việc triển khai cần hợp đồng pháp "
        "lý, bảo hiểm trách nhiệm, và mỗi cảnh báo phải có xác nhận của nhân viên y tế."
    )

    st.divider()
    st.caption(
        "*Đề tài của em là một công cụ hỗ trợ ra quyết định (decision support "
        "tool), không phải một thiết bị y tế (medical device).*"
    )
