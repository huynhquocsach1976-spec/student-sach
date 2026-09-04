import streamlit as st
import pandas as pd
import numpy as np
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# =============================================================================
# 1. CẤU HÌNH TRANG WEB & GEMINI CLIENT
# =============================================================================
st.set_page_config(
    page_title="Hệ Thống CSKH & Cảnh Báo Học Viên Tự Động",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Hệ Thống Tự Động Hóa CSKH, Báo Cáo & Can Thiệp Học Viên")
st.write("Giải pháp nâng cao hiệu suất làm việc, phân tích dữ liệu và tự động gửi email cá nhân hóa bằng AI.")

# Lấy API Key từ Streamlit Secrets hoặc biến môi trường
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

@st.cache_resource
def get_gemini_client(key):
    if not key:
        return None
    return genai.Client(api_key=key)

client = get_gemini_client(api_key)

# =============================================================================
# 2. HÀM TẠO EMAIL BẰNG GEMINI AI & HÀM GỬI GMAIL SMTP
# =============================================================================
def generate_custom_email(student_info, email_type):
    if not client:
        return "⚠️ Chưa cấu hình GEMINI_API_KEY trong Streamlit Secrets."
    
    student_id = student_info.get('Mã ID Học Viên', student_info.get('Mã ID', 'N/A'))
    student_name = student_info.get('Họ Và Tên Học Viên', 'Học viên')
    
    # Xây dựng prompt theo từng kịch bản
    if email_type == "🚨 Can thiệp nguy cơ bỏ học":
        prompt = f"""
        Bạn là Cố vấn Học tập chuyên nghiệp. Hãy viết email cá nhân hóa gửi học viên:
        - Mã ID: {student_id} | Họ tên: {student_name}
        - Xác suất bỏ học: {student_info.get('Xác Suất Bỏ Học')}%
        - Bài tập: {student_info.get('Số Bài Tập Hoàn Thành')}/10 | Điểm giữa kỳ: {student_info.get('Điểm Kiểm Tra Giữa Kỳ')}/10
        - Số ngày đi học: {student_info.get('Số Ngày Đi Học')}/30
        Yêu cầu: Giọng văn chân thành, động viên, đề xuất 1 buổi tư vấn 1-1. Độ dài khoảng 150-200 từ, có Tiêu đề Email.
        """
    elif email_type == "📢 Nhắc nhở đóng học phí":
        prompt = f"""
        Bạn là Bộ phận Kế toán / CSKH của trung tâm. Hãy viết email nhắc nhở học phí lịch sự:
        - Mã ID: {student_id} | Họ tên: {student_name}
        - Tình trạng: Chưa hoàn tất học phí khóa học.
        Yêu cầu: Giọng văn lịch sự, tinh tế, nhắc nhở hạn nộp và hướng dẫn liên hệ bộ phận hỗ trợ. Có Tiêu đề Email.
        """
    else:  # 🎓 Báo cáo kết quả học tập định kỳ
        prompt = f"""
        Bạn là Cố vấn Học tập. Hãy viết email báo cáo kết quả học tập gửi cho học viên/phụ huynh:
        - Mã ID: {student_id} | Họ tên: {student_name}
        - Điểm giữa kỳ: {student_info.get('Điểm Kiểm Tra Giữa Kỳ')}/10
        - Chuyên cần: {student_info.get('Số Ngày Đi Học')}/30 ngày
        - Số bài tập hoàn thành: {student_info.get('Số Bài Tập Hoàn Thành')}/10
        Yêu cầu: Khen ngợi điểm tốt, góp ý điểm cần cải thiện, thể hiện sự đồng hành. Có Tiêu đề Email.
        """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi tạo email từ Gemini: {e}"

def send_gmail_smtp(sender_email, app_password, recipient_email, subject, body_content):
    """Hàm kết nối SMTP Gmail để gửi email trực tiếp"""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body_content, 'plain', 'utf-8'))

        # Kết nối tới Server SMTP của Gmail (Cổng 587 SSL/TLS)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        return True, "Gửi email thành công!"
    except Exception as e:
        return False, str(e)

