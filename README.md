# 🚀 Auto Post Facebook - Hệ Thống Bán Tự Động v2.5

Hệ thống hỗ trợ đăng bài Facebook vào nhiều nhóm cùng lúc, sử dụng trình duyệt thật (Playwright) để tránh bị Facebook phát hiện là bot.

## ✨ Tính năng chính

| Tính năng | Mô tả |
| :--- | :--- |
| 🌐 **Google Sheets Online** | Đọc/ghi dữ liệu trực tiếp từ link Google Sheet, không cần tải file về máy |
| 📂 **Excel Local** | Vẫn hỗ trợ file `.xlsx` trên máy tính như cách cũ |
| 📑 **Đăng hàng loạt (Batch)** | Mở nhiều tab cùng lúc, chuẩn bị tất cả, bấm Đăng liên tục |
| 📁 **Quét thư mục Media** | Chỉ cần ghi đường dẫn folder, hệ thống tự tìm tất cả ảnh/video bên trong |
| 🔒 **Lưu phiên đăng nhập** | Chỉ cần đăng nhập Facebook 1 lần, các lần sau tự nhớ |
| 🛡️ **Bảo vệ tài khoản** | Bước cuối (bấm Đăng) luôn do người dùng thao tác bằng tay |

---

## 📦 Cài đặt

### Yêu cầu hệ thống
- Python 3.10 trở lên
- Hệ điều hành: Linux (khuyến nghị) / Windows / macOS

### Các bước cài đặt

```bash
# 1. Clone hoặc tải dự án về máy
cd ~/Project/autoPost

# 2. Tạo môi trường ảo
python3 -m venv venv

# 3. Kích hoạt môi trường ảo
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate          # Windows

# 4. Cài đặt thư viện
pip install -r requirements.txt

# 5. Cài trình duyệt Playwright
playwright install chromium
```

---

## 📝 Cấu hình dữ liệu

Hệ thống hỗ trợ **2 nguồn dữ liệu** — bạn chọn 1 trong 2:

### Cách 1: Google Sheets Online (Khuyên dùng)

Sửa dữ liệu mọi lúc mọi nơi, hệ thống tự lấy dữ liệu mới nhất.

**Thiết lập lần đầu (chỉ làm 1 lần):**

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Bật **Google Sheets API** và **Google Drive API**
3. Tạo **Service Account** → Tải file JSON về → Đổi tên thành `credentials.json` → Đặt vào thư mục gốc dự án
4. Mở Google Sheet → Nhấn **Chia sẻ** → Thêm email của Service Account → Cấp quyền **Người chỉnh sửa**

**Cấu hình trong code:**

Mở file `main.py`, sửa dòng `NGUON_DU_LIEU`:

```python
# Dán link Google Sheet hoặc ID
NGUON_DU_LIEU = "https://docs.google.com/spreadsheets/d/ID_CUA_BAN/edit"
```

### Cách 2: File Excel Local (.xlsx)

Giữ nguyên mặc định trong `main.py` (không cần sửa gì):

```python
NGUON_DU_LIEU = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'danh_sach_bai_dang.xlsx')
```

Đặt file Excel vào thư mục `data/`.

---

## 📊 Cấu trúc bảng dữ liệu

Dù dùng Google Sheet hay Excel, bảng phải có **đúng 5 cột** sau ở hàng tiêu đề:

| Cột | Tên cột (gõ chính xác) | Mô tả | Ví dụ |
| :--- | :--- | :--- | :--- |
| A | `Ma_Bai_Dang` | Ký hiệu gợi nhớ | `SALE_XE_T11` |
| B | `Link_Bai_Dang` | Link nhóm FB (nhiều link ngăn cách bởi `\|`) | `https://fb.com/groups/abc \| https://fb.com/groups/xyz` |
| C | `Caption` | Nội dung bài viết | Viết thoải mái, xuống dòng bằng `Alt+Enter` |
| D | `Anh_Video` | Đường dẫn file hoặc **thư mục** chứa ảnh/video | Xem bên dưới |
| E | `Status` | **ĐỂ TRỐNG** — Code tự điền khi chạy xong | |

### Cột `Anh_Video` - 3 cách nhập liệu

| Cách | Ví dụ | Mô tả |
| :--- | :--- | :--- |
| **Ghi đường dẫn thư mục** | `/home/user/Videos/post/` | Tự quét tất cả ảnh/video trong folder |
| **Ghi từng file** | `/path/anh1.jpg \| /path/video.mp4` | Liệt kê cụ thể từng file |
| **Kết hợp cả 2** | `/path/folder/ \| /path/anh_them.jpg` | Quét folder + thêm file riêng lẻ |

**Định dạng media được hỗ trợ:**
- Ảnh: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`
- Video: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.flv`

### Ví dụ cụ thể

| Ma_Bai_Dang | Link_Bai_Dang | Caption | Anh_Video | Status |
| :--- | :--- | :--- | :--- | :--- |
| SALE_XE | `https://fb.com/groups/xe1 \| https://fb.com/groups/xe2` | 🎉 Thanh lý xe đạp... | `/home/user/media/xe/` | *(để trống)* |
| TUYEN_IT | `https://fb.com/groups/it_jobs` | 🚀 Tuyển Dev Python... | `/home/user/media/banner.png` | *(để trống)* |

### Quy tắc quan trọng

- Dấu `|` dùng để ngăn cách nhiều giá trị. Có hoặc không có dấu cách xung quanh đều được: `a|b` hoặc `a | b`
- Đường dẫn file/thư mục trên Linux **phân biệt chữ HOA và chữ thường**: `Test.jpg` ≠ `test.jpg`
- Cột `Status` **LUÔN ĐỂ TRỐNG** — hệ thống tự ghi `DONE (X/Y)` khi hoàn thành

