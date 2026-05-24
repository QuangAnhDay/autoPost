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
COLUMNS = ["Mã bài", "Link nhóm FB", "Caption", "Ảnh/Video", "Status"]
COL_KEYS = ["ma_bai", "links", "caption", "media", "status"]
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
        self.sheet.column_width(column=3, width=250)   # Ảnh/Video
        self.sheet.column_width(column=4, width=100)   # Status

        # Cột Status chỉ đọc (không cho sửa tay)
        # Người dùng vẫn có thể chọn nhưng không edit
        self.sheet.readonly_columns(columns=[4])

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
        """Thêm một dòng trống vào cuối bảng."""
        empty_row = ["" for _ in COLUMNS]
        self.sheet.insert_row(values=empty_row)

    def _xoa_dong(self):
        """Xóa các dòng đang được chọn."""
        selected = self.sheet.get_selected_rows()
        if not selected:
            messagebox.showwarning("Chưa chọn dòng", "Hãy chọn ít nhất 1 dòng để xóa.")
            return

        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa {len(selected)} dòng?"):
            # Xóa từ cuối lên để index không bị lệch
            for row_idx in sorted(selected, reverse=True):
                self.sheet.delete_row(idx=row_idx)
            self._ghi_log(f"🗑️ Đã xóa {len(selected)} dòng.")

    def _chon_media(self):
        """Mở hộp thoại chọn file/thư mục media và điền vào ô đang chọn."""
        selected = self.sheet.get_currently_selected()
        if selected is None:
            messagebox.showinfo("Hướng dẫn",
                                "Hãy click vào ô 'Ảnh/Video' của dòng cần chọn media trước,\n"
                                "sau đó bấm nút '📂 Chọn Media'.")
            return

        # Lấy row index từ selected
        try:
            row = selected.row
        except AttributeError:
            messagebox.showinfo("Hướng dẫn", "Hãy click vào 1 ô cụ thể trên bảng trước.")
            return

        # Hỏi người dùng chọn file hay thư mục
        choice = messagebox.askyesnocancel(
            "Chọn Media",
            "Bạn muốn chọn:\n\n"
            "  ✅ Yes  → Chọn THƯ MỤC (lấy tất cả ảnh/video trong folder)\n"
            "  ❌ No   → Chọn FILE cụ thể\n"
            "  Cancel  → Hủy"
        )

        if choice is None:
            return
        elif choice:  # Yes = Chọn thư mục
            path = filedialog.askdirectory(title="Chọn thư mục chứa ảnh/video")
        else:  # No = Chọn file
            paths = filedialog.askopenfilenames(
                title="Chọn ảnh/video",
                filetypes=[
                    ("Media files", "*.jpg *.jpeg *.png *.gif *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.webm"),
                    ("All files", "*.*"),
                ]
            )
            if paths:
                path = " | ".join(paths)
            else:
                return

        if path:
            media_col = COL_KEYS.index("media")  # Cột Ảnh/Video
            # Lấy giá trị hiện tại
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
        # Lọc bài chưa DONE
        posts_chua_done = [p for p in posts
                          if p.get('ma_bai', '').strip()
                          and not p.get('status', '').strip().upper().startswith('DONE')]

        if not posts_chua_done:
            messagebox.showinfo("Thông báo", "Không có bài đăng nào cần xử lý.\n"
                                             "(Tất cả đã DONE hoặc chưa nhập Mã bài)")
            return

        confirm = messagebox.askyesno(
            "Xác nhận đăng bài",
            f"Sẽ đăng {len(posts_chua_done)} bài viết.\n\n"
            "Trình duyệt sẽ mở lên, bạn cần:\n"
            "  1. Đăng nhập Facebook (nếu chưa)\n"
            "  2. Bấm 'Đăng' thủ công trên mỗi tab\n\n"
            "Bắt đầu?"
        )

        if not confirm:
            return

        self.dang_chay = True
        self.btn_dang.configure(text="⏳ Đang chạy...", state=tk.DISABLED)
        self._ghi_log("🚀 Bắt đầu tiến trình đăng bài...")

        # Chạy trên thread riêng để GUI không bị đơ
        self._posting_thread = threading.Thread(
            target=self._chay_posting_engine,
            args=(posts_chua_done,),
            daemon=True,
        )
        self._posting_thread.start()

    def _chay_posting_engine(self, posts: list[dict]):
        """Chạy Playwright posting engine trên thread riêng."""
        try:
            import random
            from playwright.sync_api import sync_playwright
            from core.excel_manager import tach_danh_sach, phan_giai_media
            from core.browser_manager import (
                khoi_tao_trinh_duyet, cho_dang_nhap,
                dieu_huong_toi_nhom, mo_hop_thoai_dang_bai,
                tai_file_media, go_caption, dong_trinh_duyet,
            )

            df = posts_to_dataframe(posts)

            with sync_playwright() as p:
                context, page = khoi_tao_trinh_duyet(p)
                self._ghi_log_safe("🌐 Trình duyệt đã mở. Hãy đăng nhập Facebook nếu cần.")

                # Chờ đăng nhập - dùng dialog trong GUI thread
                self.root.after(0, self._hien_thi_cho_dang_nhap)
                # Chờ flag
                self._cho_dang_nhap_flag = threading.Event()
                cho_dang_nhap(page)  # Hàm này sẽ block ở input() trong terminal
                # Thực tế ta sẽ bypass bằng cách chạy logic trực tiếp
                self._ghi_log_safe("▶️ Bắt đầu xử lý bài đăng...")

                for idx, row in df.iterrows():
                    ma_bai = str(row['Ma_Bai_Dang']).strip()
                    caption = str(row['Caption']).strip()
                    if caption.lower() == 'nan':
                        caption = ""

                    links = tach_danh_sach(row['Link_Bai_Dang'])
                    media = phan_giai_media(row['Anh_Video'])

                    self._ghi_log_safe(f"📝 Đang xử lý: {ma_bai} ({len(links)} nhóm)")
                    self._cap_nhat_status_bang(ma_bai, "ĐANG CHẠY...")

                    danh_sach_tab = []
                    so_thanh_cong = 0

                    for stt, url in enumerate(links, start=1):
                        try:
                            tab = context.new_page()
                            tab.on("dialog", lambda d: d.accept())

                            self._ghi_log_safe(f"  🔗 [{ma_bai}] Nhóm {stt}/{len(links)} → {url}")

                            if not dieu_huong_toi_nhom(tab, url):
                                tab.close()
                                continue
                            if not mo_hop_thoai_dang_bai(tab):
                                tab.close()
                                continue
                            if not go_caption(tab, caption):
                                tab.close()
                                continue
                            if not tai_file_media(tab, media):
                                tab.close()
                                continue

                            danh_sach_tab.append(tab)
                            so_thanh_cong += 1
                            self._ghi_log_safe(f"  ✅ Tab {stt} đã sẵn sàng!")

                        except Exception as e:
                            self._ghi_log_safe(f"  ❌ Lỗi tab {stt}: {e}")

                        if stt < len(links):
                            time.sleep(random.randint(3, 7))

                    # Tạm dừng chờ bấm Đăng
                    if danh_sach_tab:
                        self._ghi_log_safe(
                            f"⏸️ Đã chuẩn bị {len(danh_sach_tab)} tab cho [{ma_bai}]. "
                            f"Mời bạn bấm 'Đăng' trên trình duyệt!"
                        )
                        # Hiện dialog chờ trên GUI thread
                        self._cho_bam_dang_event = threading.Event()
                        self.root.after(0, lambda mb=ma_bai, n=len(danh_sach_tab): self._hien_thi_cho_dang(mb, n))
                        self._cho_bam_dang_event.wait()

                        for tab in danh_sach_tab:
                            try:
                                tab.close()
                            except Exception:
                                pass

                    # Cập nhật status
                    ket_qua = f"DONE ({so_thanh_cong}/{len(links)})"
                    cap_nhat_status_json(ma_bai, ket_qua)
                    self._cap_nhat_status_bang(ma_bai, ket_qua)
                    self._ghi_log_safe(f"🏁 [{ma_bai}] → {ket_qua}")

                    if idx < len(df) - 1:
                        self._ghi_log_safe("⏳ Nghỉ 15s trước bài tiếp theo...")
                        time.sleep(15)

                dong_trinh_duyet(context)

            self._ghi_log_safe("🎉 HOÀN THÀNH TẤT CẢ!")

        except Exception as e:
            self._ghi_log_safe(f"❌ LỖI NGHIÊM TRỌNG: {e}")

        finally:
            self.dang_chay = False
            self.root.after(0, lambda: self.btn_dang.configure(
                text="▶️ Bắt đầu đăng", state=tk.NORMAL
            ))

    def _hien_thi_cho_dang_nhap(self):
        """Hiện thông báo chờ đăng nhập (chạy trên GUI thread)."""
        messagebox.showinfo(
            "Đăng nhập Facebook",
            "Trình duyệt đã mở.\n\n"
            "1. Đăng nhập Facebook trên trình duyệt\n"
            "2. Quay lại cửa sổ Terminal và nhấn Enter\n\n"
            "Bấm OK để tiếp tục."
        )

    def _hien_thi_cho_dang(self, ma_bai: str, so_tab: int):
        """Hiện dialog chờ người dùng bấm Đăng trên trình duyệt."""
        messagebox.showinfo(
            f"Bấm Đăng - {ma_bai}",
            f"Đã chuẩn bị xong {so_tab} tab cho [{ma_bai}].\n\n"
            "👉 Hãy chuyển sang trình duyệt, bấm 'Đăng' trên từng tab.\n"
            "👉 Sau khi đăng XONG HẾT, bấm OK ở đây để tiếp tục."
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
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = AutoPostGUI()
    app.chay()
