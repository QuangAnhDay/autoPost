# 🚀 Auto Post Facebook - Premium Desktop GUI v3.0

Hệ thống tự động hóa đăng bài Facebook vào nhiều nhóm cùng lúc với **giao diện Desktop GUI chuyên nghiệp (phong cách Windows 11 Dark Mode)** và **kiến trúc đa luồng song song thực sự (Multi-threading)**. 

Dự án sử dụng trình duyệt thật (Playwright Chromium) mô phỏng hành vi người dùng thực tế để giảm thiểu tối đa rủi ro checkpoint/khóa tài khoản.

---

## ✨ Tính năng cao cấp mới (v3.0)

| Tính năng | Chi tiết công nghệ | Lợi ích người dùng |
| :--- | :--- | :--- |
| 🖥️ **Desktop GUI Premium** | Thiết kế phong cách Windows 11 Dark Mode, bảng dữ liệu giống Excel | Nhập liệu trực tiếp, chỉnh sửa, thêm/xóa dòng cực kỳ nhanh chóng và trực quan. |
| ⚡ **Đa Luồng Song Song** | Nhân bản profile session, khởi chạy nhiều cửa sổ Chromium độc lập cùng lúc | Chuẩn bị hàng loạt bài viết cùng một lúc (song song thực sự), tiết kiệm tới 80% thời gian chờ đợi. |
| 📁 **Custom Media Dialog** | Hộp thoại chọn media Tiếng Việt tùy biến: **📁 Chọn Folder** hoặc **🖼️ Chọn Files** | Thao tác chọn tệp trực quan, dễ hiểu hơn so với hộp thoại Yes/No/Cancel mặc định. |
| 🛡️ **Bypass File Explorer OS** | Đón đầu File Chooser bằng Playwright, chặn đứng hộp thoại Windows | Loại bỏ hoàn toàn lỗi treo/kẹt luồng tự động hóa khi Facebook kích hoạt cửa sổ chọn file hệ thống. |
| 🎯 **Cột Chọn Đăng `✅`** | Double-click để Bật/Tắt tích chọn dòng đăng | Chỉ đăng những dòng được tích `✅`. Có thể đăng lại bất kỳ lúc nào mà không bị ràng buộc bởi cột Status. |
| ⏰ **Realtime Status** | Ghi nhận chi tiết thời gian và tỉ lệ đăng thành công: `HH:MM (TC/Tổng)` | Trực quan hóa tiến độ. Cho phép xóa status cũ để tái đăng bài nhiều lần trong ngày. |

---

## 📦 Cài đặt nhanh (Windows)

### Yêu cầu hệ thống
- **Python 3.10** trở lên (Khuyên dùng Python 3.13)
- Trình duyệt **Playwright Chromium**

### Các bước cài đặt:

1. **Tải mã nguồn về máy** và mở thư mục dự án bằng PowerShell:
   ```powershell
   cd d:\myProject\autoPost\autoPost\autoPost
   ```

2. **Tạo môi trường ảo Python và cài đặt thư viện**:
   ```powershell
   # Tạo môi trường ảo
   python -m venv .venv

   # Kích hoạt môi trường ảo
   .venv\Scripts\activate

   # Cài đặt các thư viện cần thiết
   pip install -r requirements.txt
   ```

3. **Cài đặt trình duyệt tự động hóa Playwright**:
   ```powershell
   playwright install chromium
   ```

---

## 📑 Hướng dẫn cấu trúc bảng dữ liệu

Giao diện bảng nhập liệu của AutoPost v3.0 gồm **6 cột** chuẩn:

| Cột | Tên Cột | Chức Năng | Định Dạng Nhập Liệu / Ví Dụ |
| :--- | :--- | :--- | :--- |
| **1** | `Chọn` | Tích chọn để đăng dòng này | Nhấp đúp chuột (`double-click`) để đảo trạng thái giữa `✅` và rỗng. |
| **2** | `Ma_Bai_Dang` | Ký hiệu phân biệt | `SALE_AMAZON_01` |
| **3** | `Link_Bai_Dang` | Danh sách link nhóm Facebook | Ngăn cách nhau bằng dấu `\|`. <br> *Ví dụ:* `https://fb.com/groups/grp1 \| https://fb.com/groups/grp2` |
| **4** | `Caption` | Nội dung văn bản bài viết | Hỗ trợ viết nhiều dòng. Xuống dòng trực tiếp trong ô. |
| **5** | `Anh_Video` | Đường dẫn chứa ảnh hoặc video | Bấm đúp vào ô để mở **Custom Dialog chọn Media Tiếng Việt**: <br> 1. Chọn Thư mục chứa ảnh/video <br> 2. Chọn từng file ảnh/video riêng lẻ |
| **6** | `Status` | Trạng thái và lịch sử đăng | Hệ thống tự ghi nhận thời gian khi đăng thành công (ví dụ: `15:30 (2/2)`). <br> Bạn có thể nhấp chọn và xóa đi để tái đăng bài. |