# =============================================================================
# 3. KHU VỰC TẢI FILE DỮ LIỆU & CẤU HÌNH THRESHOLD
# =============================================================================
st.sidebar.header("📁 Dữ Liệu Đầu Vào")
uploaded_file = st.sidebar.file_uploader("Tải file CSV/Excel học viên:", type=["csv", "xlsx"])

OPTIMAL_THRESHOLD = 0.30
custom_threshold = st.sidebar.slider(
    "Ngưỡng xác suất cảnh báo (Threshold):",
    min_value=0.1, max_value=0.9, value=OPTIMAL_THRESHOLD, step=0.05
)

EXACT_RENAME_MAP = {
    'Mã ID': 'Mã ID Học Viên', 'Ma_ID': 'Mã ID Học Viên', 'ID': 'Mã ID Học Viên', 'Mã ID Học Viên': 'Mã ID Học Viên',
    'Họ Và Tên Học Viên': 'Họ Và Tên Học Viên', 'Ten_Hoc_Vien': 'Họ Và Tên Học Viên', 'Họ và tên': 'Họ Và Tên Học Viên',
    'Số Bài Tập Hoàn Thành': 'Số Bài Tập Hoàn Thành', 'so_bai_tap_hoan_thanh': 'Số Bài Tập Hoàn Thành',
    'Điểm Kiểm Tra Giữa Kỳ': 'Điểm Kiểm Tra Giữa Kỳ', 'diem_kt_giua_ky': 'Điểm Kiểm Tra Giữa Kỳ',
    'Số Ngày Đi Học': 'Số Ngày Đi Học', 'gio_hoc_tuan': 'Số Ngày Đi Học',
    'Tình Trạng Học Phí': 'Tình Trạng Học Phí', 'da_dong_hoc_phi_day_du': 'Tình Trạng Học Phí',
    'Email': 'Email', 'email': 'Email', 'Địa chỉ Email': 'Email'
}

