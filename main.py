"""
main.py - Hệ thống Auto Post Facebook Bán Tự Động v2.5
Hỗ trợ: Google Sheets Online & Excel Local.
"""

import os
import sys
import random
import time
from colorama import init, Fore, Style
from playwright.sync_api import sync_playwright

# Import module nội bộ
from core.excel_manager import (
    doc_du_lieu,
    tach_danh_sach,
    phan_giai_media,
    cap_nhat_status,
    tien_kiem_tra_toan_bo,
)
from core.browser_manager import (
    khoi_tao_trinh_duyet,
    cho_dang_nhap,
    dieu_huong_toi_nhom,
    mo_hop_thoai_dang_bai,
    tai_file_media,
    go_caption,
    dong_trinh_duyet,
)

init(autoreset=True)

# ══════════════════════════════════════════════════════════════════════
# CẤU HÌNH NGUỒN DỮ LIỆU TẠI ĐÂY
# Bạn có thể dán LINK Google Sheet hoặc đường dẫn file Excel local
# ══════════════════════════════════════════════════════════════════════
NGUON_DU_LIEU = "https://docs.google.com/spreadsheets/d/1H4eFxMGWVf3HDNgmzBcdIs8vnNj1vv4wBym5v8fIBno/edit?gid=0#gid=0"
# Ví dụ Google Sheet: NGUON_DU_LIEU = "https://docs.google.com/spreadsheets/d/1A2B3C4D5E6F/edit"
# ══════════════════════════════════════════════════════════════════════

def in_banner():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🚀  HỆ THỐNG AUTO POST FACEBOOK - BÁN TỰ ĐỘNG  🚀    ║
║           Semi-Automation System v2.5 (Cloud)            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

def chuan_bi_bai_tren_tab(page, url, media, caption, ma_bai, stt, tong):
    print(f"\n{Fore.MAGENTA}📌 [{ma_bai}] Nhóm {stt}/{tong} -> {url}{Style.RESET_ALL}")
    if not dieu_huong_toi_nhom(page, url): return False
    if not mo_hop_thoai_dang_bai(page): return False
    if not go_caption(page, caption): return False
    if not tai_file_media(page, media): return False
    print(f"{Fore.GREEN}✅ Đã chuẩn bị xong tab {stt}!{Style.RESET_ALL}")
    return True

def auto_post_semi_auto():
    in_banner()
    
    # 1. Đọc dữ liệu
    df = doc_du_lieu(NGUON_DU_LIEU)
    if df is None: return

    # 2. Tiền kiểm tra
    hop_le, _ = tien_kiem_tra_toan_bo(df)
    if not hop_le: return

    # 3. Khởi tạo trình duyệt
    with sync_playwright() as p:
        context, page = khoi_tao_trinh_duyet(p)
        cho_dang_nhap(page)

        # 4. Vòng lặp bài đăng
        for idx, row in df.iterrows():
            ma_bai = str(row['Ma_Bai_Dang']).strip()
            caption = str(row['Caption']).strip()
            if caption.lower() == 'nan': caption = ""
            
            links = tach_danh_sach(row['Link_Bai_Dang'])
            media = phan_giai_media(row['Anh_Video'])
            
            print(f"\n{Fore.CYAN}📝 Đang xử lý bài: {ma_bai} ({len(links)} nhóm){Style.RESET_ALL}")
            
            danh_sach_tab = []
            so_thanh_cong = 0
            
            for stt, url in enumerate(links, start=1):
                try:
                    tab = context.new_page()
                    tab.on("dialog", lambda d: d.accept())
                    if chuan_bi_bai_tren_tab(tab, url, media, caption, ma_bai, stt, len(links)):
                        danh_sach_tab.append(tab)
                        so_thanh_cong += 1
                    else:
                        tab.close()
                except Exception as e:
                    print(f"{Fore.RED}Lỗi tab {stt}: {e}{Style.RESET_ALL}")
                
                if stt < len(links): time.sleep(random.randint(3, 7))

            # Tạm dừng chờ người dùng bấm Đăng
            if danh_sach_tab:
                print(f"\n{Fore.YELLOW}⚠️  Đã chuẩn bị xong {len(danh_sach_tab)} tab. Mời bạn bấm 'Đăng' thủ công trên trình duyệt.{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}👉 Sau khi đăng xong HẾT, nhấn [ENTER] tại đây để tiếp tục...{Style.RESET_ALL}")
                for tab in danh_sach_tab:
                    try: tab.close()
                    except: pass
            
            # Cập nhật Status
            ket_qua = f"DONE ({so_thanh_cong}/{len(links)})"
            cap_nhat_status(NGUON_DU_LIEU, ma_bai, ket_qua)
            print(f"{Fore.GREEN}🏁 Đã cập nhật trạng thái cho {ma_bai}{Style.RESET_ALL}")

            if idx < len(df) - 1:
                print(f"⏳ Nghỉ 15s trước bài tiếp theo...")
                time.sleep(15)

        dong_trinh_duyet(context)
    print(f"\n{Fore.GREEN}🎉 HOÀN THÀNH TẤT CẢ!{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        auto_post_semi_auto()
    except KeyboardInterrupt:
        print(f"\n⛔ Đã dừng hệ thống.")
        sys.exit(0)
