"""
gui.py - Giao diện Desktop dạng ô lưới cho AutoPost.

Sử dụng tkinter + tksheet để tạo bảng nhập liệu giống Excel.
Người dùng nhập Caption, Link nhóm FB, đường dẫn ảnh/video trực tiếp trên bảng.
Bấm "Bắt đầu đăng" để trigger Playwright posting engine.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import datetime
import random
import shutil

import sv_ttk
import tksheet

# Thêm thư mục gốc vào PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.data_manager import doc_posts, ghi_posts, tao_bai_moi, posts_to_dataframe
from core.data_manager import cap_nhat_status_json

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════
COLUMNS = ["Mã bài", "Link nhóm FB", "Caption", "Ảnh/Video", "Status", "Chọn"]
COL_KEYS = ["ma_bai", "links", "caption", "media", "status", "chon"]
WINDOW_TITLE = "🚀 AutoPost - Quản lý bài đăng"
WINDOW_SIZE = "1200x700"
MIN_WIDTH = 900
MIN_HEIGHT = 500


class AutoPostGUI:
    """Cửa sổ chính của ứng dụng AutoPost Desktop."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Áp dụng theme Sun Valley (Windows 11 style)
        sv_ttk.set_theme("dark")

        self.dang_chay = False  # Flag đang chạy posting engine
        self._posting_thread = None

        self._tao_giao_dien()
        self._tai_du_lieu()

    # ═══════════════════════════════════════════════════════════
    # TẠO GIAO DIỆN
    # ═══════════════════════════════════════════════════════════

    def _tao_giao_dien(self):
        """Tạo toàn bộ layout: toolbar + spreadsheet + log."""
        # --- Toolbar ---
        self._tao_toolbar()

        # --- Spreadsheet (bảng lưới) ---
        self._tao_spreadsheet()

        # --- Log Panel ---
        self._tao_log_panel()

    def _tao_toolbar(self):
        """Tạo thanh công cụ phía trên."""
        toolbar = ttk.Frame(self.root, padding=(10, 5))
        toolbar.pack(fill=tk.X)

        # Nút bên trái
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT)

        ttk.Button(left_frame, text="➕ Thêm dòng", command=self._them_dong,
                   style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_frame, text="🗑️ Xóa dòng", command=self._xoa_dong).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(left_frame, text="📂 Chọn Media", command=self._chon_media).pack(side=tk.LEFT, padx=(15, 5))
        ttk.Button(left_frame, text="💾 Lưu", command=self._luu_du_lieu).pack(side=tk.LEFT, padx=(0, 5))

        # Nút bên phải
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT)

        self.btn_dang = ttk.Button(right_frame, text="▶️ Bắt đầu đăng",
                                    command=self._bat_dau_dang, style="Accent.TButton")
        self.btn_dang.pack(side=tk.RIGHT)

    def _tao_spreadsheet(self):
        """Tạo bảng lưới spreadsheet (tksheet)."""
        sheet_frame = ttk.Frame(self.root)
        sheet_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        self.sheet = tksheet.Sheet(
            sheet_frame,
            headers=COLUMNS,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            height=350,
        )
        self.sheet.pack(fill=tk.BOTH, expand=True)

        # Cấu hình bảng
        self.sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_select",
            "drag_select",
            "select_all",
            "column_width_resize",
            "row_height_resize",
            "arrowkeys",
            "right_click_popup_menu",
            "rc_select",
            "copy",
            "cut",
            "paste",
            "delete",
            "undo",
            "edit_cell",
        ))

        # Độ rộng cột mặc định
        self.sheet.column_width(column=0, width=120)   # Mã bài
        self.sheet.column_width(column=1, width=280)   # Link nhóm FB
        self.sheet.column_width(column=2, width=300)   # Caption
        self.sheet.column_width(column=3, width=220)   # Ảnh/Video
        self.sheet.column_width(column=4, width=140)   # Status
        self.sheet.column_width(column=5, width=60)    # Chọn

        # Cột Status chỉ đọc (không cho sửa tay trực tiếp nhưng có thể tự xóa)
        self.sheet.readonly_columns(columns=[4])

        # Bind sự kiện double click vào ô để tự động đảo Chọn (cột 5)
        self.sheet.extra_bindings("double_click_left_click", self._double_click_sheet)

    def _double_click_sheet(self, event = None):
        """Khi người dùng double click vào cột Chọn, tự động toggle trạng thái giữa ✅ và trống."""
        try:
            selected = self.sheet.get_currently_selected()
            if selected is None:
                return
            row, col = selected.row, selected.column
            if col == 5:  # Cột Chọn (0-indexed)
                current = str(self.sheet.get_cell_data(row, col)).strip()
                new_val = "" if current == "✅" else "✅"
                self.sheet.set_cell_data(row, col, new_val)
                self.sheet.refresh()
        except Exception as e:
            self._ghi_log(f"Lỗi nhấp đúp ô: {e}")

    def _tao_log_panel(self):
        """Tạo panel log bên dưới."""
        log_frame = ttk.LabelFrame(self.root, text="📋 Log", padding=(5, 5))
        log_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD,
                                bg="#1e1e1e", fg="#d4d4d4",
                                font=("Consolas", 10),
                                insertbackground="#ffffff",
                                selectbackground="#264f78",
                                relief=tk.FLAT, padx=8, pady=5)
        self.log_text.pack(fill=tk.X, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.configure(state=tk.DISABLED)

    # ═══════════════════════════════════════════════════════════
    # QUẢN LÝ DỮ LIỆU
    # ═══════════════════════════════════════════════════════════

    def _tai_du_lieu(self):
        """Tải dữ liệu từ file JSON vào bảng lưới."""
        posts = doc_posts()
        if not posts:
            # Tạo 3 dòng trống mặc định
            posts = [tao_bai_moi() for _ in range(3)]

        data = []
        for p in posts:
            row = [p.get(k, "") for k in COL_KEYS]
            data.append(row)

        self.sheet.set_sheet_data(data)
        self._ghi_log("✅ Đã tải dữ liệu thành công.")

    def _lay_du_lieu_tu_bang(self) -> list[dict]:
        """Đọc toàn bộ dữ liệu từ bảng lưới thành list[dict]."""
        data = self.sheet.get_sheet_data()
        posts = []
        for row in data:
            # Bỏ qua dòng hoàn toàn trống
            if all(str(cell).strip() == "" for cell in row):
                continue
            post = {}
            for i, key in enumerate(COL_KEYS):
                post[key] = str(row[i]).strip() if i < len(row) else ""
            posts.append(post)
        return posts

    def _luu_du_lieu(self):
        """Lưu dữ liệu từ bảng lưới vào file JSON."""
        posts = self._lay_du_lieu_tu_bang()
        ghi_posts(posts)
        self._ghi_log(f"💾 Đã lưu {len(posts)} bài đăng.")

    # ═══════════════════════════════════════════════════════════
    # TOOLBAR ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _them_dong(self):
        """Thêm một dòng trống vào cuối bảng sử dụng thao tác mảng (Độc lập phiên bản)."""
        try:
            data = self.sheet.get_sheet_data()
            new_row = ["", "", "", "", "", "✅"]
            data.append(new_row)
            self.sheet.set_sheet_data(data)
            self.sheet.refresh()
            self._ghi_log("➕ Đã thêm 1 dòng trống mới.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm dòng: {e}")

    def _xoa_dong(self):
        """Xóa các dòng đang được chọn sử dụng thao tác mảng (Độc lập phiên bản)."""
        try:
            selected = self.sheet.get_selected_rows()
            if not selected:
                messagebox.showwarning("Chưa chọn dòng", "Hãy chọn ít nhất 1 dòng để xóa.")
                return

            if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa {len(selected)} dòng?"):
                data = self.sheet.get_sheet_data()
                # Xóa từ dưới lên để tránh lệch index
                for row_idx in sorted(selected, reverse=True):
                    if row_idx < len(data):
                        data.pop(row_idx)
                self.sheet.set_sheet_data(data)
                self.sheet.refresh()
                self._ghi_log(f"🗑️ Đã xóa {len(selected)} dòng.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa dòng: {e}")

    def _chon_media(self):
        """Mở hộp thoại thiết kế mới tùy chỉnh 3 nút bằng tiếng Việt thay thế cho askyesnocancel."""
        selected = self.sheet.get_currently_selected()
        if selected is None:
            messagebox.showinfo("Hướng dẫn",
                                "Hãy click vào ô 'Ảnh/Video' của dòng cần chọn media trước,\n"
                                "sau đó bấm nút '📂 Chọn Media'.")
            return

        try:
            row = selected.row
        except AttributeError:
            messagebox.showinfo("Hướng dẫn", "Hãy click vào 1 ô cụ thể trên bảng trước.")
            return

        # Tạo Custom TopLevel window để hiển thị 3 nút chuẩn Việt
        dialog = tk.Toplevel(self.root)
        dialog.title("Chọn nguồn tải Media")
        dialog.geometry("380x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Căn giữa màn hình so với cửa sổ chính
        x = self.root.winfo_x() + (self.root.winfo_width() - 380) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl = ttk.Label(frame, text="Bạn muốn tải lên tệp tin hay thư mục media?", font=("Segoe UI", 11, "bold"))
        lbl.pack(pady=(0, 20))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        result = {"path": None}

        def chon_thu_muc():
            path = filedialog.askdirectory(title="Chọn thư mục chứa ảnh/video")
            if path:
                result["path"] = path
            dialog.destroy()

        def chon_file():
            paths = filedialog.askopenfilenames(
                title="Chọn các file ảnh/video",
                filetypes=[
                    ("Media files", "*.jpg *.jpeg *.png *.gif *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.webm"),
                    ("All files", "*.*"),
                ]
            )
            if paths:
                result["path"] = " | ".join(paths)
            dialog.destroy()

        def huy_bo():
            dialog.destroy()

        btn_folder = ttk.Button(btn_frame, text="📁 Thư mục", command=chon_thu_muc, style="Accent.TButton")
        btn_folder.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_file = ttk.Button(btn_frame, text="🖼️ Ảnh/Video", command=chon_file)
        btn_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        btn_close = ttk.Button(btn_frame, text="❌ Hủy", command=huy_bo)
        btn_close.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Đợi cửa sổ đóng
        self.root.wait_window(dialog)

        path = result["path"]
        if path:
            media_col = COL_KEYS.index("media")  # Cột Ảnh/Video
            current = str(self.sheet.get_cell_data(row, media_col)).strip()
            if current:
                path = current + " | " + path
            self.sheet.set_cell_data(row, media_col, path)
            self._ghi_log(f"📂 Đã chọn media cho dòng {row + 1}")

    # ═══════════════════════════════════════════════════════════
    # POSTING ENGINE
    # ═══════════════════════════════════════════════════════════

    def _bat_dau_dang(self):
        """Bắt đầu tiến trình đăng bài."""
        if self.dang_chay:
            messagebox.showwarning("Đang chạy", "Tiến trình đăng bài đang chạy. Vui lòng đợi hoàn tất.")
            return

        # Lưu dữ liệu trước
        self._luu_du_lieu()

        posts = self._lay_du_lieu_tu_bang()
        # Lọc các bài viết được tích chọn (cột Chọn có giá trị ✅)
        posts_duoc_chon = [p for p in posts
                           if p.get('ma_bai', '').strip()
                           and p.get('chon', '').strip() == '✅']

        if not posts_duoc_chon:
            messagebox.showinfo("Thông báo", "Không có bài đăng nào được tích chọn (✅) để đăng.\n"
                                             "Vui lòng nhấp đúp ô ở cột 'Chọn' để tích chọn bài viết.")
            return

        # Gom toàn bộ link nhóm để tính tổng số cửa sổ
        tong_so_cua_so = 0
        from core.excel_manager import tach_danh_sach
        for p in posts_duoc_chon:
            links = tach_danh_sach(p.get('links', ''))
            tong_so_cua_so += len(links)

        confirm = messagebox.askyesno(
            "Xác nhận đăng bài hàng loạt",
            f"Hệ thống sẽ chuẩn bị SONG SONG {tong_so_cua_so} cửa sổ trình duyệt cho {len(posts_duoc_chon)} bài viết được chọn.\n\n"
            "Quy trình thực hiện:\n"
            "  1. Trình duyệt chính mở lên: Bạn đăng nhập Facebook (nếu cần) rồi click [OK] để lưu phiên đăng nhập.\n"
            "  2. Hệ thống nhân bản profile và mở song song {tong_so_cua_so} cửa sổ chuẩn bị toàn bộ các bài viết cùng lúc.\n"
            "  3. Bạn đi một vòng bấm 'Đăng' trên từng cửa sổ.\n"
            "  4. Click [OK] trên GUI để hoàn tất và tự động dọn dẹp các cửa sổ.\n\n"
            "Bắt đầu?",
            parent=self.root
        )

        if not confirm:
            return

        self.dang_chay = True
        self.btn_dang.configure(text="⏳ Đang chuẩn bị...", state=tk.DISABLED)
        self._ghi_log("🚀 Bắt đầu tiến trình chuẩn bị đăng bài hàng loạt...")

        # Chạy trên thread riêng để GUI không bị đơ
        self._posting_thread = threading.Thread(
            target=self._chay_posting_engine,
            args=(posts_duoc_chon,),
            daemon=True,
        )
        self._posting_thread.start()

    def _chay_posting_engine(self, posts: list[dict]):
        """Chạy Playwright posting engine trên thread riêng chuẩn bị song song hàng loạt."""
        try:
            from playwright.sync_api import sync_playwright
            from core.excel_manager import tach_danh_sach, phan_giai_media
            from core.browser_manager import (
                SESSION_DIR,
                dieu_huong_toi_nhom, mo_hop_thoai_dang_bai,
                tai_file_media, go_caption, dong_trinh_duyet,
            )

            df = posts_to_dataframe(posts)

            # Tạo event chờ chung để đóng các browser sau khi đăng xong
            event_cho_dang = threading.Event()

            # Thu thập tất cả các nhiệm vụ chuẩn bị tab
            nhiem_vu = []
            for idx, row in df.iterrows():
                ma_bai = str(row['Ma_Bai_Dang']).strip()
                caption = str(row['Caption']).strip()
                if caption.lower() == 'nan':
                    caption = ""
                links = tach_danh_sach(row['Link_Bai_Dang'])
                media = phan_giai_media(row['Anh_Video'])
                
                for stt, url in enumerate(links, start=1):
                    nhiem_vu.append({
                        'ma_bai': ma_bai,
                        'url': url,
                        'media': media,
                        'caption': caption,
                        'stt': stt,
                        'tong': len(links),
                        'event_cho_dang': event_cho_dang,
                        'event_chuan_bi_xong': threading.Event()
                    })

            if not nhiem_vu:
                self._ghi_log_safe("❌ Không tìm thấy liên kết nhóm nào hợp lệ để đăng.")
                return

            # BƯỚC 1: Mở trình duyệt chính một lần duy nhất để người dùng đăng nhập/kiểm tra phiên đăng nhập
            self._ghi_log_safe("🌐 Đang mở trình duyệt chính để xác nhận đăng nhập Facebook...")
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=SESSION_DIR,
                    headless=False,
                    viewport={'width': 1100, 'height': 800},
                    locale='vi-VN',
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                    ]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.on("dialog", lambda d: d.accept())
                
                self._ghi_log_safe("📱 Đang chuyển hướng tới Facebook...")
                page.goto('https://www.facebook.com/', wait_until='domcontentloaded')
                time.sleep(3)

                # Chờ người dùng đăng nhập bằng dialog trên GUI
                self._cho_dang_nhap_event = threading.Event()
                self.root.after(0, self._hien_thi_cho_dang_nhap_dialog)
                self._cho_dang_nhap_event.wait()

                # Đóng trình duyệt chính để lưu session sạch
                context.close()
                self._ghi_log_safe("🔒 Đã lưu phiên đăng nhập chính thành công.")

            # BƯỚC 2: Khởi chạy song song các luồng (mỗi luồng một trình duyệt riêng)
            self._ghi_log_safe(f"🚀 Bắt đầu mở SONG SONG {len(nhiem_vu)} cửa sổ trình duyệt...")

            threads = []
            ban_ghi_thanh_cong = {}
            temp_dirs = []

            for task_idx, task in enumerate(nhiem_vu, start=1):
                t = threading.Thread(
                    target=self._chay_task_song_song,
                    args=(task, task_idx, len(nhiem_vu), ban_ghi_thanh_cong, temp_dirs),
                    daemon=True
                )
                threads.append(t)
                t.start()
                # Tạo độ trễ ngắn 2s để tránh các trình duyệt mở dồn dập cùng 1 lúc gây quá tải
                time.sleep(2)

            # Đợi toàn bộ các luồng con chuẩn bị xong nội dung (hoặc báo lỗi)
            self._ghi_log_safe("⏳ Đang chuẩn bị bài đăng trên các cửa sổ...")
            for task in nhiem_vu:
                task['event_chuan_bi_xong'].wait()

            self._ghi_log_safe("🔔 Đã chuẩn bị xong tất cả bài viết! Mời bạn kiểm tra và tự tay bấm đăng.")

            # Lúc này mới hiển thị Dialog chờ người dùng kiểm tra và bấm Đăng trên các cửa sổ
            self._cho_bam_dang_event = threading.Event()
            self.root.after(0, lambda n=len(nhiem_vu): self._hien_thi_cho_dang_dialog(n))
            self._cho_bam_dang_event.wait()

            # Kích hoạt toàn bộ các event để các luồng đóng trình duyệt của mình
            self._ghi_log_safe("🧹 Đang đóng toàn bộ các cửa sổ trình duyệt...")
            for task in nhiem_vu:
                task['event_cho_dang'].set()

            # Chờ các thread kết thúc để dọn dẹp thư mục tạm
            for t in threads:
                t.join(timeout=10)

            # Dọn dẹp các thư mục session tạm thời
            for tmp in temp_dirs:
                if os.path.exists(tmp):
                    try:
                        shutil.rmtree(tmp, ignore_errors=True)
                    except:
                        pass

            # Cập nhật Status và log hoàn thành với ngày giờ cụ thể
            bay_gio = datetime.datetime.now().strftime("%H:%M (%d/%m)")
            for idx, row in df.iterrows():
                ma_bai = str(row['Ma_Bai_Dang']).strip()
                links = tach_danh_sach(row['Link_Bai_Dang'])
                so_tc = ban_ghi_thanh_cong.get(ma_bai, 0)
                
                ket_qua = f"{bay_gio} ({so_tc}/{len(links)})"
                cap_nhat_status_json(ma_bai, ket_qua)
                self._cap_nhat_status_bang(ma_bai, ket_qua)
                self._ghi_log_safe(f"🏁 [{ma_bai}] → {ket_qua}")

            self._ghi_log_safe("🎉 HOÀN THÀNH TẤT CẢ CÁC BÀI VIẾT!")

        except Exception as e:
            self._ghi_log_safe(f"❌ LỖI NGHIÊM TRỌNG: {e}")

        finally:
            self.dang_chay = False
            self.root.after(0, lambda: self.btn_dang.configure(
                text="▶️ Bắt đầu đăng", state=tk.NORMAL
            ))

    def _chay_task_song_song(self, task, task_idx, total_tasks, ban_ghi_thanh_cong, temp_dirs):
        """Luồng con xử lý song song mở trình duyệt độc lập."""
        from playwright.sync_api import sync_playwright
        from core.browser_manager import SESSION_DIR, dieu_huong_toi_nhom, mo_hop_thoai_dang_bai, go_caption

        ma_bai = task['ma_bai']
        url = task['url']
        media = task['media']
        caption = task['caption']
        stt = task['stt']
        tong = task['tong']

        self._ghi_log_safe(f"➡️ Cửa sổ {task_idx}/{total_tasks}: Đang mở trình duyệt cho [{ma_bai}] Nhóm {stt}/{tong}...")
        self._cap_nhat_status_bang(ma_bai, "ĐANG CHUẨN BỊ...")

        # Tạo thư mục session tạm thời cho luồng này để tránh xung đột SingletonLock của Chromium
        temp_session = f"{SESSION_DIR}_temp_{task_idx}"
        temp_dirs.append(temp_session)
        os.makedirs(temp_session, exist_ok=True)
        if os.path.exists(SESSION_DIR):
            try:
                shutil.copytree(SESSION_DIR, temp_session, dirs_exist_ok=True)
                # Xóa file lock của Chromium nếu có
                lock_file = os.path.join(temp_session, "SingletonLock")
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except Exception as e_copy:
                self._ghi_log_safe(f"⚠️ Cảnh báo copy profile: {e_copy}")

        try:
            with sync_playwright() as p:
                # Khởi tạo trình duyệt riêng biệt cho luồng này
                context = p.chromium.launch_persistent_context(
                    user_data_dir=temp_session,
                    headless=False,
                    viewport={'width': 1000, 'height': 750},
                    locale='vi-VN',
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                    ]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.on("dialog", lambda d: d.accept())

                success = False
                try:
                    # Chuyển hướng trực tiếp tới nhóm
                    if dieu_huong_toi_nhom(page, url):
                        if mo_hop_thoai_dang_bai(page):
                            # Gọi hàm tai_file_media_safe xử lý thông minh để chặn File Explorer OS!
                            if self._tai_file_media_safe(page, media):
                                if go_caption(page, caption):
                                    success = True

                    if success:
                        ban_ghi_thanh_cong[ma_bai] = ban_ghi_thanh_cong.get(ma_bai, 0) + 1
                        self._cap_nhat_status_bang(ma_bai, "CHỜ BẤM ĐĂNG...")
                        self._ghi_log_safe(f"  ✅ Cửa sổ {task_idx} cho [{ma_bai}] chuẩn bị XONG!")
                    else:
                        self._cap_nhat_status_bang(ma_bai, "THẤT BẠI")
                        self._ghi_log_safe(f"  ❌ Cửa sổ {task_idx} cho [{ma_bai}] bị LỖI chuẩn bị.")
                except Exception as task_err:
                    self._cap_nhat_status_bang(ma_bai, "LỖI")
                    self._ghi_log_safe(f"  ❌ Lỗi tương tác ở cửa sổ {task_idx} ([{ma_bai}]): {task_err}")
                finally:
                    task['event_chuan_bi_xong'].set()

                # DÙ THÀNH CÔNG HAY LỖI, LUÔN LUÔN GIỮ CỬA SỔ TRÌNH DUYỆT MỞ CHỜ USER BẤM ĐĂNG XONG
                task['event_cho_dang'].wait()

                # Đóng trình duyệt
                context.close()

        except Exception as e:
            self._ghi_log_safe(f"❌ Lỗi khởi động trình duyệt ở cửa sổ {task_idx} ([{ma_bai}]): {e}")

    def _tai_file_media_safe(self, page, media_files) -> bool:
        """Hàm tải file media cải tiến vượt trội: Sử dụng expect_file_chooser để chặn đứng cửa sổ File Explorer OS."""
        if not media_files:
            return True

        self._ghi_log_safe("  📎 Đang tải lên các file media song song...")

        try:
            # Lấy dialog đăng bài
            dialog = page.locator('div[role="dialog"]').first

            # Các selectors nút Ảnh/video
            cac_selector_media = [
                'div[aria-label*="Ảnh/video"]',
                'div[aria-label*="Photo/video"]',
                'div[aria-label*="Ảnh/Video"]',
                'div[aria-label*="Photo/Video"]',
            ]

            da_tai = False
            # Thử bắt sự kiện File Chooser khi click vào nút Ảnh/video
            for sel in cac_selector_media:
                try:
                    icon = dialog.locator(sel).first
                    if icon.is_visible(timeout=2000):
                        # DÙNG expect_file_chooser ĐỂ CHẶN HOÀN TOÀN HỘP THOẠI WINDOWS FILE EXPLORER
                        try:
                            with page.expect_file_chooser(timeout=3000) as fc_info:
                                icon.click(force=True)
                            file_chooser = fc_info.value
                            file_chooser.set_files(media_files)
                            da_tai = True
                            break
                        except Exception:
                            # Nếu click không mở file chooser mà chỉ hiện dropzone
                            icon.click(force=True)
                            time.sleep(2)
                            break
                except Exception:
                    continue

            if not da_tai:
                # Thử tìm input file trực tiếp trên trang để nạp file
                all_file_inputs = page.locator("input[type='file']")
                count = all_file_inputs.count()
                if count > 0:
                    file_input = all_file_inputs.nth(count - 1)
                    file_input.set_input_files(media_files)
                    da_tai = True

            if da_tai:
                # Chờ một lúc để file được upload hoàn tất lên giao diện Facebook
                wait_time = max(6, len(media_files) * 3)
                time.sleep(wait_time)
                return True
            else:
                self._ghi_log_safe("  ✗ Không tìm thấy nút tải hoặc ô nhập media.")
                return False

        except Exception as e:
            self._ghi_log_safe(f"  ✗ Lỗi tải file media: {e}")
            return False

    def _hien_thi_cho_dang_nhap_dialog(self):
        """Hiện thông báo chờ đăng nhập tích hợp trực tiếp trên giao diện GUI."""
        messagebox.showinfo(
            "Xác thực Facebook",
            "Trình duyệt đã được mở tới trang Facebook.\n\n"
            "1. Hãy đăng nhập tài khoản Facebook của bạn (nếu cần).\n"
            "2. Sau khi đã vào được trang chủ (Bảng tin) Facebook thành công,\n"
            "   hãy bấm [OK] dưới đây để hệ thống bắt đầu tự động chuẩn bị các tab đăng bài!",
            parent=self.root
        )
        self._cho_dang_nhap_event.set()

    def _hien_thi_cho_dang_dialog(self, count: int):
        """Hiện thông báo chờ người dùng bấm Đăng trên tất cả các tab."""
        messagebox.showinfo(
            "Xác nhận đã Đăng bài",
            f"Đã chuẩn bị xong {count} cửa sổ trình duyệt song song cho các bài viết được chọn.\n\n"
            "👉 Hãy chuyển qua các cửa sổ trình duyệt, kiểm tra và bấm nút 'Đăng' trên từng cửa sổ.\n"
            "👉 Sau khi đã bấm Đăng XONG HẾT, click nút [OK] ở đây để hoàn tất và đóng toàn bộ.",
            parent=self.root
        )
        self._cho_bam_dang_event.set()

    # ═══════════════════════════════════════════════════════════
    # TIỆN ÍCH
    # ═══════════════════════════════════════════════════════════

    def _ghi_log(self, message: str):
        """Ghi log vào panel (chạy trên GUI thread)."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}]  {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _ghi_log_safe(self, message: str):
        """Ghi log thread-safe (gọi từ thread khác GUI)."""
        self.root.after(0, lambda: self._ghi_log(message))

    def _cap_nhat_status_bang(self, ma_bai: str, status: str):
        """Cập nhật cột Status trên bảng lưới theo mã bài."""
        def _update():
            data = self.sheet.get_sheet_data()
            ma_col = COL_KEYS.index("ma_bai")
            status_col = COL_KEYS.index("status")
            for row_idx, row in enumerate(data):
                if str(row[ma_col]).strip() == ma_bai.strip():
                    self.sheet.set_cell_data(row_idx, status_col, status)
                    break
            self.sheet.refresh()
        self.root.after(0, _update)

    def chay(self):
        """Khởi chạy vòng lặp chính của GUI."""
        # Xử lý đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self._dong_ung_dung)
        self.root.mainloop()

    def _dong_ung_dung(self):
        """Xử lý khi đóng cửa sổ."""
        if self.dang_chay:
            if not messagebox.askyesno("Đang chạy",
                                       "Tiến trình đăng bài đang chạy.\nBạn có chắc muốn thoát?"):
                return

        # Auto-save khi đóng
        try:
            posts = self._lay_du_lieu_tu_bang()
            if posts:
                ghi_posts(posts)
        except Exception:
            pass

        self.root.destroy()


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = AutoPostGUI()
    app.chay()
