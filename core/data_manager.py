"""
data_manager.py - Module quản lý dữ liệu bài đăng bằng file JSON.

Thay thế Google Sheets / Excel cho giao diện GUI desktop.
Cung cấp các hàm đọc/ghi dữ liệu tương thích với cấu trúc DataFrame
hiện có của excel_manager.py.
"""

import os
import json
import pandas as pd
from datetime import datetime

# Đường dẫn mặc định tới file dữ liệu
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DEFAULT_JSON_PATH = os.path.join(DATA_DIR, 'posts.json')


def _dam_bao_thu_muc():
    """Tạo thư mục data/ nếu chưa tồn tại."""
    os.makedirs(DATA_DIR, exist_ok=True)


def tao_bai_moi() -> dict:
    """Trả về dict bài đăng trống với các trường mặc định."""
    return {
        "ma_bai": "",
        "links": "",
        "caption": "",
        "media": "",
        "status": "",
    }


def doc_posts(duong_dan: str = None) -> list[dict]:
    """
    Đọc danh sách bài đăng từ file JSON.

    Args:
        duong_dan: Đường dẫn tới file JSON. Mặc định: data/posts.json

    Returns:
        List các dict bài đăng. Trả về list rỗng nếu file chưa tồn tại.
    """
    path = duong_dan or DEFAULT_JSON_PATH
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Đảm bảo mỗi bài có đầy đủ trường
        template = tao_bai_moi()
        for item in data:
            for key in template:
                if key not in item:
                    item[key] = template[key]
        return data
    except (json.JSONDecodeError, Exception) as e:
        print(f"[LỖI] Không thể đọc file {path}: {e}")
        return []


def ghi_posts(posts: list[dict], duong_dan: str = None):
    """
    Ghi danh sách bài đăng vào file JSON.

    Args:
        posts: List các dict bài đăng.
        duong_dan: Đường dẫn file JSON. Mặc định: data/posts.json
    """
    _dam_bao_thu_muc()
    path = duong_dan or DEFAULT_JSON_PATH
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def posts_to_dataframe(posts: list[dict]) -> pd.DataFrame:
    """
    Chuyển đổi list bài đăng sang DataFrame tương thích với excel_manager.

    Mapping:
        ma_bai  -> Ma_Bai_Dang
        links   -> Link_Bai_Dang
        caption -> Caption
        media   -> Anh_Video
        status  -> Status
    """
    if not posts:
        return pd.DataFrame(columns=['Ma_Bai_Dang', 'Link_Bai_Dang', 'Caption', 'Anh_Video', 'Status'])

    rows = []
    for p in posts:
        rows.append({
            'Ma_Bai_Dang': p.get('ma_bai', ''),
            'Link_Bai_Dang': p.get('links', ''),
            'Caption': p.get('caption', ''),
            'Anh_Video': p.get('media', ''),
            'Status': p.get('status', ''),
        })
    return pd.DataFrame(rows)


def cap_nhat_status_json(ma_bai: str, gia_tri: str, duong_dan: str = None):
    """
    Cập nhật Status cho một bài đăng theo mã bài.

    Args:
        ma_bai: Mã bài đăng cần cập nhật.
        gia_tri: Giá trị Status mới (VD: 'DONE (2/3)').
        duong_dan: Đường dẫn file JSON.
    """
    posts = doc_posts(duong_dan)
    for p in posts:
        if p.get('ma_bai', '').strip() == ma_bai.strip():
            p['status'] = gia_tri
            break
    ghi_posts(posts, duong_dan)
