"""
browser_manager.py - Module chuyên thao tác trên trình duyệt Facebook.

Chức năng chính:
    1. Khởi tạo trình duyệt Chromium với persistent context (lưu phiên đăng nhập).
    2. Xử lý luồng đăng nhập bán tự động (Semi-Auto Login).
    3. Điều hướng vào nhóm, mở hộp thoại đăng bài.
    4. Tải file Media (ảnh + video) lên Facebook.
    5. Gõ Caption với tốc độ ngẫu nhiên mô phỏng người thật.
    6. Xử lý Popup rác (Alert/Dialog, DOM Popup).
    7. Quản lý RAM: Tái sử dụng 1 Tab duy nhất (Single-Tab Reuse).
"""

import time
import random
import os
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
from colorama import Fore, Style


# Đường dẫn tới thư mục lưu phiên đăng nhập (Cookie, LocalStorage)
SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'profiles', 'fb_session_main')


def nghi_ngau_nhien(tu: float, den: float, thong_bao: str = ""):
    """
    Nghỉ (sleep) một khoảng thời gian ngẫu nhiên để mô phỏng hành vi người thật.

    Args:
        tu: Số giây TỐI THIỂU.
        den: Số giây TỐI ĐA.
        thong_bao: Thông báo in ra Terminal (tùy chọn).
    """
    delay = random.uniform(tu, den)
    if thong_bao:
        print(f"{Fore.CYAN}  ⏳ {thong_bao} ({delay:.1f}s)...{Style.RESET_ALL}")
    time.sleep(delay)


def khoi_tao_trinh_duyet(playwright_instance: Playwright) -> tuple[BrowserContext, Page]:
    """
    Khởi tạo trình duyệt Chromium với persistent context.
    Trình duyệt sẽ mở ở chế độ có giao diện (headless=False) để người dùng
    nhìn thấy và thao tác đăng nhập.

    Args:
        playwright_instance: Instance của Playwright đã được khởi tạo.

    Returns:
        Tuple gồm (BrowserContext, Page).
    """
    print(f"{Fore.CYAN}🌐 Đang khởi tạo trình duyệt...{Style.RESET_ALL}")

    # Đảm bảo thư mục session tồn tại
    os.makedirs(SESSION_DIR, exist_ok=True)

    context = playwright_instance.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=False,  # BẮT BUỘC hiển thị giao diện để người dùng đăng nhập
        viewport={'width': 1280, 'height': 800},
        locale='vi-VN',  # Đặt ngôn ngữ tiếng Việt để các nút FB hiển thị đúng
        args=[
            '--disable-blink-features=AutomationControlled',  # Ẩn dấu hiệu tự động hóa
            '--no-sandbox',
        ]
    )

    # Tái sử dụng tab đầu tiên nếu có, hoặc mở tab mới
    if context.pages:
        page = context.pages[0]
    else:
        page = context.new_page()

    # --- Đăng ký Event Listener xử lý Popup/Dialog ---
    # Hễ có dialog trình duyệt hiện ra ("Bạn có muốn rời trang?"), tự động đồng ý
    page.on("dialog", lambda dialog: dialog.accept())

    print(f"{Fore.GREEN}  ✅ Trình duyệt đã sẵn sàng!{Style.RESET_ALL}")
    return context, page


def cho_dang_nhap(page: Page):
    """
    Mở trang Facebook và chờ người dùng đăng nhập thủ công.
    Script sẽ TẠM DỪNG hoàn toàn tại đây cho đến khi người dùng nhấn Enter.
    """
    print(f"\n{Fore.CYAN}📱 Đang mở Facebook...{Style.RESET_ALL}")
    page.goto('https://www.facebook.com/', wait_until='domcontentloaded')
    time.sleep(3)

    print()
    print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  ⏸️  HỆ THỐNG ĐANG TẠM DỪNG!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}")
    print()
    print(f"  👉 Hãy thao tác trên trình duyệt:")
    print(f"     - Nếu đã đăng nhập sẵn: Bạn sẽ thấy Bảng tin (News Feed).")
    print(f"     - Nếu chưa đăng nhập: Hãy nhập Tài khoản, Mật khẩu, 2FA.")
    print()
    input(f"  👉 Sau khi đã vào được Facebook, HÃY NHẤN [ENTER] ĐỂ BẮT ĐẦU: ")
    print()
    print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  ▶️  BẮT ĐẦU TIẾN TRÌNH AUTO POST!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
    print()


