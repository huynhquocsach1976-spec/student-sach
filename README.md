# 🚀 Hệ Thống Tự Động Hóa CSKH, Cảnh Báo & Can Thiệp Học Viên

Một giải pháp phần mềm toàn diện kết hợp **Data Analytics (Machine Learning)** và **Generative AI (Google Gemini 2.5 Flash)** nhằm tự động hóa quy trình phân tích học viên có nguy cơ bỏ học, báo cáo kết quả học tập và gửi email cá nhân hóa trực tiếp qua Gmail SMTP.

---

## 🌟 Tính Năng Nổi Bật

- **📊 Phân Tích & Dự Đoán Tự Động:** Đọc dữ liệu từ file CSV/Excel, tự động tính toán xác suất bỏ học dựa trên các chỉ số (Chuyên cần, Bài tập, Điểm số, Học phí).
- **🎛️ Tối Ưu Ngưỡng Cảnh Báo (Dynamic Thresholding):** Cho phép điều chỉnh ngưỡng xác suất can thiệp bằng thanh trượt (Slider), ưu tiên chỉ số **Recall** giúp phát hiện tối đa học viên rủi ro.
- **🤖 AI CSKH & Cá Nhân Hóa Nội Dung:** Tích hợp Google Gemini 2.5 Flash để tự động tạo email theo nhiều kịch bản (*Can thiệp bỏ học, Báo cáo học tập, Nhắc học phí*).
- **🚀 Gửi Email Trực Tiếp (Gmail SMTP):** Tích hợp giao thức SMTP cho phép gửi email cá nhân hóa đến từng học viên chỉ với một cú click.
- **📥 Xuất Báo Cáo Linh Hoạt:** Hỗ trợ xuất danh sách học viên rủi ro ra file `.csv` và nội dung email dưới dạng `.txt`.

---

## 🛠️ Công Nghệ Sử Dụng

- **Ngôn ngữ:** Python 3.9+
- **Giao diện Web:** [Streamlit](https://streamlit.io/)
- **Xử lý dữ liệu:** `pandas`, `numpy`
- **Generative AI:** `google-genai` (Google Gemini API)
- **Tự động hóa Email:** `smtplib`, `email.mime`

---

## 📂 Cấu Trúc Dự Án

```text
├── app.py              # Mã nguồn chính của ứng dụng Streamlit
├── requirements.txt    # Danh sách thư viện phụ thuộc
├── .gitignore          # Cấu hình bỏ qua file nhạy cảm (.secrets.toml)
└── README.md           # Tài liệu hướng dẫn & giới thiệu dự án