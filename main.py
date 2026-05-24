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
    if df is None or len(df) == 0: return

    # 2. Tiền kiểm tra
    hop_le, _ = tien_kiem_tra_toan_bo(df)
    if not hop_le: return

    # Thu thập tất cả các nhiệm vụ đăng bài từ mọi dòng được chọn
    nhiem_vu = []
    for idx, row in df.iterrows():
        ma_bai = str(row['Ma_Bai_Dang']).strip()
        caption = str(row['Caption']).strip()
        if caption.lower() == 'nan': caption = ""
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
                'row_idx': idx
            })

    if not nhiem_vu:
        print(f"{Fore.YELLOW}Không có link nhóm nào để đăng!{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}🚀 Chuẩn bị mở {len(nhiem_vu)} tab chuẩn bị song song cho {len(df)} bài viết...{Style.RESET_ALL}")

    # 3. Khởi tạo trình duyệt
    with sync_playwright() as p:
        context, page = khoi_tao_trinh_duyet(p)
        cho_dang_nhap(page)

        # Mở và chuẩn bị tất cả các tab
        danh_sach_tab = []
        ban_ghi_thanh_cong = {} # ma_bai -> count

        for task_idx, task in enumerate(nhiem_vu, start=1):
            ma_bai = task['ma_bai']
            url = task['url']
            media = task['media']
            caption = task['caption']
            stt = task['stt']
            tong = task['tong']
            
            print(f"\n{Fore.CYAN}➡️ [{task_idx}/{len(nhiem_vu)}] Đang mở tab cho [{ma_bai}] Nhóm {stt}/{tong} -> {url}{Style.RESET_ALL}")
            
            try:
                tab = context.new_page()
                tab.on("dialog", lambda d: d.accept())
                
                # Thực hiện các bước chuẩn bị (Tải ảnh trước, gõ caption sau!)
                success = False
                if dieu_huong_toi_nhom(tab, url):
                    if mo_hop_thoai_dang_bai(tab):
                        if tai_file_media(tab, media):
                            if go_caption(tab, caption):
                                success = True
                                
                if success:
                    danh_sach_tab.append(tab)
                    ban_ghi_thanh_cong[ma_bai] = ban_ghi_thanh_cong.get(ma_bai, 0) + 1
                    print(f"{Fore.GREEN}✅ Đã chuẩn bị xong tab {task_idx}!{Style.RESET_ALL}")
                else:
                    tab.close()
                    print(f"{Fore.RED}❌ Thất bại khi chuẩn bị tab {task_idx}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi tab {task_idx}: {e}{Style.RESET_ALL}")
            
            # Chờ một chút giữa các tab để tự nhiên
            if task_idx < len(nhiem_vu):
                time.sleep(random.randint(2, 4))

        # Tạm dừng chờ người dùng bấm Đăng trên tất cả các tab
        if danh_sach_tab:
            print(f"\n{Fore.YELLOW}⚠️  Đã chuẩn bị xong TẤT CẢ {len(danh_sach_tab)} tab.")
            print(f"{Fore.YELLOW}👉 Mời bạn chuyển sang trình duyệt bấm 'Đăng' thủ công trên từng tab.{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}👉 Sau khi đã đăng xong HẾT tất cả các tab, nhấn [ENTER] tại đây để tiếp tục...{Style.RESET_ALL}")
            
            # Đóng tất cả các tab
            for tab in danh_sach_tab:
                try: tab.close()
                except: pass

        # 4. Cập nhật Status thời gian thực cho tất cả bài đăng
        import datetime
        bay_gio = datetime.datetime.now().strftime("%H:%M (%d/%m)")
        for idx, row in df.iterrows():
            ma_bai = str(row['Ma_Bai_Dang']).strip()
            links = tach_danh_sach(row['Link_Bai_Dang'])
            so_tc = ban_ghi_thanh_cong.get(ma_bai, 0)
            
            ket_qua = f"{bay_gio} ({so_tc}/{len(links)})"
            cap_nhat_status(NGUON_DU_LIEU, ma_bai, ket_qua)
            print(f"{Fore.GREEN}🏁 Đã cập nhật trạng thái cho {ma_bai} -> {ket_qua}{Style.RESET_ALL}")

        dong_trinh_duyet(context)
    print(f"\n{Fore.GREEN}🎉 HOÀN THÀNH TẤT CẢ!{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        auto_post_semi_auto()
    except KeyboardInterrupt:
        print(f"\n⛔ Đã dừng hệ thống.")
        sys.exit(0)