def don_dep_popup(page: Page):
    """
    Sau khi tải trang, tự động nhấn phím Escape 1-2 lần để đóng
    mọi popup rác của Facebook (gợi ý tham gia nhóm, thông báo...).
    """
    try:
        page.keyboard.press("Escape")
        time.sleep(0.5)
        page.keyboard.press("Escape")
        time.sleep(0.5)
    except Exception:
        pass  # Không có popup thì bỏ qua, không cần xử lý gì


def dieu_huong_toi_nhom(page: Page, url: str) -> bool:
    """
    Điều hướng trình duyệt tới URL nhóm Facebook.
    Chờ trang tải xong và dọn dẹp popup.

    Args:
        page: Đối tượng Page của Playwright.
        url: URL nhóm/trang Facebook cần truy cập.

    Returns:
        True nếu điều hướng thành công, False nếu có lỗi.
    """
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=45000)
        # Chờ mạng ổn định nhưng không quá khắt khe
        try:
            page.wait_for_load_state('networkidle', timeout=30000)
        except Exception:
            # Nếu hết 30s mà mạng vẫn chưa idle nhưng trang đã hiện thì vẫn tiếp tục
            pass
            
        nghi_ngau_nhien(2, 4, "Đang chờ trang ổn định")
        don_dep_popup(page)
        return True
    except Exception as e:
        print(f"{Fore.RED}  ✗ Lỗi khi truy cập {url}: {e}{Style.RESET_ALL}")
        return False


def mo_hop_thoai_dang_bai(page: Page) -> bool:
    """
    Tìm và click vào ô "Viết nội dung nào đó..." (hoặc "Write something...")
    để mở hộp thoại tạo bài viết mới.

    Thử nhiều selector khác nhau để tương thích với cả giao diện
    tiếng Việt và tiếng Anh của Facebook.

    Returns:
        True nếu mở thành công, False nếu không tìm thấy nút.
    """
    # Danh sách các text có thể xuất hiện trên nút tạo bài viết
    cac_ten_nut = [
        "Viết nội dung nào đó...",
        "Bạn đang nghĩ gì?",
        "Write something...",
        "What's on your mind",
        "Viết nội dung nào đó",
        "Bạn đang nghĩ gì",
        "đang nghĩ gì",
        "nội dung nào đó",
    ]

    for ten_nut in cac_ten_nut:
        try:
            # Thử tìm theo role button
            btn = page.get_by_role("button", name=ten_nut, exact=False)
            if btn.is_visible():
                btn.click()
                nghi_ngau_nhien(2, 3.5, "Đang mở hộp thoại đăng bài")
                return True
        except Exception:
            continue

    # Thử tìm theo aria-label (rất hiệu quả trên Facebook)
    try:
        page.click('[aria-label*="đang nghĩ gì"]', timeout=3000)
        nghi_ngau_nhien(2, 3.5, "Đang mở bằng aria-label")
        return True
    except Exception:
        try:
            page.click('[aria-label*="nội dung nào đó"]', timeout=3000)
            nghi_ngau_nhien(2, 3.5, "Đang mở bằng aria-label")
            return True
        except Exception:
            pass

    # Fallback: Thử click bằng selector CSS nếu tất cả text đều không khớp
    try:
        selector_fallback = '[role="button"][tabindex="0"]'
        elements = page.query_selector_all(selector_fallback)
        for el in elements:
            text = el.inner_text()
            if any(keyword in text.lower() for keyword in ['viết', 'write', 'nghĩ', 'mind']):
                el.click()
                nghi_ngau_nhien(2, 3.5, "Đang mở hộp thoại đăng bài (fallback)")
                return True
    except Exception:
        pass

    print(f"{Fore.RED}  ✗ Không tìm thấy nút tạo bài viết!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}    → Có thể nhóm này không cho phép đăng bài, hoặc giao diện đã thay đổi.{Style.RESET_ALL}")
    return False