---

## ▶️ Quy trình vận hành & Sử dụng

### Khởi chạy giao diện:
```powershell
& .venv/Scripts/python.exe gui.py
```

### Luồng làm việc thông minh v3.0:

```
                  ┌──────────────────────────────────────────────┐
                  │          Nhập/Sửa bài viết trên GUI          │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 1. ĐĂNG NHẬP: Mở 1 trình duyệt chính duy nhất│
                  │   để đăng nhập & lưu session sạch → Bấm OK   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 2. ĐA LUỒNG SONG SONG: Tự động nhân bản và   │
                  │   mở song song hàng loạt cửa sổ Chromium.    │
                  └──────────────────────┬───────────────────────┘
                                         │
┌────────────────────────────────────────┴────────────────────────────────────────┐
│  Các cửa sổ tự động làm việc SONG SONG cùng một lúc:                            │
│  - Truy cập group Facebook tương ứng.                                           │
│  - Bypass File Explorer để nạp ảnh/video trực tiếp siêu tốc.                     │
│  - Gõ caption tự động với delay ngẫu nhiên chống bot.                           │
│  - Đặt trạng thái về "CHỜ BẤM ĐĂNG..." và đứng im giữ mở trình duyệt.           │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 3. KIỂM TRA & BẤM ĐĂNG: Bạn chuyển qua từng  │
                  │   cửa sổ Chromium để kiểm tra lại bài đăng   │
                  │   đã soạn sẵn và tự tay bấm "Đăng".          │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 4. HOÀN TẤT: Quay lại GUI bấm [OK] ở popup   │
                  │  → Đóng sạch trình duyệt, dọn cache profile  │
                  │  → Ghi realtime status: HH:MM (Thành công/TC)│
                  └──────────────────────────────────────────────┘
```

---

## ⚙️ Cấu trúc thư mục dự án

```
autoPost/
├── gui.py                          # 🖥️ Giao diện Desktop GUI Premium (Chạy file này)
├── main.py                         # 🚀 CLI Engine (Dành cho chế độ dòng lệnh)
├── requirements.txt                # 📦 Các thư viện phụ thuộc Python
├── README.md                       # 📖 Tài liệu hướng dẫn sử dụng này
│
├── core/                           # ⚙️ Nhân Engine xử lý Logic
│   ├── browser_manager.py          #    Điều khiển tương tác Facebook Chromium
│   ├── excel_manager.py            #    Đọc/xuất dữ liệu Excel & Tệp tin
│   └── data_manager.py             #    Xử lý cấu trúc dữ liệu JSON/DataFrame
│
├── data/                           # 📊 Dữ liệu lưu trữ Local
│   └── danh_sach_bai_dang.json     #    Dữ liệu bài đăng được đồng bộ thời gian thực
│
└── profiles/                       # 🔒 Quản lý phiên đăng nhập (Tự động sinh ra)
    ├── fb_session_main/            #    Profile phiên chính (gốc) của bạn
    └── fb_session_main_temp_X/     #    Các profile tạm thời phục vụ chạy đa luồng
```

---

## 🔒 Cơ chế An Toàn & Bảo Mật

1. **Lưu phiên an toàn:** Phiên đăng nhập Facebook của bạn được lưu cục bộ trong thư mục `profiles/fb_session_main/` trên máy tính cá nhân dưới dạng mã hóa của Chromium. Không gửi hay lưu trữ bất kỳ thông tin nào lên máy chủ bên thứ ba.
2. **Hành vi tự nhiên:** Quá trình nhập liệu caption sử dụng cơ chế gõ phím tuần tự có khoảng trễ thời gian ngẫu nhiên (`random delay`), qua mặt hoàn toàn các bộ quét tự động hóa đơn giản.
3. **Bán tự động tối ưu:** Hệ thống tự động làm 99% các bước nặng nhọc nhất (mở nhóm, tìm ô đăng, tải ảnh lên, gõ bài). Bước click **Đăng** cuối cùng do chính bạn thao tác thủ công, đảm bảo Facebook nhận diện đây là hành động tự nguyện của người dùng thật.
