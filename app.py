import streamlit as st
import pandas as pd
import numpy as np
import joblib

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG WEB & TẢI MÔ HÌNH
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Hệ Thống Báo Động Học Viên Có Nguy Cơ Bỏ Học",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Hệ Thống Dự Đoán & Can Thiệp Học Viên Bỏ Học")
st.write("Tải file dữ liệu học viên lên để hệ thống phân tích và lọc ra danh sách cần can thiệp sớm.")

# Hàm tải mô hình (dùng cache để tối ưu hiệu năng)
@st.cache_resource
def load_model():
    # Trong thực tế, bạn sẽ load file .pkl đã lưu:
    # return joblib.load("student_churn_model.pkl")
    return None

# Giả lập threshold tối ưu đã tìm được từ bước trước
OPTIMAL_THRESHOLD_CLASS0 = 0.30  # Xác suất bỏ học >= 30% là đưa vào danh sách cảnh báo

# -----------------------------------------------------------------------------
# 2. KHU VỰC TẢI FILE DỮ LIỆU
# -----------------------------------------------------------------------------
st.sidebar.header("📁 Dữ Liệu Đầu Vào")
uploaded_file = st.sidebar.file_uploader("Tải file CSV/Excel học viên:", type=["csv", "xlsx"])

# Cho phép chỉnh ngưỡng can thiệp trực tiếp từ giao diện (nếu muốn)
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
    # Đọc dữ liệu
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success(f"Tải thành công {len(df)} bản ghi học viên!")
        
        # Hiển thị dữ liệu thô
        with st.expander("👀 Xem dữ liệu gốc"):
            st.dataframe(df.head())

        # --- DỰ ĐOÁN (GIẢ LẬP HOẶC DÙNG MODEL THẬT) ---
        # Chuẩn bị danh sách đặc trưng cần thiết
        feature_cols = ['so_bai_tap_hoan_thanh', 'diem_kt_giua_ky', 'gio_hoc_tuan', 'da_dong_hoc_phi_day_du']
        
        # Kiểm tra đủ cột dữ liệu không
        if all(col in df.columns for col in feature_cols):
            X = df[feature_cols]
            
            # Nếu có model thật:
            # model_data = load_model()
            # model = model_data['model']
            # proba_class0 = model.predict_proba(X)[:, 0]
            
            # Demo giả lập tính xác suất dựa trên logic thực tế nếu chưa gắn pickle file:
            # Bài tập ít + điểm thấp + giờ học ít = Xác suất bỏ học cao
            proba_class0 = (
                (10 - X['so_bai_tap_hoan_thanh']) * 0.05 + 
                (10 - X['diem_kt_giua_ky']) * 0.04 + 
                (15 - X['gio_hoc_tuan']) * 0.02
            ).clip(0.05, 0.95)

            # Gán kết quả vào DataFrame
            df['Xac_Suat_Bo_Hoc'] = (proba_class0 * 100).round(1)
            df['Trang_Thai_Canh_Bao'] = np.where(proba_class0 >= custom_threshold, "⚠️ Có Nguy Cơ Bỏ Học", "✅ An Toàn")

            # --- THỐNG KÊ TỔNG QUAN (METRICS METRICS) ---
            total_students = len(df)
            at_risk_count = (proba_class0 >= custom_threshold).sum()
            at_risk_rate = (at_risk_count / total_students) * 100

            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng số học viên", f"{total_students} người")
            col2.metric("Số học viên nguy cơ", f"{at_risk_count} người", delta=f"{at_risk_rate:.1f}% tổng số", delta_color="inverse")
            col3.metric("Ngưỡng can thiệp áp dụng", f"{custom_threshold * 100:.0f}%")

            st.markdown("---")

            # --- BAN BẢNG DANH SÁCH HỌC VIÊN NGUY CƠ CAO ---
            st.subheader("📌 Danh Sách Học Viên Cần Can Thiệp Gấp")
            
            # Lọc danh sách nguy cơ và sắp xếp theo xác suất bỏ học giảm dần
            df_at_risk = df[df['Trang_Thai_Canh_Bao'] == "⚠️ Có Nguy Cơ Bỏ Học"].sort_values(
                by="Xac_Suat_Bo_Hoc", ascending=False
            )

            if len(df_at_risk) > 0:
                # Định dạng hiển thị màu sắc
                st.dataframe(
                    df_at_risk.style.highlight_between(
                        subset=['Xac_Suat_Bo_Hoc'], 
                        left=custom_threshold*100, 
                        right=100, 
                        color='#ffcccc'
                    )
                )

                # Nút tải danh sách cần chăm sóc về máy (CSV)
                csv_data = df_at_risk.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Tải Danh Sách Học Viên Cần Can Thiệp (.CSV)",
                    data=csv_data,
                    file_name="danh_sach_hoc_vien_nguy_co_bo_hoc.csv",
                    mime="text/csv"
                )
            else:
                st.balloons()
                st.success("Tuyệt vời! Không có học viên nào vượt ngưỡng nguy cơ bỏ học.")

        else:
            st.error(f"File thiếu các cột thuộc tính cần thiết: {feature_cols}")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi đọc file: {e}")

else:
    # Hướng dẫn khi chưa upload file
    st.info("👆 Vui lòng tải file dữ liệu học viên (CSV/Excel) ở thanh bên trái để bắt đầu.")
    st.markdown("""
    **Cấu trúc các cột bắt buộc có trong file:**
    * `so_bai_tap_hoan_thanh`: Số bài tập đã nộp (0 - 10)
    * `diem_kt_giua_ky`: Điểm kiểm tra giữa kỳ (0.0 - 10.0)
    * `gio_hoc_tuan`: Số giờ học trung bình mỗi tuần
    * `da_dong_hoc_phi_day_du`: 1 (Đã đóng) hoặc 0 (Chưa đóng)
    """)