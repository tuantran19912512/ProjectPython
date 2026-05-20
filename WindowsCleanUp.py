import os
import shutil
import ctypes
import sys
import subprocess

def kiem_tra_quyen_quan_tri():
    """Hàm kiểm tra xem mã có đang chạy dưới quyền Administrator hay không."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def tu_dong_nang_quyen():
    """Hàm tự động bật bảng UAC xin quyền Administrator nếu chưa có."""
    if not kiem_tra_quyen_quan_tri():
        print("Đang yêu cầu quyền Quản trị viên (UAC)...")
        # Lấy đường dẫn tuyệt đối của tệp Python đang chạy
        duong_dan_file = os.path.abspath(sys.argv[0])
        # Gọi lại chính file này với quyền runas (Administrator)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{duong_dan_file}"', None, 1)
        # Thoát tiến trình cũ (không có quyền)
        sys.exit()

# Gọi hàm tự động nâng quyền ngay đầu chương trình
tu_dong_nang_quyen()

# --- BẮT ĐẦU LUỒNG DỌN DẸP CHÍNH ---
print("Đang bắt đầu quá trình dọn dẹp hệ thống toàn diện...\n")

print("[1/4] Đang chạy công cụ dọn dẹp ổ đĩa (Disk Cleanup)...")
subprocess.run(["cleanmgr.exe", "/autoclean"])

print("\n[2/4] Đang dọn dẹp các thư mục tạm và bộ nhớ đệm...")
thu_muc_rac = [
    os.environ.get('TEMP'),
    os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
    os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Prefetch'),
    os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'SoftwareDistribution', 'Download')
]

for thu_muc in thu_muc_rac:
    if thu_muc and os.path.exists(thu_muc):
        print(f" - Đang làm sạch: {thu_muc}")
        for ten_file in os.listdir(thu_muc):
            duong_dan = os.path.join(thu_muc, ten_file)
            try:
                if os.path.isfile(duong_dan) or os.path.islink(duong_dan):
                    os.unlink(duong_dan)
                elif os.path.isdir(duong_dan):
                    shutil.rmtree(duong_dan)
            except Exception:
                pass

print("\n[3/4] Đang làm sạch Thùng rác...")
try:
    ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
except Exception:
    pass

print("\n[4/4] Đang dọn dẹp sâu hệ thống (WinSxS)...")
print("LƯU Ý: Quá trình này có thể mất 10-20 phút, vui lòng không tắt công cụ!")
subprocess.run(["DISM.exe", "/Online", "/Cleanup-Image", "/StartComponentCleanup"])

print("\nQuá trình dọn dẹp toàn diện đã hoàn tất!")
os.system('pause')