# =============================================================================
# 4. XỬ LÝ DỮ LIỆU VÀ HIỂN THỊ
# =============================================================================
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.success(f"Tải thành công {len(df)} bản ghi học viên!")
        
        df = df.rename(columns=lambda c: EXACT_RENAME_MAP.get(str(c).strip(), str(c).strip()))

        feature_cols = ['Số Bài Tập Hoàn Thành', 'Điểm Kiểm Tra Giữa Kỳ', 'Số Ngày Đi Học', 'Tình Trạng Học Phí']
        missing_cols = [col for col in feature_cols if col not in df.columns]

        if not missing_cols:
            X = df[feature_cols]
            so_bt = pd.to_numeric(X['Số Bài Tập Hoàn Thành'], errors='coerce').fillna(0)
            diem_kt = pd.to_numeric(X['Điểm Kiểm Tra Giữa Kỳ'], errors='coerce').fillna(0)
            ngay_di_hoc = pd.to_numeric(X['Số Ngày Đi Học'], errors='coerce').fillna(0)

            max_day = 30 if ngay_di_hoc.max() > 15 else 15
            proba_class0 = (
                (10 - so_bt) * 0.05 + 
                (10 - diem_kt) * 0.04 + 
                (max_day - ngay_di_hoc) * (0.3 / max_day)
            ).clip(0.05, 0.95)

            df['Xác Suất Bỏ Học'] = (proba_class0 * 100).round(1)
            df['Trạng Thái Cảnh Báo'] = np.where(proba_class0 >= custom_threshold, "⚠️ Có Nguy Cơ Bỏ Học", "✅ An Toàn")

            # Dashboard Thống kê
            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng số học viên", f"{len(df)} người")
            col2.metric("Số học viên nguy cơ", f"{(proba_class0 >= custom_threshold).sum()} người", delta_color="inverse")
            col3.metric("Ngưỡng can thiệp", f"{custom_threshold * 100:.0f}%")

            st.markdown("---")
            st.subheader("📌 Bảng Phân Tích & Danh Sách Học Viên")
            
            df_display = df.sort_values(by="Xác Suất Bỏ Học", ascending=False)
            st.dataframe(df_display, use_container_width=True)

            # =========================================================================
            # 5. CẤU HÌNH GỬI EMAIL TỰ ĐỘNG (GMAIL SMTP + GEMINI AI)
            # =========================================================================
            st.markdown("---")
            st.header("🤖 AI CSKH & Tự Động Gửi Email Trực Tiếp")

            # Cấu hình thông tin gửi mail
            with st.expander("⚙️ Cấu Hình Tài Khoản Gmail Gửi Đi (SMTP)", expanded=False):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    sender_email = st.text_input("Email người gửi (Gmail):", placeholder="vidu@gmail.com")
                with col_m2:
                    app_password = st.text_input("Mật khẩu ứng dụng Google (16 ký tự):", type="password", help="Tạo trong phần Bảo mật tài khoản Google -> App Passwords")

            col_select1, col_select2 = st.columns(2)
            with col_select1:
                email_scenario = st.selectbox(
                    "📋 Chọn kịch bản Email cần gửi:",
                    ["🚨 Can thiệp nguy cơ bỏ học", "🎓 Báo cáo kết quả học tập định kỳ", "📢 Nhắc nhở đóng học phí"]
                )
            
            with col_select2:
                student_list = df_display.index.tolist()
                def get_student_label(idx):
                    row = df_display.loc[idx]
                    sid = row.get('Mã ID Học Viên', f'HV{idx+1:04d}')
                    name = row.get('Họ Và Tên Học Viên', f'Học viên {idx+1}')
                    return f"[{sid}] {name} - Xác suất bỏ học: {row['Xác Suất Bỏ Học']}%"

                selected_idx = st.selectbox("🎯 Chọn học viên:", options=student_list, format_func=get_student_label)

            student_data = df_display.loc[selected_idx].to_dict()

            col_info, col_ai = st.columns([1, 2])

            with col_info:
                st.subheader("📋 Chi Tiết Học Viên")
                st.write(f"**Mã ID:** `{student_data.get('Mã ID Học Viên', 'N/A')}`")
                st.write(f"**Họ tên:** `{student_data.get('Họ Và Tên Học Viên', 'N/A')}`")
                st.write(f"**Email nhận:** `{student_data.get('Email', 'Chưa có cột Email')}`")
                st.write(f"**Xác suất bỏ học:** `{student_data['Xác Suất Bỏ Học']}%`")
                
                btn_generate = st.button("✨ Dùng AI Soạn Email", type="primary", use_container_width=True)

            with col_ai:
                st.subheader("✉️ Nội Dung Email & Gửi Trực Tiếp")
                if btn_generate:
                    with st.spinner("Gemini AI đang soạn email theo kịch bản..."):
                        st.session_state['generated_email'] = generate_custom_email(student_data, email_scenario)

                if 'generated_email' in st.session_state:
                    email_body = st.text_area("Nội dung Email (Có thể chỉnh sửa):", value=st.session_state['generated_email'], height=250)
                    
                    target_email = st.text_input("Địa chỉ Email người nhận:", value=str(student_data.get('Email', '')))
                    subject_input = st.text_input("Tiêu đề Email:", value=f"[{email_scenario.split()[-1].upper()}] Thông báo từ Trung tâm Đào tạo")

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("🚀 GỬI EMAIL NGAY (GMAIL SMTP)", type="primary", use_container_width=True):
                            if not sender_email or not app_password:
                                st.error("⚠️ Vui lòng mở mục 'Cấu Hình Tài Khoản Gmail' để nhập Email & Mật khẩu ứng dụng trước!")
                            elif not target_email or "@" not in target_email:
                                st.error("⚠️ Vui lòng nhập địa chỉ Email người nhận hợp lệ!")
                            else:
                                with st.spinner("Hệ thống đang kết nối SMTP và gửi email..."):
                                    success, msg = send_gmail_smtp(sender_email, app_password, target_email, subject_input, email_body)
                                    if success:
                                        st.balloons()
                                        st.success(f"✅ Đã gửi email thành công tới: {target_email}")
                                    else:
                                        st.error(f"❌ Gửi email thất bại: {msg}")

                    with col_btn2:
                        st.download_button(
                            label="📥 Tải file Email (.txt)",
                            data=email_body,
                            file_name=f"email_{student_data.get('Mã ID Học Viên', 'HV')}.txt",
                            use_container_width=True
                        )

        else:
            st.error(f"❌ File thiếu các cột thuộc tính bắt buộc: {missing_cols}")

    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
else:
    st.info("👆 Vui lòng tải file Excel/CSV học viên lên để khởi chạy hệ thống.")