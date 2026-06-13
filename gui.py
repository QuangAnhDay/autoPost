"""
gui.py - Giao diện Desktop dạng ô lưới cho AutoPost.

Sử dụng tkinter + tksheet để tạo bảng nhập liệu giống Excel.
Người dùng nhập Caption, Link nhóm FB, đường dẫn ảnh/video trực tiếp trên bảng.
Bấm "Bắt đầu đăng" để trigger Playwright posting engine.
"""

import os
import sys
import asyncio

# Thiết lập UTF-8 cho stdout/stderr trên Windows để tránh lỗi UnicodeEncodeError khi in các ký tự tiếng Việt / Emojis
# Đồng thời cấu hình WindowsProactorEventLoopPolicy để hỗ trợ các tiến trình con (Playwright) trong luồng ngầm
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

import tkinter as tk
from tkinter import ttk, filedialog
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
# WINDOWS GLASSMORPHISM UTILITIES & CUSTOM WIDGETS
# ═══════════════════════════════════════════════════════════════
import ctypes
from ctypes import windll, c_int, byref, Structure, sizeof

class ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", c_int),
        ("AccentFlags", c_int),
        ("GradientColor", c_int),
        ("AnimationId", c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    _fields_ = [
        ("Attribute", c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t)
    ]

def ap_dung_glassmorphism(window, is_dark=True):
    """Áp dụng hiệu ứng Acrylic/Aero Blur phía sau cửa sổ trên Windows."""
    if not sys.platform.startswith("win"):
        return
    try:
        window.update()
        hwnd = window.winfo_id()
        
        accent = ACCENT_POLICY()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        accent.AccentFlags = 2
        # Màu nền ABGR: 0xE6160F0B (90% opacity tối màu) giúp chữ hiển thị rõ nét
        accent.GradientColor = 0xE6160F0B if is_dark else 0xE6FFFFFF
        
        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.cast(byref(accent), ctypes.c_void_p)
        data.SizeOfData = sizeof(accent)
        
        windll.user32.SetWindowCompositionAttribute(hwnd, byref(data))
    except Exception:
        pass


class GlassCard(tk.Canvas):
    """Thẻ chứa giao diện dạng kính mờ (Glassmorphism card) bo góc có viền màu sắc."""
    def __init__(self, parent, bg_color="#101726", border_color="#1e293b", radius=14, **kwargs):
        kwargs["highlightthickness"] = 0
        kwargs["bd"] = 0
        kwargs["bg"] = parent.cget("bg") if hasattr(parent, "cget") else "#0a0e17"
        super().__init__(parent, **kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        r = self.radius
        if w > 10 and h > 10:
            self.create_rounded_rect(2, 2, w-2, h-2, r, fill=self.bg_color, outline=self.border_color, width=1.5)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)


class GlassButton(tk.Button):
    """Nút bấm phẳng hiện đại hỗ trợ hiệu ứng hover và màu sắc gradient/neon."""
    def __init__(self, parent, text, command, bg_color="#1e293b", fg_color="#f8fafc", hover_bg="#334155", active_bg="#0f172a", font=("Segoe UI", 9, "bold"), **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            activebackground=active_bg,
            activeforeground=fg_color,
            font=font,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            **kwargs
        )
        self.bg_color = bg_color
        self.hover_bg = hover_bg
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))

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
        self.root.title("AutoPost Mini")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        # Tính toán tọa độ xuất hiện ở góc trên bên phải màn hình
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_coord = screen_width - 320 - 20
        y_coord = 20
        self.root.geometry(f"320x180+{x_coord}+{y_coord}")

        # Áp dụng theme Sun Valley (Windows 11 style)
        sv_ttk.set_theme("dark")

        self.dang_chay = False  # Flag đang chạy posting engine
        self._posting_thread = None
        self.posts_in_memory = []

        self.editor_win = None
        self.sheet = None
        self.log_text = None

        self._tao_giao_dien_mini()
        self._tai_du_lieu()

    def _tao_giao_dien_mini(self):
        """Tạo giao diện mini dashboard siêu gọn ở góc trên bên phải màn hình."""
        self.root.config(bg="#0a0e17")
        ap_dung_glassmorphism(self.root)

        # Sử dụng GlassCard bao phủ toàn bộ giao diện mini
        self.card = GlassCard(self.root, bg_color="#101726", border_color="#1e293b", radius=14)
        self.card.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Thêm padding thực tế bên trong card
        container = tk.Frame(self.card, bg="#101726")
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        lbl_title = tk.Label(container, text="🚀 AUTOPOST CONTROL PANEL", font=("Segoe UI", 9, "bold"), fg="#8b5cf6", bg="#101726")
        lbl_title.pack(anchor=tk.W, pady=(0, 2))

        self.lbl_status = tk.Label(container, text="Trạng thái: Sẵn sàng", font=("Segoe UI", 9, "bold"), fg="#10b981", bg="#101726")
        self.lbl_status.pack(anchor=tk.W, pady=(0, 6))

        # Log container dạng kính tối màu hơn
        log_bg = tk.Frame(container, bg="#0b0f19", padx=8, pady=6)
        log_bg.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.lbl_mini_log = tk.Label(log_bg, text="Sẵn sàng thực hiện nhiệm vụ...", font=("Consolas", 8), fg="#94a3b8", bg="#0b0f19", wraplength=260, justify=tk.LEFT)
        self.lbl_mini_log.pack(anchor=tk.W, fill=tk.X)

        btn_frame = tk.Frame(container, bg="#101726")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Nút Đăng neon tím
        self.btn_dang = GlassButton(btn_frame, text="▶️ Bắt đầu đăng", command=self._bat_dau_dang, bg_color="#8b5cf6", hover_bg="#a855f7", active_bg="#7c3aed")
        self.btn_dang.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        # Nút Quản lý xám kính
        btn_quan_ly = GlassButton(btn_frame, text="⚙️ Quản lý bài đăng", command=self._mo_giao_dien_quan_ly, bg_color="#1e293b", hover_bg="#334155", active_bg="#0f172a")
        btn_quan_ly.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

    def _show_custom_dialog(self, title, message, type_dialog="info"):
        """
        Hiển thị hộp thoại tùy chỉnh của riêng ứng dụng.
        Tự động định vị ở trên cùng và thẳng đứng ngay bên dưới cửa sổ tool chính (góc trên bên phải).
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        dialog.config(bg="#0a0e17")
        ap_dung_glassmorphism(dialog)
        dialog.transient(self.root)
        dialog.grab_set()

        # Lấy vị trí hiện tại của tool
        tool_x = self.root.winfo_x()
        tool_y = self.root.winfo_y()
        tool_w = self.root.winfo_width()
        tool_h = self.root.winfo_height()

        dlg_w = 400
        # Nâng chiều cao lên 380 để không bao giờ bị tràn chữ che mất nút
        dlg_h = 380

        # Căn lề phải của dialog trùng với lề phải của tool
        x = tool_x + tool_w - dlg_w
        # Đặt ngay bên dưới tool
        y = tool_y + tool_h + 15

        # Đảm bảo không trôi khỏi màn hình
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()

        if x < 0:
            x = 10
        if x + dlg_w > screen_w:
            x = screen_w - dlg_w - 10
        if y + dlg_h > screen_h - 50:
            y = tool_y - dlg_h - 15
        if y < 0:
            y = 10

        dialog.geometry(f"{dlg_w}x{dlg_h}+{x}+{y}")

        # Glassmorphism Card
        card = GlassCard(dialog, bg_color="#101726", border_color="#1e293b", radius=14)
        card.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        container = tk.Frame(card, bg="#101726")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 1. Pack Title
        lbl_title = tk.Label(container, text=title, font=("Segoe UI", 11, "bold"), fg="#8b5cf6", bg="#101726")
        lbl_title.pack(anchor=tk.W, pady=(0, 10))

        # 2. Pack Button Frame ở BOTTOM trước để cố định vị trí dưới cùng
        btn_frame = tk.Frame(container, bg="#101726")
        btn_frame.pack(side=tk.BOTTOM, anchor=tk.E, pady=(10, 0))

        # 3. Pack Message container điền vào phần giữa còn lại
        msg_bg = tk.Frame(container, bg="#0b0f19", padx=10, pady=8)
        msg_bg.pack(fill=tk.BOTH, expand=True)

        lbl_msg = tk.Label(msg_bg, text=message, wraplength=330, justify=tk.LEFT, font=("Segoe UI", 9), fg="#e2e8f0", bg="#0b0f19")
        lbl_msg.pack(anchor=tk.W, fill=tk.BOTH, expand=True)

        result = {"value": False}

        def on_ok():
            result["value"] = True
            dialog.destroy()

        def on_cancel():
            result["value"] = False
            dialog.destroy()

        if type_dialog == "confirm":
            btn_yes = GlassButton(btn_frame, text="Đồng ý", command=on_ok, bg_color="#8b5cf6", hover_bg="#a855f7", active_bg="#7c3aed")
            btn_yes.pack(side=tk.LEFT, padx=(0, 10))
            btn_no = GlassButton(btn_frame, text="Hủy bỏ", command=on_cancel, bg_color="#1e293b", hover_bg="#334155", active_bg="#0f172a")
            btn_no.pack(side=tk.LEFT)
        else:
            btn_ok = GlassButton(btn_frame, text="OK", command=on_ok, bg_color="#8b5cf6", hover_bg="#a855f7", active_bg="#7c3aed")
            btn_ok.pack(side=tk.LEFT)

        self.root.wait_window(dialog)
        return result["value"]

    def _mo_giao_dien_quan_ly(self):
        """Mở cửa sổ lớn để quản lý, chỉnh sửa danh sách bài đăng."""
        if self.editor_win is not None and self.editor_win.winfo_exists():
            self.editor_win.focus_force()
            return

        self.editor_win = tk.Toplevel(self.root)
        self.editor_win.title(WINDOW_TITLE)
        self.editor_win.geometry(WINDOW_SIZE)
        self.editor_win.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.editor_win.config(bg="#0a0e17")
        ap_dung_glassmorphism(self.editor_win)

        # Cấu hình đóng cửa sổ: lưu dữ liệu
        self.editor_win.protocol("WM_DELETE_WINDOW", self._dong_editor)

        # Tạo thanh công cụ trên cửa sổ lớn
        toolbar = tk.Frame(self.editor_win, bg="#0a0e17", padx=12, pady=8)
        toolbar.pack(fill=tk.X)

        left_frame = tk.Frame(toolbar, bg="#0a0e17")
        left_frame.pack(side=tk.LEFT)

        # Sử dụng các GlassButton với màu sắc đồng điệu của SaaS Dashboard
        GlassButton(left_frame, text="➕ Thêm dòng", command=self._them_dong, bg_color="#8b5cf6", hover_bg="#a855f7", active_bg="#7c3aed").pack(side=tk.LEFT, padx=(0, 6))
        GlassButton(left_frame, text="🗑️ Xóa dòng", command=self._xoa_dong, bg_color="#ef4444", hover_bg="#f87171", active_bg="#dc2626").pack(side=tk.LEFT, padx=(0, 6))

        # Một khoảng trống nhẹ phân cách thay cho Separator cổ điển
        tk.Frame(left_frame, width=15, bg="#0a0e17").pack(side=tk.LEFT)

        GlassButton(left_frame, text="📂 Chọn Media", command=self._chon_media, bg_color="#3b82f6", hover_bg="#60a5fa", active_bg="#2563eb").pack(side=tk.LEFT, padx=(0, 6))
        GlassButton(left_frame, text="💾 Lưu", command=self._luu_du_lieu, bg_color="#10b981", hover_bg="#34d399", active_bg="#059669").pack(side=tk.LEFT, padx=(0, 6))

        # --- Spreadsheet (bảng lưới) ---
        # Gói bảng lưới bên trong một GlassCard bo góc tuyệt đẹp
        sheet_card = GlassCard(self.editor_win, bg_color="#101726", border_color="#1e293b", radius=14)
        sheet_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        sheet_container = tk.Frame(sheet_card, bg="#101726")
        sheet_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sheet = tksheet.Sheet(
            sheet_container,
            headers=COLUMNS,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            height=350,
        )
        self.sheet.pack(fill=tk.BOTH, expand=True)

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

        self.sheet.column_width(column=0, width=120)
        self.sheet.column_width(column=1, width=280)
        self.sheet.column_width(column=2, width=300)
        self.sheet.column_width(column=3, width=220)
        self.sheet.column_width(column=4, width=140)
        self.sheet.column_width(column=5, width=60)

        self.sheet.readonly_columns(columns=[4])
        self.sheet.extra_bindings("begin_edit_cell", self._begin_edit_cell)
        self.sheet.extra_bindings("double_click_left_click", self._double_click_sheet)

        # Thay đổi giao diện tksheet đồng bộ với màu kính
        self.sheet.change_theme("dark blue")
        try:
            self.sheet.config(
                background="#101726",
                face_background="#101726",
                grid_color="#1e293b",
                header_background="#1e294b",
                header_foreground="#f8fafc",
                header_grid_color="#1e293b",
                selected_cells_background="#8b5cf6",
                selected_cells_foreground="#ffffff",
                selected_rows_background="#8b5cf6",
                selected_rows_foreground="#ffffff",
                outline_color="#1e293b",
                index_background="#101726",
                index_foreground="#94a3b8",
                index_grid_color="#1e293b"
            )
        except:
            pass

        # --- Log Panel ---
        log_card = GlassCard(self.editor_win, bg_color="#101726", border_color="#1e293b", radius=14)
        log_card.pack(fill=tk.X, padx=10, pady=(5, 10))

        log_container = tk.Frame(log_card, bg="#101726")
        log_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        lbl_log_title = tk.Label(log_container, text="📋 HỆ THỐNG LOG HOẠT ĐỘNG", font=("Segoe UI", 9, "bold"), fg="#8b5cf6", bg="#101726")
        lbl_log_title.pack(anchor=tk.W, pady=(0, 4))

        text_frame = tk.Frame(log_container, bg="#101726")
        text_frame.pack(fill=tk.X, expand=True)

        self.log_text = tk.Text(text_frame, height=8, wrap=tk.WORD,
                                bg="#0b0f19", fg="#e2e8f0",
                                font=("Consolas", 10),
                                insertbackground="#ffffff",
                                selectbackground="#8b5cf6",
                                relief=tk.FLAT, padx=8, pady=5)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.configure(state=tk.DISABLED)

        # Nạp dữ liệu hiện tại từ bộ nhớ
        self._hien_thi_du_lieu_tu_bo_nho()

    def _hien_thi_du_lieu_tu_bo_nho(self):
        if self.sheet is not None:
            data = []
            for p in self.posts_in_memory:
                row = [p.get(k, "") for k in COL_KEYS]
                data.append(row)
            self.sheet.set_sheet_data(data)
            self.sheet.refresh()

    def _dong_editor(self):
        # Lưu dữ liệu từ bảng editor về bộ nhớ trước khi đóng
        self._luu_du_lieu()
        self.sheet = None
        self.log_text = None
        if self.editor_win is not None:
            self.editor_win.destroy()
            self.editor_win = None

    def _begin_edit_cell(self, event = None):
        """Chặn người dùng sửa thủ công cột Chọn (cột 5)."""
        try:
            col = None
            if event is not None:
                if hasattr(event, "column"):
                    col = event.column
                elif isinstance(event, dict) and "column" in event:
                    col = event["column"]
                elif isinstance(event, (list, tuple)) and len(event) >= 2:
                    col = event[1]
            
            if col == 5:  # Cột Chọn (0-indexed)
                return False
        except:
            pass
        return True

    def _double_click_sheet(self, event = None):
        """Khi người dùng double click vào cột Chọn, tự động toggle trạng thái giữa ✅ và trống."""
        try:
            row, col = None, None
            if event is not None:
                if hasattr(event, "row") and hasattr(event, "column"):
                    row, col = event.row, event.column
                elif isinstance(event, dict) and "row" in event and "column" in event:
                    row, col = event["row"], event["column"]
                elif isinstance(event, (list, tuple)) and len(event) >= 2:
                    row, col = event[0], event[1]

            if row is None or col is None:
                selected = self.sheet.get_currently_selected()
                if selected is not None:
                    if isinstance(selected, (list, tuple)):
                        row, col = selected[0], selected[1]
                    else:
                        row, col = selected.row, selected.column

            if row is not None and col == 5:  # Cột Chọn (0-indexed)
                val = self.sheet.get_cell_data(row, col)
                current = "" if val is None else str(val).strip()
                new_val = "" if current in ("✅", "None", "nan") else "✅"
                self.sheet.set_cell_data(row, col, new_val)
                self.sheet.refresh()
        except Exception as e:
            self._ghi_log(f"Lỗi nhấp đúp ô: {e}")

    def _tai_du_lieu(self):
        """Tải dữ liệu từ file JSON vào bộ nhớ."""
        posts = doc_posts()
        if not posts:
            posts = [tao_bai_moi() for _ in range(3)]
        self.posts_in_memory = posts
        self._ghi_log("✅ Đã tải dữ liệu thành công.")

    def _lay_du_lieu_tu_bang(self) -> list[dict]:
        """Đọc dữ liệu từ bảng lưới (nếu đang mở) hoặc trả về bộ nhớ đệm."""
        if self.sheet is None:
            return self.posts_in_memory

        try:
            data = self.sheet.get_sheet_data()
            posts = []
            for row in data:
                if all(str(cell).strip() == "" for cell in row):
                    continue
                post = {}
                for i, key in enumerate(COL_KEYS):
                    post[key] = str(row[i]).strip() if i < len(row) else ""
                posts.append(post)
            self.posts_in_memory = posts
            return posts
        except Exception:
            return self.posts_in_memory

    def _luu_du_lieu(self):
        """Lưu dữ liệu từ bộ nhớ vào file JSON."""
        posts = self._lay_du_lieu_tu_bang()
        ghi_posts(posts)
        self._ghi_log(f"💾 Đã lưu {len(posts)} bài đăng.")

    # ═══════════════════════════════════════════════════════════
    # TOOLBAR ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _them_dong(self):
        """Thêm một dòng trống vào cuối bảng sử dụng thao tác mảng (Độc lập phiên bản)."""
        if self.sheet is None:
            return
        try:
            data = self.sheet.get_sheet_data()
            new_row = ["", "", "", "", "", "✅"]
            data.append(new_row)
            self.sheet.set_sheet_data(data)
            self.sheet.refresh()
            self._ghi_log("➕ Đã thêm 1 dòng trống mới.")
        except Exception as e:
            self._show_custom_dialog("Lỗi", f"Không thể thêm dòng: {e}")

    def _xoa_dong(self):
        """Xóa các dòng đang được chọn sử dụng thao tác mảng (Độc lập phiên bản)."""
        if self.sheet is None:
            return
        try:
            selected = self.sheet.get_selected_rows()
            if not selected:
                self._show_custom_dialog("Chưa chọn dòng", "Hãy chọn ít nhất 1 dòng để xóa.")
                return

            if self._show_custom_dialog("Xác nhận xóa", f"Bạn có chắc muốn xóa {len(selected)} dòng?", "confirm"):
                data = self.sheet.get_sheet_data()
                # Xóa từ dưới lên để tránh lệch index
                for row_idx in sorted(selected, reverse=True):
                    if row_idx < len(data):
                        data.pop(row_idx)
                self.sheet.set_sheet_data(data)
                self.sheet.refresh()
                self._ghi_log(f"🗑️ Đã xóa {len(selected)} dòng.")
        except Exception as e:
            self._show_custom_dialog("Lỗi", f"Không thể xóa dòng: {e}")

    def _chon_media(self):
        """Mở hộp thoại thiết kế mới tùy chỉnh 3 nút bằng tiếng Việt thay thế cho askyesnocancel."""
        if self.sheet is None:
            return
        selected = self.sheet.get_currently_selected()
        if selected is None:
            self._show_custom_dialog("Hướng dẫn",
                                "Hãy click vào ô 'Ảnh/Video' của dòng cần chọn media trước,\n"
                                "sau đó bấm nút '📂 Chọn Media'.")
            return

        try:
            row = selected.row
        except AttributeError:
            self._show_custom_dialog("Hướng dẫn", "Hãy click vào 1 ô cụ thể trên bảng trước.")
            return

        # Tạo Custom TopLevel window để hiển thị 3 nút chuẩn Việt
        dialog = tk.Toplevel(self.root)
        dialog.title("Chọn nguồn tải Media")
        dialog.geometry("380x180")
        dialog.resizable(False, False)
        dialog.config(bg="#0a0e17")
        ap_dung_glassmorphism(dialog)
        dialog.transient(self.root)
        dialog.grab_set()

        # Căn giữa màn hình so với cửa sổ chính
        x = self.root.winfo_x() + (self.root.winfo_width() - 380) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        # Glassmorphism Card
        card = GlassCard(dialog, bg_color="#101726", border_color="#1e293b", radius=14)
        card.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        container = tk.Frame(card, bg="#101726")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        lbl = tk.Label(container, text="Bạn muốn tải lên tệp tin hay thư mục media?", font=("Segoe UI", 10, "bold"), fg="#8b5cf6", bg="#101726")
        lbl.pack(pady=(0, 20))

        btn_frame = tk.Frame(container, bg="#101726")
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

        btn_folder = GlassButton(btn_frame, text="📁 Thư mục", command=chon_thu_muc, bg_color="#8b5cf6", hover_bg="#a855f7", active_bg="#7c3aed")
        btn_folder.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_file = GlassButton(btn_frame, text="🖼️ Ảnh/Video", command=chon_file, bg_color="#3b82f6", hover_bg="#60a5fa", active_bg="#2563eb")
        btn_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        btn_close = GlassButton(btn_frame, text="❌ Hủy", command=huy_bo, bg_color="#1e293b", hover_bg="#334155", active_bg="#0f172a")
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
            self._show_custom_dialog("Đang chạy", "Tiến trình đăng bài đang chạy. Vui lòng đợi hoàn tất.")
            return

        # Lưu dữ liệu trước
        self._luu_du_lieu()

        posts = self._lay_du_lieu_tu_bang()
        # Lọc các bài viết được tích chọn (dòng nào cột Chọn KHÔNG RỖNG thì đăng)
        posts_duoc_chon = [p for p in posts
                           if p.get('ma_bai', '').strip()
                           and p.get('chon', '').strip() != '']

        if not posts_duoc_chon:
            self._show_custom_dialog("Thông báo", "Không có bài đăng nào được chọn để đăng.\n"
                                             "Vui lòng điền ký tự bất kỳ hoặc tích chọn (✅) vào cột 'Chọn' của dòng cần đăng.")
            return

        # Gom toàn bộ link nhóm để tính tổng số cửa sổ
        tong_so_cua_so = 0
        from core.excel_manager import tach_danh_sach
        for p in posts_duoc_chon:
            links = tach_danh_sach(p.get('links', ''))
            tong_so_cua_so += len(links)

        confirm = self._show_custom_dialog(
            "Xác nhận đăng bài hàng loạt",
            f"Hệ thống sẽ chuẩn bị SONG SONG {tong_so_cua_so} cửa sổ trình duyệt cho {len(posts_duoc_chon)} bài viết được chọn.\n\n"
            f"Quy trình thực hiện:\n"
            f"  1. Trình duyệt chính mở lên: Bạn đăng nhập Facebook (nếu cần) rồi click [OK] để lưu phiên đăng nhập.\n"
            f"  2. Hệ thống nhân bản profile và mở song song {tong_so_cua_so} cửa sổ chuẩn bị toàn bộ các bài viết cùng lúc.\n"
            f"  3. Bạn đi một vòng bấm 'Đăng' trên từng cửa sổ.\n"
            f"  4. Click [OK] trên GUI để hoàn tất và tự động dọn dẹp các cửa sổ.\n\n"
            f"Bắt đầu?",
            "confirm"
        )

        if not confirm:
            return

        self.dang_chay = True
        self.btn_dang.configure(text="⏳ Đang chạy...", state=tk.DISABLED)
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

            # Xóa file lock của Chromium nếu có để tránh lỗi mở trình duyệt chính
            if os.path.exists(SESSION_DIR):
                for file_name in ("SingletonLock", "lockfile"):
                    lock_file = os.path.join(SESSION_DIR, file_name)
                    if os.path.exists(lock_file):
                        try:
                            os.remove(lock_file)
                        except Exception:
                            pass

            # BƯỚC 1: Mở trình duyệt chính một lần duy nhất để người dùng đăng nhập/kiểm tra phiên đăng nhập
            self._ghi_log_safe("🌐 Đang mở trình duyệt chính để xác nhận đăng nhập Facebook...")
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=SESSION_DIR,
                    headless=False,
                    no_viewport=True,
                    channel="chrome",  # Sử dụng Chrome thật trên máy để tránh bot detection
                    ignore_default_args=["--enable-automation"],
                    locale='vi-VN',
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--start-maximized',
                        '--disable-infobars',
                    ]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.on("dialog", lambda d: self._safe_dialog_accept(d))
                
                self._ghi_log_safe("📱 Đang chuyển hướng tới Facebook...")
                page.goto('https://www.facebook.com/', wait_until='domcontentloaded')
                time.sleep(3)

                # Chờ người dùng đăng nhập bằng dialog trên GUI
                self._cho_dang_nhap_event = threading.Event()
                self.root.after(0, self._hien_thi_cho_dang_nhap_dialog)
                self._cho_dang_nhap_event.wait()

                # Đóng trình duyệt chính để lưu session sạch
                try:
                    context.close()
                except Exception:
                    pass
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

        try:
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
                    for file_name in ("SingletonLock", "lockfile"):
                        lock_file = os.path.join(temp_session, file_name)
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
                        no_viewport=True,
                        channel="chrome",  # Sử dụng Chrome thật để tránh bot detection
                        ignore_default_args=["--enable-automation"],
                        locale='vi-VN',
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--no-sandbox',
                            '--start-maximized',
                            '--disable-infobars',
                        ]
                    )
                    page = context.pages[0] if context.pages else context.new_page()
                    page.on("dialog", lambda d: self._safe_dialog_accept(d))

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
                    try:
                        context.close()
                    except Exception:
                        pass

            except Exception as e:
                self._ghi_log_safe(f"❌ Lỗi khởi động trình duyệt ở cửa sổ {task_idx} ([{ma_bai}]): {e}")
        finally:
            # Bảo đảm 100% luồng chính không bị treo chờ đợi bất kể tình huống lỗi nào xảy ra
            task['event_chuan_bi_xong'].set()

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
        self._show_custom_dialog(
            "Xác thực Facebook",
            "Trình duyệt đã được mở tới trang Facebook.\n\n"
            "1. Hãy đăng nhập tài khoản Facebook của bạn (nếu cần).\n"
            "2. Sau khi đã vào được trang chủ (Bảng tin) Facebook thành công,\n"
            "   hãy bấm [OK] dưới đây để hệ thống bắt đầu tự động chuẩn bị các tab đăng bài!"
        )
        self._cho_dang_nhap_event.set()

    def _hien_thi_cho_dang_dialog(self, count: int):
        """Hiện thông báo chờ người dùng bấm Đăng trên tất cả các tab."""
        self._show_custom_dialog(
            "Xác nhận đã Đăng bài",
            f"Đã chuẩn bị xong {count} cửa sổ trình duyệt song song cho các bài viết được chọn.\n\n"
            "👉 Hãy chuyển qua các cửa sổ trình duyệt, kiểm tra và bấm nút 'Đăng' trên từng cửa sổ.\n"
            "👉 Sau khi đã bấm Đăng XONG HẾT, click nút [OK] ở đây để hoàn tất và đóng toàn bộ."
        )
        self._cho_bam_dang_event.set()

    # ═══════════════════════════════════════════════════════════
    # TIỆN ÍCH
    # ═══════════════════════════════════════════════════════════

    def _ghi_log(self, message: str):
        """Ghi log vào terminal, nhãn mini và panel log lớn (nếu mở)."""
        print(message)
        
        # Cập nhật nhãn mini trên GUI chính
        clean_msg = message
        for prefix in ["✅", "❌", "⚠️", "🚀", "💾", "➕", "🗑️", "📂", "🔔", "🧹", "🏁", "🎉", "⏳", "➡️", "🌐", "🔒", "📱"]:
            clean_msg = clean_msg.replace(prefix, "").strip()
        
        try:
            self.lbl_mini_log.configure(text=clean_msg)
        except Exception:
            pass

        # Cập nhật log panel trên editor lớn nếu đang mở
        if self.log_text is not None:
            try:
                timestamp = time.strftime("%H:%M:%S")
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, f"[{timestamp}]  {message}\n")
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
            except Exception:
                pass

    def _ghi_log_safe(self, message: str):
        """Ghi log thread-safe (gọi từ thread khác GUI)."""
        self.root.after(0, lambda: self._ghi_log(message))

    def _cap_nhat_status_bang(self, ma_bai: str, status: str):
        """Cập nhật trạng thái trên bảng lưới (nếu mở) và trong bộ nhớ."""
        # Cập nhật trong bộ nhớ trước
        for p in self.posts_in_memory:
            if p.get("ma_bai", "").strip() == ma_bai.strip():
                p["status"] = status
                break
        
        # Cập nhật status label ở mini dashboard
        try:
            self.lbl_status.configure(text=f"Trạng thái: {status}")
        except Exception:
            pass

        # Cập nhật sheet nếu đang mở
        if self.sheet is not None:
            def _update():
                try:
                    if self.sheet is None:
                        return
                    data = self.sheet.get_sheet_data()
                    ma_col = COL_KEYS.index("ma_bai")
                    status_col = COL_KEYS.index("status")
                    for row_idx, row in enumerate(data):
                        if str(row[ma_col]).strip() == ma_bai.strip():
                            self.sheet.set_cell_data(row_idx, status_col, status)
                            break
                    self.sheet.refresh()
                except Exception:
                    pass
            self.root.after(0, _update)

    def chay(self):
        """Khởi chạy vòng lặp chính của GUI."""
        # Xử lý đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self._dong_ung_dung)
        self.root.mainloop()

    def _dong_ung_dung(self):
        """Xử lý khi đóng cửa sổ."""
        if self.dang_chay:
            if not self._show_custom_dialog("Đang chạy", "Tiến trình đăng bài đang chạy.\nBạn có chắc muốn thoát?", "confirm"):
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