---

## ▶️ Cách chạy

```bash
# 1. Kích hoạt môi trường ảo
source venv/bin/activate

# 2. Chạy hệ thống
python main.py
```

### Luồng hoạt động (Batch Mode)

```
┌─────────────────────────────────────────────────────────┐
│  1. Đọc dữ liệu từ Google Sheet / Excel                │
│  2. Kiểm tra đường dẫn media → Báo lỗi nếu sai         │
│  3. Mở trình duyệt Chromium                             │
│  4. Chờ bạn đăng nhập Facebook → Nhấn Enter             │
│                                                         │
│  ╔═══════════════════════════════════════════════╗       │
│  ║  VỚI MỖI BÀI ĐĂNG:                          ║       │
│  ║                                               ║       │
│  ║  a. Mở TAB 1 → Vào nhóm → Gõ bài → Up ảnh   ║       │
│  ║  b. Mở TAB 2 → Vào nhóm → Gõ bài → Up ảnh   ║       │
│  ║  c. Mở TAB 3 → ...                           ║       │
│  ║                                               ║       │
│  ║  ⏸️ TẠM DỪNG 1 LẦN DUY NHẤT                  ║       │
│  ║  → Bạn lướt qua từng tab bấm "Đăng"          ║       │
│  ║  → Nhấn Enter ở Terminal                      ║       │
│  ║                                               ║       │
│  ║  ✅ Tự đóng hết tab phụ                       ║       │
│  ║  ✅ Tự ghi DONE lên Google Sheet / Excel      ║       │
│  ╚═══════════════════════════════════════════════╝       │
│                                                         │
│  5. Chuyển sang bài đăng tiếp theo                      │
│  6. Đóng trình duyệt khi hoàn tất                       │
└─────────────────────────────────────────────────────────┘
```

### Thao tác khi hệ thống đang chạy

1. **Trình duyệt tự mở** → Hiện trang Facebook
2. **Nếu chưa đăng nhập:** Bạn tự đăng nhập, xác thực 2FA
3. **Sau khi vào được Bảng tin:** Quay lại Terminal → Nhấn `Enter`
4. **Hệ thống tự mở nhiều tab** → Vào nhóm → Gõ bài → Tải ảnh → Lặp lại cho tất cả nhóm
5. **Khi tất cả tab đã sẵn sàng:**
   - Hệ thống hiện thông báo: *"Đã chuẩn bị xong X tab"*
   - Bạn chuyển qua từng tab → Bấm nút **"Đăng"** trên Facebook
   - Sau khi đăng hết → Quay lại Terminal → Nhấn `Enter`
6. **Hệ thống tự đóng tab, cập nhật Status, chuyển sang bài tiếp theo**

### Dừng giữa chừng

- Nhấn `Ctrl + C` trên Terminal bất kỳ lúc nào
- Cookie đăng nhập vẫn được lưu
- Cột `Status` cho biết bài nào đã xong → Lần chạy sau tự bỏ qua các bài DONE

---

## 📁 Cấu trúc thư mục

```
autoPost/
├── credentials.json                # 🔑 Chìa khóa Google Sheets API
├── main.py                         # 🚀 File chạy chính
├── requirements.txt                # 📦 Danh sách thư viện
├── README.md                       # 📖 File hướng dẫn này
│
├── core/                           # ⚙️ Mã nguồn logic (KHÔNG CẦN SỬA)
│   ├── __init__.py
│   ├── excel_manager.py            #    Đọc/ghi Google Sheets & Excel
│   └── browser_manager.py          #    Điều khiển trình duyệt Facebook
│
├── data/                           # 📊 Dữ liệu local (nếu dùng Excel)
│   └── danh_sach_bai_dang.xlsx
│
└── profiles/                       # 🔒 Cookie đăng nhập (TỰ ĐỘNG TẠO)
    └── fb_session_main/
```

---

## ❓ Xử lý sự cố

| Lỗi | Nguyên nhân | Cách sửa |
| :--- | :--- | :--- |
| `ModuleNotFoundError` | Chưa cài thư viện | `pip install -r requirements.txt` |
| `File is not a zip file` | File Excel bị lỗi định dạng | Tải lại file `.xlsx` chuẩn từ Google Sheets |
| `KHÔNG TỒN TẠI trên ổ cứng` | Đường dẫn media sai | Kiểm tra lại đường dẫn (Linux phân biệt HOA/thường) |
| `Timeout khi mở hộp thoại` | Facebook đổi giao diện hoặc popup chặn | Kiểm tra trình duyệt, tắt popup thủ công |
| `Lỗi kết nối Google Sheets` | Chưa Share quyền hoặc API chưa bật | Kiểm tra lại quyền Editor cho Service Account |
| `Không tìm thấy cột Status` | Tên cột trong Sheet/Excel bị sai | Đảm bảo hàng tiêu đề ghi chính xác 5 cột |

---

## 📋 Ghi chú kỹ thuật

- **Trình duyệt:** Playwright Chromium (headful mode - có giao diện)
- **Chống bot:** Sử dụng `keyboard.type()` mô phỏng gõ phím thật, delay ngẫu nhiên giữa các thao tác
- **Session:** Lưu tại `profiles/fb_session_main/`, xóa thư mục này nếu muốn đăng nhập lại từ đầu
- **Google Sheets:** Sử dụng `gspread` + Service Account, không cần mở trình duyệt để xác thực
