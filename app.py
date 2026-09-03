import streamlit as st
import pandas as pd
import numpy as np
import os
from google import genai

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG WEB & GEMINI CLIENT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Hệ Thống Báo Động Học Viên Có Nguy Cơ Bỏ Học",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Hệ Thống Dự Đoán & Can Thiệp Học Viên Bỏ Học")
st.write("Tải file dữ liệu học viên lên để hệ thống phân tích, lọc danh sách nguy cơ và dùng AI soạn email can thiệp.")

# Lấy API Key từ Streamlit Secrets hoặc biến môi trường
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

@st.cache_resource
def get_gemini_client(key):
    if not key:
        return None
    return genai.Client(api_key=key)

client = get_gemini_client(api_key)

def generate_intervention_email(student_info):
    if not client:
        return "⚠️ Chưa cấu hình GEMINI_API_KEY trong Streamlit Secrets."
    
    prompt = f"""
    Bạn là một Cố vấn Học tập (Academic Advisor) cực kỳ tận tâm, thấu hiểu và chuyên nghiệp tại một trung tâm đào tạo.
    
    Thông tin học viên cần can thiệp:
    - Họ và tên / Mã HV: {student_info.get('Ten_Hoc_Vien', 'Học viên')}
    - Xác suất bỏ học dự đoán: {student_info.get('Xac_Suat_Bo_Hoc')}%
    - Số bài tập đã hoàn thành: {student_info.get('so_bai_tap_hoan_thanh')}/10 bài
    - Điểm kiểm tra giữa kỳ: {student_info.get('diem_kt_giua_ky')}/10
    - Số giờ học trung bình/tuần: {student_info.get('gio_hoc_tuan')} giờ
    - Tình trạng học phí: {"Đã đóng đủ" if student_info.get('da_dong_hoc_phi_day_du') == 1 else "Chưa đóng đủ"}

    Nhiệm vụ:
    Hãy viết 1 bức email gửi cho học viên này.
    Yêu cầu về nội dung & văn phong:
    1. Giọng văn: Ấm áp, chân thành, động viên, tuyệt đối KHÔNG chỉ trích hay gây áp lực.
    2. Chỉ ra khéo léo điểm cần hỗ trợ (ví dụ: thiếu bài tập, điểm giữa kỳ chưa như ý, hoặc thời gian học bị giảm).
    3. Đưa ra giải pháp cụ thể: Đề xuất 1 buổi tư vấn 1-1 với Trợ giảng hoặc linh hoạt gia hạn bài tập.
    4. Độ dài: Ngắn gọn (khoảng 150 - 250 từ), có Tiêu đề Email (Subject) rõ ràng.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi tạo email từ Gemini: {e}"

# -----------------------------------------------------------------------------
# 2. KHU VỰC TẢI FILE DỮ LIỆU & CẤU HÌNH THRESHOLD
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Dữ Liệu Đầu Vào")
uploaded_file = st.sidebar.file_uploader("Tải file CSV/Excel học viên:", type=["csv", "xlsx"])

OPTIMAL_THRESHOLD_CLASS0 = 0.30

custom_threshold = st.sidebar.slider(
    "Ngưỡng xác suất cảnh báo (Threshold):",
    min_value=0.1,
    max_value=0.9,
    value=OPTIMAL_THRESHOLD_CLASS0,
    step=0.05,
    help="Hạ threshold xuống sẽ tăng khả năng bắt học viên bỏ học (Recall cao hơn)."
)

# -----------------------------------------------------------------------------
# 3. XỬ LÝ VÀ HIỂN THỊ KẾT QUẢ
# -----------------------------------------------------------------------------
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success(f"Tải thành công {len(df)} bản ghi học viên!")
        
        with st.expander("👀 Xem dữ liệu gốc"):
            st.dataframe(df.head())

        feature_cols = ['so_bai_tap_hoan_thanh', 'diem_kt_giua_ky', 'gio_hoc_tuan', 'da_dong_hoc_phi_day_du']
        
        if all(col in df.columns for col in feature_cols):
            X = df[feature_cols]
            
            # Tính xác suất bỏ học
            proba_class0 = (
                (10 - X['so_bai_tap_hoan_thanh']) * 0.05 + 
                (10 - X['diem_kt_giua_ky']) * 0.04 + 
                (15 - X['gio_hoc_tuan']) * 0.02
            ).clip(0.05, 0.95)

            df['Xac_Suat_Bo_Hoc'] = (proba_class0 * 100).round(1)
            df['Trang_Thai_Canh_Bao'] = np.where(proba_class0 >= custom_threshold, "⚠️ Có Nguy Cơ Bỏ Học", "✅ An Toàn")

            # --- METRICS THỐNG KÊ ---
            total_students = len(df)
            at_risk_count = (proba_class0 >= custom_threshold).sum()
            at_risk_rate = (at_risk_count / total_students) * 100

            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng số học viên", f"{total_students} người")
            col2.metric("Số học viên nguy cơ", f"{at_risk_count} người", delta=f"{at_risk_rate:.1f}% tổng số", delta_color="inverse")
            col3.metric("Ngưỡng can thiệp áp dụng", f"{custom_threshold * 100:.0f}%")

            st.markdown("---")

            # --- BẢNG DANH SÁCH HỌC VIÊN NGUY CƠ CAO ---
            st.subheader("📌 Danh Sách Học Viên Cần Can Thiệp Gấp")
            
            df_at_risk = df[df['Trang_Thai_Canh_Bao'] == "⚠️ Có Nguy Cơ Bỏ Học"].sort_values(
                by="Xac_Suat_Bo_Hoc", ascending=False
            )

            if len(df_at_risk) > 0:
                st.dataframe(
                    df_at_risk.style.highlight_between(
                        subset=['Xac_Suat_Bo_Hoc'], 
                        left=custom_threshold*100, 
                        right=100, 
                        color='#ffcccc'
                    )
                )

                csv_data = df_at_risk.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Tải Danh Sách Học Viên Cần Can Thiệp (.CSV)",
                    data=csv_data,
                    file_name="danh_sach_hoc_vien_nguy_co_bo_hoc.csv",
                    mime="text/csv"
                )

                # --- AI ASSISTANT (GEMINI) SOẠN EMAIL CAN THIỆP ---
                st.markdown("---")
                st.header("🤖 AI Assistant: Tự Động Soạn Email Can Thiệp Cá Nhân Hóa")

                student_list = df_at_risk.index.tolist()
                selected_idx = st.selectbox(
                    "🎯 Chọn học viên cần gửi email can thiệp:", 
                    options=student_list,
                    format_func=lambda x: f"Học viên ID {x} - Risk: {df_at_risk.loc[x, 'Xac_Suat_Bo_Hoc']}% (Bài tập: {df_at_risk.loc[x, 'so_bai_tap_hoan_thanh']}/10, Điểm: {df_at_risk.loc[x, 'diem_kt_giua_ky']})"
                )

                student_data = df_at_risk.loc[selected_idx].to_dict()
                student_data['Ten_Hoc_Vien'] = f"Học viên #{selected_idx}"

                col_info, col_ai = st.columns([1, 2])

                with col_info:
                    st.subheader("📋 Phân Tích Chỉ Số")
                    st.write(f"**Xác suất bỏ học:** `{student_data['Xac_Suat_Bo_Hoc']}%`")
                    st.write(f"**Bài tập hoàn thành:** `{student_data['so_bai_tap_hoan_thanh']}/10`")
                    st.write(f"**Điểm giữa kỳ:** `{student_data['diem_kt_giua_ky']}`")
                    st.write(f"**Giờ học/tuần:** `{student_data['gio_hoc_tuan']}h`")
                    
                    btn_generate = st.button("✨ Viết Email Bằng Gemini AI", type="primary", use_container_width=True)

                with col_ai:
                    st.subheader("✉️ Nội Dung Email Đề Xuất")
                    if btn_generate:
                        with st.spinner("Gemini đang phân tích chỉ số và soạn email..."):
                            generated_email = generate_intervention_email(student_data)
                            st.session_state['current_email'] = generated_email

                    if 'current_email' in st.session_state:
                        email_text = st.text_area(
                            "Nội dung (Có thể chỉnh sửa trực tiếp trước khi gửi):", 
                            value=st.session_state['current_email'], 
                            height=300
                        )
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.download_button(
                                label="📥 Tải file Email (.txt)",
                                data=email_text,
                                file_name=f"email_can_thiep_hv_{selected_idx}.txt",
                                mime="text/plain"
                            )
                        with c2:
                            if st.button("✅ Xác nhận đã gửi email"):
                                st.success("Đã ghi nhận trạng thái: Đã gửi email can thiệp!")

            else:
                st.balloons()
                st.success("Tuyệt vời! Không có học viên nào vượt ngưỡng nguy cơ bỏ học.")

        else:
            st.error(f"File thiếu các cột thuộc tính cần thiết: {feature_cols}")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi đọc file: {e}")

else:
    st.info("👆 Vui lòng tải file dữ liệu học viên (CSV/Excel) ở thanh bên trái để bắt đầu.")