def tai_file_media(page: Page, danh_sach_file: list[str]) -> bool:
    if not danh_sach_file:
        return True

    print(f"{Fore.CYAN}  📎 Đang tải lên {len(danh_sach_file)} file media...{Style.RESET_ALL}")

    try:
        # Giới hạn click CHỈ trong hộp thoại "Tạo bài viết"
        dialog = page.locator('div[role="dialog"]').first

        # Tìm và click nút "Ảnh/video" BÊN TRONG dialog
        da_click = False
        cac_selector_media = [
            'div[aria-label*="Ảnh/video"]',
            'div[aria-label*="Photo/video"]',
            'div[aria-label*="Ảnh/Video"]',
            'div[aria-label*="Photo/Video"]',
            'div[aria-label="Ảnh/video"]',
            'div[aria-label="Photo/video"]',
        ]

        for sel in cac_selector_media:
            try:
                icon = dialog.locator(sel).first
                if icon.is_visible(timeout=3000):
                    icon.click(force=True)
                    da_click = True
                    time.sleep(3)
                    break
            except Exception:
                continue

        if not da_click:
            # Thử tìm theo text bên trong dialog có chứa từ khóa
            try:
                # Tìm phần tử có chứa chữ "Ảnh/video" hoặc "Photo/video"
                for kw in ["Ảnh/video", "Photo/video", "Ảnh/Video", "Photo/Video"]:
                    icon = dialog.get_by_text(kw, exact=False).first
                    if icon.is_visible(timeout=2000):
                        icon.click(force=True)
                        da_click = True
                        time.sleep(3)
                        break
            except Exception:
                pass

        if not da_click:
            print(f"{Fore.YELLOW}  ⚠️ Không tìm thấy nút Ảnh/video trong dialog. Thử tìm input file trực tiếp...{Style.RESET_ALL}")

        # Tìm input[type=file] trên TOÀN TRANG (Facebook thường đặt nó ở ngoài dialog)
        # Lấy tất cả input file và chọn cái cuối cùng (thường là cái mới xuất hiện nhất)
        all_file_inputs = page.locator("input[type='file']")
        count = all_file_inputs.count()
        
        if count == 0:
            print(f"{Fore.RED}  ✗ Không tìm thấy ô upload file nào!{Style.RESET_ALL}")
            return False

        # Dùng cái cuối cùng (cái mới nhất, thường là của dialog đăng bài)
        file_input = all_file_inputs.nth(count - 1)
        file_input.set_input_files(danh_sach_file)

        # Chờ Facebook upload
        thoi_gian_cho = max(6, len(danh_sach_file) * 4)
        nghi_ngau_nhien(thoi_gian_cho, thoi_gian_cho + 2, f"Đang chờ FB tải lên {len(danh_sach_file)} file")

        print(f"{Fore.GREEN}  ✅ Tải file media thành công!{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}  ✗ Lỗi khi tải file media: {e}{Style.RESET_ALL}")
        return False


def go_caption(page: Page, noi_dung: str) -> bool:
    if not noi_dung or noi_dung.strip() == '':
        return True

    print(f"{Fore.CYAN}  ✏️ Đang nhập nội dung ({len(noi_dung)} ký tự)...{Style.RESET_ALL}")
    
    try:
        # Bước 1: Click vào giữa hộp thoại để đảm bảo đang focus đúng chỗ
        # Ta click vào chỗ có chữ "Bạn đang nghĩ gì?"
        page.click('div[role="dialog"] div[role="textbox"]', timeout=5000)
        time.sleep(1)

        # Bước 2: Dùng bàn phím mô phỏng gõ phím thật (Keyboard Type)
        # Cách này không cần selector chính xác thẻ div sâu bên trong
        toc_do_go = random.randint(30, 80)
        page.keyboard.type(noi_dung, delay=toc_do_go)
        
        time.sleep(2)
        print(f"{Fore.GREEN}  ✅ Nhập nội dung thành công!{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}  ✗ Lỗi khi gõ Caption: {e}{Style.RESET_ALL}")
        return False


def quay_ve_trang_chu(page: Page):
    """
    Điều hướng về trang chủ Facebook để "reset" lại màn hình.
    Dùng khi gặp lỗi ở 1 nhóm, cần làm sạch UI trước khi chuyển sang nhóm mới.
    """
    try:
        page.goto('https://www.facebook.com/', wait_until='domcontentloaded', timeout=15000)
        time.sleep(2)
        don_dep_popup(page)
    except Exception:
        pass  # Nếu cả trang chủ cũng lỗi thì thôi, vòng lặp sẽ thử lại ở nhóm tiếp theo


def dong_trinh_duyet(context: BrowserContext):
    """
    Đóng trình duyệt và lưu lại toàn bộ Cookie/Session.
    Lần chạy tiếp theo sẽ không cần đăng nhập lại.
    """
    try:
        context.close()
        print(f"\n{Fore.GREEN}🔒 Đã đóng trình duyệt và lưu phiên đăng nhập thành công.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}[CẢNH BÁO] Lỗi khi đóng trình duyệt: {e}{Style.RESET_ALL}")
