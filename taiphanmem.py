import sys
import os
import ctypes
import subprocess
import csv
import time
import hashlib
import concurrent.futures
import base64
import re
import urllib.parse
import shutil
from pathlib import Path
import requests
import psutil

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QScrollArea, 
                             QCheckBox, QProgressBar, QFrame, QPlainTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap

# ==============================================================================
# CẤU HÌNH TOÀN CỤC & THƯ MỤC
# ==============================================================================
URL_CSV = "https://raw.githubusercontent.com/tuantran19912512/Windows-tool-box/refs/heads/main/DanhSachPhanMem.csv"
THU_MUC_LUU_TRU = Path(os.environ.get('PUBLIC', 'C:\\Users\\Public')) / "LuuTruPhanMemViet"
THU_MUC_TEMP = Path("C:\\VietToolbox_Temp")
THU_MUC_ICON = THU_MUC_TEMP / "Icons"

THU_MUC_LUU_TRU.mkdir(parents=True, exist_ok=True)
THU_MUC_TEMP.mkdir(parents=True, exist_ok=True)
THU_MUC_ICON.mkdir(parents=True, exist_ok=True)

DANH_SACH_KHOA_API = [
    base64.b64decode("QUl6YVN5Q3VKUkJaTDZnUU8tdVZOMWVvdHhmMlppTXNtYy1sandR").decode('utf-8'),
    base64.b64decode("QUl6YVN5QlRhVmRQdmlLaUJyR0JUVk0tUlRiVW51QUdFUzRWck1v").decode('utf-8'),
    base64.b64decode("QUl6YVN5QkI0NENOamtHRkdQSjhBaVZaMURxZFJnc3M5MDc4QThv").decode('utf-8'),
    base64.b64decode("QUl6YVN5Q2IzaE1LUVNOamt2bFNKbUlhTGtYcVNybFpWaFNSTThR").decode('utf-8'),
    base64.b64decode("QUl6YVN5Q2V0SVlWVzRsQmlULTd3TzdNQUJoWlNVQ0dKR1puQTM0").decode('utf-8')
]

# ==============================================================================
# HÀM XỬ LÝ CẤP THẤP: QUYỀN ADMIN & DIỆT CỬA SỔ
# ==============================================================================
def kiem_tra_quyen_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not kiem_tra_quyen_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def lay_danh_sach_explorer():
    hwnds = []
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetClassName = ctypes.windll.user32.GetClassNameW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            buff = ctypes.create_unicode_buffer(256)
            GetClassName(hwnd, buff, 256)
            if buff.value in ["CabinetWClass", "ExploreWClass"]:
                hwnds.append(hwnd)
        return True
    EnumWindows(EnumWindowsProc(foreach_window), 0)
    return hwnds

def dong_cua_so(hwnd):
    ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)

# ==============================================================================
# LỚP DỮ LIỆU & GIAO DIỆN PHỤ
# ==============================================================================
class PhanMem:
    def __init__(self, ten, url_tai, tham_so, danh_muc, icon_url, mac_dinh_chon):
        self.ten = ten
        self.url_tai = url_tai
        self.tham_so = tham_so
        self.danh_muc = danh_muc
        self.icon_url = icon_url
        self.chon = mac_dinh_chon
        self.trang_thai = "Sẵn sàng"
        self.tien_trinh = 0
        self.ket_qua = ""

class CardPhanMem(QFrame):
    def __init__(self, pm, fn_click):
        super().__init__()
        self.pm = pm
        self.fn_click = fn_click
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            CardPhanMem { background-color: #1E293B; border: 1px solid #334155; border-radius: 8px; margin-bottom: 2px; } 
            CardPhanMem:hover { border: 1px solid #475569; background-color: #334155; }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.fn_click(self.pm)

# ==============================================================================
# LUỒNG XỬ LÝ NGẦM
# ==============================================================================
class LuongTaiIcon(QThread):
    icon_da_tai = pyqtSignal(object, bytes)

    def __init__(self, danh_sach_pm):
        super().__init__()
        self.danh_sach = danh_sach_pm

    def tai_mot_icon(self, pm):
        if not pm.icon_url: return
        ten_file = hashlib.md5(pm.icon_url.encode('utf-8')).hexdigest() + ".png"
        duong_dan_cache = THU_MUC_ICON / ten_file
        
        if duong_dan_cache.exists():
            try:
                with open(duong_dan_cache, 'rb') as f: self.icon_da_tai.emit(pm, f.read())
                return
            except: pass

        try:
            response = requests.get(pm.icon_url, timeout=5)
            if response.status_code == 200:
                with open(duong_dan_cache, 'wb') as f: f.write(response.content)
                self.icon_da_tai.emit(pm, response.content)
        except: pass

    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(self.tai_mot_icon, self.danh_sach)

class LuongCaiDat(QThread):
    cap_nhat_giao_dien = pyqtSignal(PhanMem, str, int)
    hoan_thanh_toan_bo = pyqtSignal()
    ghi_log = pyqtSignal(str) 

    def __init__(self, danh_sach_cai_dat):
        super().__init__()
        self.danh_sach = danh_sach_cai_dat
        self.dung_lai = False

    def xu_ly_log(self, thong_diep):
        thoi_gian = time.strftime('%H:%M:%S')
        self.ghi_log.emit(f"[{thoi_gian}] {thong_diep}")

    def nhan_dang_installer_thong_minh(self, duong_dan_exe):
        try:
            with open(duong_dan_exe, 'rb') as f:
                data_dau = f.read(2 * 1024 * 1024).decode('latin1', errors='ignore')

                if 'Inno Setup' in data_dau or 'InnoSetup' in data_dau:
                    self.xu_ly_log("  -> Nhận diện chữ ký: Inno Setup")
                    return ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"]
                if 'Nullsoft' in data_dau or 'NSIS' in data_dau:
                    self.xu_ly_log("  -> Nhận diện chữ ký: NSIS (Nullsoft)")
                    return ["/S"]
                if 'InstallShield' in data_dau:
                    self.xu_ly_log("  -> Nhận diện chữ ký: InstallShield")
                    return ["/s", '/v"/qn"']
                if 'WiX Toolset' in data_dau or 'wix' in data_dau.lower():
                    self.xu_ly_log("  -> Nhận diện chữ ký: WiX Toolset")
                    return ["/quiet", "/norestart"]
                if 'Advanced Installer' in data_dau:
                    self.xu_ly_log("  -> Nhận diện chữ ký: Advanced Installer")
                    return ["/exenoui", "/qn"]

                f.seek(0, 2)
                kich_thuoc = f.tell()
                if kich_thuoc > 2 * 1024 * 1024:
                    f.seek(kich_thuoc - 2 * 1024 * 1024)
                    data_cuoi = f.read().decode('latin1', errors='ignore')
                    
                    if 'Inno Setup' in data_cuoi or 'InnoSetup' in data_cuoi:
                        self.xu_ly_log("  -> Nhận diện chữ ký (cuối file): Inno Setup")
                        return ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"]
                    if 'Nullsoft' in data_cuoi or 'NSIS' in data_cuoi:
                        self.xu_ly_log("  -> Nhận diện chữ ký (cuối file): NSIS")
                        return ["/S"]
                    if 'InstallShield' in data_cuoi:
                        self.xu_ly_log("  -> Nhận diện chữ ký (cuối file): InstallShield")
                        return ["/s", '/v"/qn"']
        except Exception as e:
            self.xu_ly_log(f"  -> Lỗi phân tích nhị phân: {str(e)}")

        self.xu_ly_log("  -> Không nhận diện được chữ ký, dùng mặc định: /S")
        return ["/S"]

    def phat_hien_cua_so_cai_dat(self, pid_goc):
        try:
            tien_trinh = psutil.Process(pid_goc)
            danh_sach_pid = [p.pid for p in tien_trinh.children(recursive=True)]
            danh_sach_pid.append(pid_goc)
            
            EnumWindows = ctypes.windll.user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
            GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
            IsWindowVisible = ctypes.windll.user32.IsWindowVisible
            GetWindowText = ctypes.windll.user32.GetWindowTextW
            GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
            
            danh_sach_cua_so = []

            def lap_qua_cua_so(hwnd, lParam):
                if IsWindowVisible(hwnd):
                    do_dai = GetWindowTextLength(hwnd)
                    if do_dai > 0:
                        pid_hien_tai = ctypes.c_ulong()
                        GetWindowThreadProcessId(hwnd, ctypes.byref(pid_hien_tai))
                        if pid_hien_tai.value in danh_sach_pid:
                            buff = ctypes.create_unicode_buffer(do_dai + 1)
                            GetWindowText(hwnd, buff, do_dai + 1)
                            ten = buff.value
                            if ten not in ["Default IME", "MSCTFIME UI"]:
                                danh_sach_cua_so.append(ten)
                return True
                
            EnumWindows(EnumWindowsProc(lap_qua_cua_so), 0)
            return danh_sach_cua_so
        except Exception:
            return []

    def huy_tien_trinh_va_con(self, pid_goc):
        try:
            tien_trinh_me = psutil.Process(pid_goc)
            for con in tien_trinh_me.children(recursive=True):
                try: con.kill() 
                except: pass
            tien_trinh_me.kill()
        except:
            pass

    def run(self):
        self.xu_ly_log("=== BẮT ĐẦU TIẾN TRÌNH XỬ LÝ ===")
        for pm in self.danh_sach:
            if self.dung_lai: break
            self.xu_ly_mot_phan_mem(pm)
        if self.dung_lai:
            self.xu_ly_log("=== TIẾN TRÌNH BỊ HỦY BỞI NGƯỜI DÙNG ===")
        else:
            self.xu_ly_log("=== HOÀN TẤT TOÀN BỘ TIẾN TRÌNH ===")
        self.hoan_thanh_toan_bo.emit()

    def dung_tien_trinh(self): self.dung_lai = True

    def xu_ly_mot_phan_mem(self, pm: PhanMem):
        self.xu_ly_log(f"Đang xử lý: {pm.ten}")
        self.cap_nhat_giao_dien.emit(pm, "Đang khởi tạo...", 5)
        duong_dan_luu = self.tai_file_thong_minh(pm)
        
        if not duong_dan_luu:
            self.xu_ly_log(f"❌ Thất bại tải về: {pm.ten}")
            return
            
        if self.dung_lai: return

        duong_dan_str = str(duong_dan_luu)
        file_thuc_thi = duong_dan_str
        is_archive = duong_dan_str.lower().endswith(('.zip', '.rar', '.7z'))
        
        thu_muc_giai_nen = THU_MUC_TEMP / f"Extracted_{''.join(c for c in pm.ten if c.isalnum())}"
        
        if is_archive:
            self.xu_ly_log(f"  -> Giải nén file: {Path(duong_dan_str).name}")
            self.cap_nhat_giao_dien.emit(pm, "Đang bung file nén...", 30)
            thu_muc_giai_nen.mkdir(parents=True, exist_ok=True)
            exe_7z = THU_MUC_TEMP / "7za.exe"
            
            if not exe_7z.exists():
                try:
                    r = requests.get("https://github.com/develar/7zip-bin/raw/master/win/x64/7za.exe", timeout=10)
                    with open(exe_7z, 'wb') as f: f.write(r.content)
                except: pass
            
            subprocess.run([str(exe_7z), "x", duong_dan_str, "-pAdmin@2512", f"-o{thu_muc_giai_nen}", "-y"], creationflags=subprocess.CREATE_NO_WINDOW)
            
            ds_exe = [x for x in thu_muc_giai_nen.rglob("*.*") if x.suffix.lower() in ['.exe', '.msi'] and not re.search(r"(?i)unin|remove", x.name)]
            if ds_exe:
                ds_exe.sort(key=lambda f: f.stat().st_size, reverse=True)
                file_thuc_thi = str(ds_exe[0])
                self.xu_ly_log(f"  -> Đã tìm thấy exe trong file nén: {Path(file_thuc_thi).name}")

        ten_exe_chinh = Path(file_thuc_thi).stem.lower()
        la_app_portable = not re.search(r"(?i)setup|install|msiexec", ten_exe_chinh) and (re.search(r"(?i)unikey|evkey|rufus|anydesk", pm.ten) or is_archive)

        if la_app_portable:
            self.xu_ly_log("  -> Nhận diện là ứng dụng Portable, đang tạo thư mục và Shortcut...")
            self.cap_nhat_giao_dien.emit(pm, "Cài Portable & Tạo lối tắt...", 70)
            thu_muc_dich = Path(os.environ.get('ProgramW6432', 'C:\\Program Files')) / ''.join(c for c in pm.ten if c.isalnum() or c in ' -_')
            try:
                if is_archive: shutil.copytree(thu_muc_giai_nen, thu_muc_dich, dirs_exist_ok=True)
                else:
                    thu_muc_dich.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_thuc_thi, thu_muc_dich)
                
                ds_dich = [x for x in thu_muc_dich.rglob("*.exe") if not re.search(r"(?i)unin|remove|update|crash|setup|helper|subp", x.name)]
                
                if ds_dich:
                    ds_dich.sort(key=lambda f: f.stat().st_size, reverse=True)
                    target_exe = str(ds_dich[0])
                    tu_khoa = pm.ten.split()[0].lower()
                    
                    match_chinh_xac = [x for x in ds_dich if x.stem.lower() == tu_khoa]
                    if match_chinh_xac: target_exe = str(match_chinh_xac[0])
                    else:
                        for exe in ds_dich:
                            ten_exe = exe.stem.lower()
                            if len(ten_exe) >= 3 and ten_exe in pm.ten.lower():
                                target_exe = str(exe)
                                break
                    
                    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
                    vbs_path = THU_MUC_TEMP / "shortcut.vbs"
                    vbs_code = f'''Set ws = WScript.CreateObject("WScript.Shell")\nSet oLink = ws.CreateShortcut("{desktop / (pm.ten + ".lnk")}")\noLink.TargetPath = "{target_exe}"\noLink.WorkingDirectory = "{Path(target_exe).parent}"\noLink.Save'''
                    with open(vbs_path, "w", encoding="utf-8") as f: f.write(vbs_code)
                    
                    subprocess.run(["wscript.exe", str(vbs_path)], creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.Popen([target_exe], creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    self.xu_ly_log(f"✔️ Hoàn tất Portable: {pm.ten}")
                    self.cap_nhat_giao_dien.emit(pm, "Hoàn tất!", 100)
                    return
            except Exception as e: 
                self.xu_ly_log(f"❌ Lỗi xử lý Portable: {str(e)}")

        if file_thuc_thi.lower().endswith('.msi'):
            tham_so_cai = ["/quiet", "/norestart", "ALLUSERS=1"]
            file_thuc_thi = "msiexec.exe"
            lenh_thuc_thi_goc = [file_thuc_thi, "/i", duong_dan_str] + tham_so_cai
            danh_sach_tham_so_thu = [lenh_thuc_thi_goc]
        elif file_thuc_thi.lower().endswith(('.msix', '.appx', '.msixbundle')):
            lenh_thuc_thi_goc = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", f"Add-AppxPackage -Path '{file_thuc_thi}'"]
            danh_sach_tham_so_thu = [lenh_thuc_thi_goc]
        else:
            if pm.tham_so and pm.tham_so.strip():
                tham_so_cai = pm.tham_so.split()
                if len(tham_so_cai) == 1 and tham_so_cai[0].lower() in ['/s', '-s']:
                    tham_so_chuan = self.nhan_dang_installer_thong_minh(file_thuc_thi)
                    if tham_so_chuan == ["/S"] and tham_so_cai[0] != "/S":
                        tham_so_cai = ["/S"]
                        self.xu_ly_log("  -> [Auto-Fix] Tự động sửa lỗi gõ nhầm thành /S (Chuẩn NSIS)")
                    elif tham_so_chuan == ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"]:
                        tham_so_cai = tham_so_chuan
                        self.xu_ly_log("  -> [Auto-Fix] Cập nhật tham số sai thành chuẩn Inno Setup")
                else:
                    self.xu_ly_log(f"  -> Dùng tham số tĩnh từ CSV: {' '.join(tham_so_cai)}")
            else:
                self.xu_ly_log("  -> Đang quét nhị phân để lấy tham số Silent...")
                self.cap_nhat_giao_dien.emit(pm, "Đang phân tích bộ cài...", 45)
                tham_so_cai = self.nhan_dang_installer_thong_minh(file_thuc_thi)

            lenh_thuc_thi_goc = [file_thuc_thi] + tham_so_cai
            danh_sach_tham_so_thu = [lenh_thuc_thi_goc]

            # Thêm các tham số phổ thông làm phương án dự phòng cho file EXE
            cac_tham_so_du_phong = [
                ["/S"], 
                ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"], 
                ["/quiet", "/norestart"], 
                ["/s", '/v"/qn"'], 
                ["-q"]
            ]
            for ts_dp in cac_tham_so_du_phong:
                lenh_moi = [file_thuc_thi] + ts_dp
                if lenh_moi not in danh_sach_tham_so_thu:
                    danh_sach_tham_so_thu.append(lenh_moi)

        cai_dat_thanh_cong = False
        explorer_cu = lay_danh_sach_explorer()

        # VÒNG LẶP THỬ NGHIỆM TỪNG THAM SỐ (BRUTE-FORCE SILENT)
        for lan_thu, lenh_thuc_thi in enumerate(danh_sach_tham_so_thu, 1):
            if self.dung_lai: break
            
            self.xu_ly_log(f"  -> [Lần thử {lan_thu}] Đang nạp lệnh: {' '.join(lenh_thuc_thi)}")
            self.cap_nhat_giao_dien.emit(pm, f"Đang cài (Thử {lan_thu})...", 50)
            
            try:
                process = subprocess.Popen(lenh_thuc_thi, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                
                thoi_gian_cho_toi_da = 600
                bi_bung_giao_dien = False
                
                for i in range(thoi_gian_cho_toi_da):
                    if process.poll() is not None or self.dung_lai: 
                        break
                    
                    tien_trinh_ao = 50 + int((i / thoi_gian_cho_toi_da) * 45)
                    self.cap_nhat_giao_dien.emit(pm, f"Đang tiến hành (Lần {lan_thu})...", tien_trinh_ao)
                    
                    # Radar quét cửa sổ mỗi 3 giây
                    if i > 0 and i % 3 == 0:
                        cua_so_loi = self.phat_hien_cua_so_cai_dat(process.pid)
                        if cua_so_loi:
                            ten_cs = " | ".join(cua_so_loi)
                            self.xu_ly_log(f"  ⚠️ Thất bại: Cửa sổ '{ten_cs}' bị bung ra màn hình!")
                            self.xu_ly_log("  -> Đang dập tiến trình để chuyển sang tham số dự phòng tiếp theo...")
                            self.huy_tien_trinh_va_con(process.pid)
                            bi_bung_giao_dien = True
                            break 
                    
                    for hwnd in lay_danh_sach_explorer():
                        if hwnd not in explorer_cu: dong_cua_so(hwnd)
                    time.sleep(1)
                
                if not bi_bung_giao_dien:
                    if process.poll() is None:
                        self.xu_ly_log("  -> Cảnh báo: Quá 10 phút cài đặt, đang ép thoát.")
                        self.huy_tien_trinh_va_con(process.pid)
                    cai_dat_thanh_cong = True
                    break 

            except Exception as e:
                self.xu_ly_log(f"❌ Lỗi kĩ thuật khi chạy lệnh: {str(e)}")
                
        self.don_rac_he_thong()
        for hwnd in lay_danh_sach_explorer():
            if hwnd not in explorer_cu: dong_cua_so(hwnd)
                
        if cai_dat_thanh_cong:
            self.xu_ly_log(f"✔️ Cài đặt im lặng thành công: {pm.ten}")
            self.cap_nhat_giao_dien.emit(pm, "Hoàn tất!", 100)
        else:
            self.xu_ly_log(f"❌ Bó tay: Đã thử hết toàn bộ tham số nhưng {pm.ten} vẫn không chịu chạy ẩn.")
            self.cap_nhat_giao_dien.emit(pm, "Lỗi cài đặt", 0)

    def lay_id_drive(self, url):
        m = re.search(r"id=([^&]+)", url); return m.group(1) if m else (re.search(r"/d/([^/]+)", url).group(1) if re.search(r"/d/([^/]+)", url) else None)

    def tai_file_thong_minh(self, pm):
        parsed_url = urllib.parse.urlparse(pm.url_tai)
        duoi_file_goc = Path(parsed_url.path).suffix.lower()
        
        danh_sach_duoi_hop_le = ['.exe', '.msi', '.zip', '.rar', '.7z', '.msixbundle', '.appx']
        duoi_su_dung = duoi_file_goc if duoi_file_goc in danh_sach_duoi_hop_le else ".exe"

        ten_file_md = ''.join(c for c in pm.ten if c.isalnum() or c in ' -_') + duoi_su_dung
        duong_dan = THU_MUC_LUU_TRU / ten_file_md
        id_drive = self.lay_id_drive(pm.url_tai)

        if id_drive:
            self.xu_ly_log(f"  -> Link Google Drive ID: {id_drive}")
            for key in DANH_SACH_KHOA_API:
                try:
                    self.cap_nhat_giao_dien.emit(pm, "Quét Drive...", 10)
                    res_meta = requests.get(f"https://www.googleapis.com/drive/v3/files/{id_drive}?fields=name&key={key}", timeout=10)
                    if res_meta.status_code == 200:
                        tg = res_meta.json().get('name', '')
                        if tg and any(tg.lower().endswith(ext) for ext in danh_sach_duoi_hop_le):
                            duong_dan = THU_MUC_LUU_TRU / tg

                    if duong_dan.exists() and duong_dan.stat().st_size > 500 * 1024:
                        self.xu_ly_log(f"  -> File đã tồn tại: {duong_dan.name} ({round(duong_dan.stat().st_size / 1024 / 1024, 1)} MB)")
                        self.cap_nhat_giao_dien.emit(pm, "Đã có sẵn bộ cài", 100)
                        return duong_dan

                    self.xu_ly_log("  -> Đang tải file từ Google Drive...")
                    response = requests.get(f"https://www.googleapis.com/drive/v3/files/{id_drive}?alt=media&key={key}", stream=True, timeout=10)
                    
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'text/html' in content_type:
                        self.xu_ly_log("❌ Lỗi: Link Drive yêu cầu đăng nhập hoặc trỏ tới HTML.")
                        self.cap_nhat_giao_dien.emit(pm, "Lỗi Link (Link dẫn tới trang web)", 0)
                        return None
                        
                    if response.status_code == 200:
                        if self.thuc_hien_ghi_file(pm, response, duong_dan): return duong_dan
                    elif response.status_code in [403, 429]: 
                        self.xu_ly_log("  -> Quá giới hạn API Drive, thử Key khác...")
                        continue 
                except: continue
            self.cap_nhat_giao_dien.emit(pm, "Lỗi kết nối API", 0)
            return None 
        else:
            if duong_dan.exists() and duong_dan.stat().st_size > 500 * 1024:
                self.xu_ly_log(f"  -> File đã tồn tại: {duong_dan.name}")
                self.cap_nhat_giao_dien.emit(pm, "Đã có sẵn bộ cài", 100)
                return duong_dan
            try:
                self.xu_ly_log(f"  -> Đang tải file Direct Link...")
                response = requests.get(pm.url_tai, stream=True, timeout=10)
                
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    self.xu_ly_log("❌ Lỗi: URL trả về trang web HTML.")
                    self.cap_nhat_giao_dien.emit(pm, "Lỗi Link (Link dẫn tới trang web)", 0)
                    return None
                    
                if 'Content-Disposition' in response.headers:
                    m = re.search(r'filename="?([^";]+)"?', response.headers['Content-Disposition'])
                    if m:
                        tth = urllib.parse.unquote(m.group(1))
                        if any(tth.lower().endswith(ext) for ext in danh_sach_duoi_hop_le):
                            duong_dan = THU_MUC_LUU_TRU / tth
                            
                if response.status_code == 200:
                    if self.thuc_hien_ghi_file(pm, response, duong_dan): return duong_dan
            except Exception as e: 
                self.xu_ly_log(f"❌ Lỗi tải xuống: {str(e)}")
        self.cap_nhat_giao_dien.emit(pm, "Lỗi tải xuống", 0)
        return None

    def thuc_hien_ghi_file(self, pm, response, duong_dan):
        tong = int(response.headers.get('content-length', 0))
        da_tai = 0
        t_cap_nhat = time.time()
        with open(duong_dan, 'wb') as f:
            for chunk in response.iter_content(chunk_size=16384): 
                if self.dung_lai: 
                    f.close()
                    try: duong_dan.unlink(missing_ok=True)
                    except: pass
                    return False
                    
                if chunk:
                    f.write(chunk)
                    da_tai += len(chunk)
                    hien_tai = time.time()
                    if hien_tai - t_cap_nhat > 0.2 or da_tai == tong:
                        if tong > 0:
                            pt = int((da_tai / tong) * 100)
                            self.cap_nhat_giao_dien.emit(pm, f"Đang tải: {pt}%", pt)
                        else:
                            mb = round(da_tai / (1024*1024), 1)
                            self.cap_nhat_giao_dien.emit(pm, f"Đang tải: {mb} MB", 50)
                        t_cap_nhat = hien_tai
                        
        if duong_dan.exists() and duong_dan.stat().st_size < 500 * 1024:
            try: duong_dan.unlink(missing_ok=True)
            except: pass
            self.xu_ly_log("❌ Lỗi: File tải về quá nhỏ hoặc bị hỏng")
            self.cap_nhat_giao_dien.emit(pm, "Lỗi: File tải về quá nhỏ/bị hỏng", 0)
            return False
            
        return True

    def don_rac_he_thong(self):
        self.xu_ly_log("  -> Dọn dẹp tiến trình phụ (cmd, notepad)...")
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() in ['cmd.exe', 'notepad.exe', 'hh.exe']:
                    proc.kill()
            except: pass

# ==============================================================================
# GIAO DIỆN CHÍNH (GUI)
# ==============================================================================
class VietToolboxApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.danh_sach_phan_mem = []
        self.danh_sach_ui = {} 
        self.ds_dang_cai = []
        self.luong_cai_dat = None
        self.luong_icon = None

        self.dong_ho = QTimer(self)
        self.dong_ho.timeout.connect(self.cap_nhat_thoi_gian)
        self.thoi_gian_bat_dau = 0

        self.thiet_lap_giao_dien()
        self.tai_du_lieu_csv()

    def thiet_lap_giao_dien(self):
        self.setWindowTitle("VietToolbox Dashboard - V711 (Auto-Brute-Force Silent)")
        self.setMinimumSize(1150, 780)
        self.setStyleSheet("background-color: #0B1120; font-family: 'Segoe UI';")

        widget_chinh = QWidget()
        layout_chinh = QHBoxLayout(widget_chinh)
        layout_chinh.setContentsMargins(0, 0, 0, 0)
        layout_chinh.setSpacing(0)

        panel_trai = QFrame()
        panel_trai.setFixedWidth(300)
        panel_trai.setStyleSheet("background-color: #0F172A; color: white;")
        layout_trai = QVBoxLayout(panel_trai)
        layout_trai.setContentsMargins(20, 30, 20, 20)
        
        lbl_logo = QLabel("🚀\nVIETTOOLBOX")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setFont(QFont("Segoe UI", 20, QFont.Weight.Black))
        layout_trai.addWidget(lbl_logo)
        layout_trai.addSpacing(25)

        self.btn_bat_dau = QPushButton("▶ BẮT ĐẦU CÀI ĐẶT")
        self.btn_bat_dau.setFixedHeight(50)
        self.btn_bat_dau.setStyleSheet("QPushButton { background-color: #10B981; color: white; font-weight: bold; border-radius: 8px; font-size: 13px; } QPushButton:hover { background-color: #059669; }")
        self.btn_bat_dau.clicked.connect(self.bat_dau_cai_dat)
        layout_trai.addWidget(self.btn_bat_dau)

        self.btn_huy = QPushButton("⏹ HỦY TIẾN TRÌNH")
        self.btn_huy.setFixedHeight(45)
        self.btn_huy.setEnabled(False)
        self.btn_huy.setStyleSheet("QPushButton { background-color: #EF4444; color: white; font-weight: bold; border-radius: 8px; font-size: 13px; }")
        self.btn_huy.clicked.connect(self.huy_cai_dat)
        layout_trai.addWidget(self.btn_huy)

        frame_tk = QFrame()
        frame_tk.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        layout_tk = QHBoxLayout(frame_tk)
        self.lbl_so_luong = QLabel("0")
        self.lbl_so_luong.setStyleSheet("color: #10B981; font-size: 24px; font-weight: bold;")
        lbl_text_da_chon = QLabel("Đã chọn")
        lbl_text_da_chon.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout_tk.addWidget(self.lbl_so_luong, alignment=Qt.AlignmentFlag.AlignRight)
        layout_tk.addWidget(lbl_text_da_chon, alignment=Qt.AlignmentFlag.AlignLeft)
        layout_trai.addWidget(frame_tk)
        layout_trai.addSpacing(15)

        khung_tien_trinh = QFrame()
        khung_tien_trinh.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 10px;")
        layout_tien_trinh = QVBoxLayout(khung_tien_trinh)
        layout_tien_trinh.setContentsMargins(15, 15, 15, 15)

        self.lbl_thoi_gian = QLabel("⏱ Thời gian: 00:00")
        self.lbl_thoi_gian.setStyleSheet("background-color: transparent; color: #38BDF8; font-weight: bold; font-size: 13px; border: none;")

        self.lbl_phan_tram_tong = QLabel("Tổng tiến trình: 0%")
        self.lbl_phan_tram_tong.setStyleSheet("background-color: transparent; color: #94A3B8; font-size: 12px; border: none; margin-top: 5px;")

        self.prg_tong = QProgressBar()
        self.prg_tong.setFixedHeight(8)
        self.prg_tong.setTextVisible(False)
        self.prg_tong.setStyleSheet("QProgressBar { border: none; background: #0B1120; border-radius: 4px; margin-top: 5px; } QProgressBar::chunk { background-color: #38BDF8; border-radius: 4px; }")

        layout_tien_trinh.addWidget(self.lbl_thoi_gian)
        layout_tien_trinh.addWidget(self.lbl_phan_tram_tong)
        layout_tien_trinh.addWidget(self.prg_tong)

        layout_trai.addWidget(khung_tien_trinh)
        layout_trai.addSpacing(15)

        frame_log = QFrame()
        frame_log.setStyleSheet("background-color: #0B1120; border-radius: 8px;")
        layout_log = QVBoxLayout(frame_log)
        layout_log.setContentsMargins(0, 0, 0, 0)
        
        lbl_log_title = QLabel("📋  Danh sách chờ cài đặt")
        lbl_log_title.setStyleSheet("background-color: #1E293B; color: #38BDF8; padding: 10px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; font-size: 11px;")
        layout_log.addWidget(lbl_log_title)
        
        self.scroll_log = QScrollArea()
        self.scroll_log.setWidgetResizable(True)
        self.scroll_log.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; } 
            QScrollBar:vertical { width: 6px; background-color: #0F172A; } 
            QScrollBar::handle:vertical { background-color: #334155; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        self.widget_log_content = QWidget()
        self.widget_log_content.setStyleSheet("background-color: transparent;")
        self.layout_log_content = QVBoxLayout(self.widget_log_content)
        self.layout_log_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_log_content.setContentsMargins(8, 8, 8, 8)
        self.layout_log_content.setSpacing(4)
        
        self.scroll_log.setWidget(self.widget_log_content)
        layout_log.addWidget(self.scroll_log)
        layout_trai.addWidget(frame_log, 1)

        panel_phai = QWidget()
        self.layout_phai = QVBoxLayout(panel_phai)
        self.layout_phai.setContentsMargins(20, 20, 20, 20)
        self.layout_phai.setSpacing(15)

        khung_tieu_de = QWidget()
        layout_td = QHBoxLayout(khung_tieu_de)
        layout_td.setContentsMargins(0, 0, 0, 0)
        
        btn_chon_het = QPushButton("☑ Chọn tất cả")
        btn_bo_chon = QPushButton("☐ Bỏ chọn")
        btn_lam_moi = QPushButton("🔄 Làm mới")
        
        for btn in [btn_chon_het, btn_bo_chon, btn_lam_moi]:
            btn.setFixedSize(110, 36)
            btn.setStyleSheet("QPushButton { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; color: #F8FAFC; font-weight: 600; } QPushButton:hover { background-color: #334155; }")
        
        btn_lam_moi.setStyleSheet("QPushButton { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; color: #38BDF8; font-weight: 600; } QPushButton:hover { background-color: #334155; }")
        
        btn_chon_het.clicked.connect(lambda: self.doi_trang_thai_chon(True))
        btn_bo_chon.clicked.connect(lambda: self.doi_trang_thai_chon(False))
        btn_lam_moi.clicked.connect(self.lam_moi_toan_bo)
        
        layout_td.addWidget(btn_chon_het)
        layout_td.addWidget(btn_bo_chon)
        layout_td.addWidget(btn_lam_moi)
        layout_td.addStretch()
        self.layout_phai.addWidget(khung_tieu_de)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; } 
            QScrollBar:vertical { width: 8px; background-color: #0B1120; margin: 0px; } 
            QScrollBar::handle:vertical { background-color: #475569; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        self.khung_danh_sach = QWidget()
        self.khung_danh_sach.setStyleSheet("background-color: transparent;")
        self.layout_danh_sach = QVBoxLayout(self.khung_danh_sach) 
        self.scroll_area.setWidget(self.khung_danh_sach)
        self.layout_phai.addWidget(self.scroll_area, stretch=7) 

        self.txt_log_terminal = QPlainTextEdit()
        self.txt_log_terminal.setReadOnly(True)
        self.txt_log_terminal.setPlaceholderText("Terminal Log: Chờ lệnh thực thi...")
        self.txt_log_terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0F172A;
                color: #A7F3D0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            QScrollBar:vertical { width: 8px; background-color: #0F172A; margin: 0px; } 
            QScrollBar::handle:vertical { background-color: #475569; border-radius: 4px; }
        """)
        self.layout_phai.addWidget(self.txt_log_terminal, stretch=3) 

        layout_chinh.addWidget(panel_trai)
        layout_chinh.addWidget(panel_phai)
        self.setCentralWidget(widget_chinh)

    def cap_nhat_thoi_gian(self):
        giay_troi_qua = int(time.time() - self.thoi_gian_bat_dau)
        phut = giay_troi_qua // 60
        giay = giay_troi_qua % 60
        self.lbl_thoi_gian.setText(f"⏱ Thời gian: {phut:02d}:{giay:02d}")

    def lam_moi_toan_bo(self):
        self.dong_ho.stop()
        self.lbl_thoi_gian.setText("⏱ Thời gian: 00:00")
        self.prg_tong.setValue(0)
        self.lbl_phan_tram_tong.setText("Tổng tiến trình: 0%")
        self.txt_log_terminal.clear() 

        for pm in self.danh_sach_phan_mem:
            pm.chon = False
            pm.trang_thai = "Sẵn sàng"
            pm.tien_trinh = 0
            pm.ket_qua = ""
            ui = self.danh_sach_ui.get(pm)
            if ui:
                ui['chk'].setChecked(False)
                ui['prg'].setValue(0)
                ui['prg'].setStyleSheet("QProgressBar::chunk { background-color: #10B981; border-radius: 4px; }")
                ui['lbl_tt'].setText("Sẵn sàng")
        self.cap_nhat_danh_sach_chon()

    def tuong_tac_card(self, pm):
        pm.chon = not pm.chon
        self.danh_sach_ui[pm]['chk'].setChecked(pm.chon)
        self.cap_nhat_danh_sach_chon()

    def tai_du_lieu_csv(self):
        try:
            response = requests.get(URL_CSV)
            response.encoding = 'utf-8'
            reader = csv.DictReader(response.text.splitlines())
            
            for row in reader:
                if not row.get('DownloadUrl'): continue
                
                pm = PhanMem(
                    ten=row.get('Name', 'Unknown'),
                    url_tai=row.get('DownloadUrl', ''),
                    tham_so=row.get('SilentArgs', ''),
                    danh_muc=row.get('Category', row.get('catologi', 'Chung')),
                    icon_url=row.get('IconURL', ''),
                    mac_dinh_chon=(row.get('Check', 'False').lower() == 'true')
                )
                self.danh_sach_phan_mem.append(pm)
            
            self.ve_danh_sach_phan_mem()
            self.cap_nhat_danh_sach_chon()

            self.luong_icon = LuongTaiIcon(self.danh_sach_phan_mem)
            self.luong_icon.icon_da_tai.connect(self.gan_icon_vao_ui)
            self.luong_icon.start()
        except Exception as e: pass

    def ve_danh_sach_phan_mem(self):
        danh_muc_dict = {}
        for pm in self.danh_sach_phan_mem:
            cat = pm.danh_muc if pm.danh_muc else "Khác"
            if cat not in danh_muc_dict: danh_muc_dict[cat] = []
            danh_muc_dict[cat].append(pm)

        for danh_muc, ds_pm in danh_muc_dict.items():
            lbl_dm = QLabel(danh_muc)
            lbl_dm.setStyleSheet("background-color: transparent; font-size: 16px; font-weight: bold; color: #38BDF8; margin-top: 20px; margin-bottom: 8px;")
            self.layout_danh_sach.addWidget(lbl_dm)

            vbox_cat = QVBoxLayout()
            vbox_cat.setContentsMargins(0, 0, 0, 0)
            vbox_cat.setSpacing(0)

            for pm in ds_pm:
                card = CardPhanMem(pm, self.tuong_tac_card)
                card.setFixedHeight(60) 
                
                layout_card = QHBoxLayout(card)
                layout_card.setContentsMargins(15, 5, 15, 5)
                
                chk = QCheckBox()
                chk.setChecked(pm.chon)
                chk.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
                chk.setStyleSheet("""
                    QCheckBox { background-color: transparent; }
                    QCheckBox::indicator { 
                        width: 18px; height: 18px; 
                        border: 2px solid #475569; 
                        border-radius: 4px; 
                        background-color: #1E293B; 
                    }
                    QCheckBox::indicator:checked { 
                        background-color: #10B981; 
                        border: 2px solid #10B981; 
                    }
                """) 
                
                lbl_icon = QLabel()
                lbl_icon.setFixedSize(32, 32)
                lbl_icon.setStyleSheet("background-color: transparent; border: none;")
                
                lbl_ten = QLabel(pm.ten)
                lbl_ten.setFixedWidth(200)
                lbl_ten.setStyleSheet("background-color: transparent; font-weight: bold; font-size: 13px; color: #F8FAFC; border: none;")
                
                prg = QProgressBar()
                prg.setFixedHeight(8)
                prg.setTextVisible(False)
                prg.setStyleSheet("QProgressBar { border: none; background: #0F172A; border-radius: 4px; } QProgressBar::chunk { background-color: #10B981; border-radius: 4px; }")
                
                lbl_tt = QLabel(pm.trang_thai)
                lbl_tt.setFixedWidth(130)
                lbl_tt.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                lbl_tt.setStyleSheet("background-color: transparent; color: #94A3B8; font-size: 11px; border: none; font-weight: 600;")

                layout_card.addWidget(chk)
                layout_card.addSpacing(10)
                layout_card.addWidget(lbl_icon)
                layout_card.addWidget(lbl_ten)
                layout_card.addWidget(prg)
                layout_card.addWidget(lbl_tt)

                vbox_cat.addWidget(card)
                self.danh_sach_ui[pm] = {'chk': chk, 'lbl_icon': lbl_icon, 'prg': prg, 'lbl_tt': lbl_tt}

            widget_cat = QWidget()
            widget_cat.setStyleSheet("background-color: transparent;")
            widget_cat.setLayout(vbox_cat)
            self.layout_danh_sach.addWidget(widget_cat)

        self.layout_danh_sach.addStretch()

    def cap_nhat_danh_sach_chon(self):
        for i in reversed(range(self.layout_log_content.count())):
            widget = self.layout_log_content.itemAt(i).widget()
            if widget: widget.setParent(None)

        ds_chon = [pm for pm in self.danh_sach_phan_mem if pm.chon]
        self.lbl_so_luong.setText(str(len(ds_chon)))

        if not ds_chon:
            lbl_trong = QLabel("Chưa chọn phần mềm nào")
            lbl_trong.setStyleSheet("background-color: transparent; color: #475569; font-style: italic; font-size: 11px;")
            self.layout_log_content.addWidget(lbl_trong)
            return

        for stt, pm in enumerate(ds_chon, 1):
            khung_item = QFrame()
            khung_item.setStyleSheet("background-color: #1E293B; border-radius: 5px;")
            khung_item.setFixedHeight(32)
            layout_item = QHBoxLayout(khung_item)
            layout_item.setContentsMargins(10, 0, 10, 0)
            
            lbl_stt = QLabel(f"{stt}. ")
            lbl_stt.setStyleSheet("background-color: transparent; color: #64748B; font-size: 11px;")
            
            lbl_ten = QLabel(pm.ten)
            lbl_ten.setStyleSheet("background-color: transparent; color: white; font-weight: bold; font-size: 11px;")
            
            lbl_kq = QLabel(pm.ket_qua)
            mau_kq = "#10B981" if "✔" in pm.ket_qua else "#EF4444"
            lbl_kq.setStyleSheet(f"background-color: transparent; color: {mau_kq}; font-weight: bold; font-size: 12px;")
            
            layout_item.addWidget(lbl_stt)
            layout_item.addWidget(lbl_ten, 1)
            layout_item.addWidget(lbl_kq)
            self.layout_log_content.addWidget(khung_item)

        self.scroll_log.verticalScrollBar().setValue(self.scroll_log.verticalScrollBar().maximum())

    def gan_icon_vao_ui(self, pm, du_lieu_anh):
        ui = self.danh_sach_ui.get(pm)
        if ui and 'lbl_icon' in ui:
            pixmap = QPixmap()
            pixmap.loadFromData(du_lieu_anh)
            ui['lbl_icon'].setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def doi_trang_thai_chon(self, trang_thai):
        for pm in self.danh_sach_phan_mem:
            pm.chon = trang_thai
            self.danh_sach_ui[pm]['chk'].setChecked(trang_thai)
        self.cap_nhat_danh_sach_chon()

    def ghi_terminal_log(self, text):
        self.txt_log_terminal.appendPlainText(text)
        scrollbar = self.txt_log_terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def cap_nhat_ui_phan_mem(self, pm, txt_trang_thai, phan_tram):
        pm.tien_trinh = phan_tram
        
        if self.ds_dang_cai:
            tong_phan_tram = sum(p.tien_trinh for p in self.ds_dang_cai) / len(self.ds_dang_cai)
            self.prg_tong.setValue(int(tong_phan_tram))
            self.lbl_phan_tram_tong.setText(f"Tổng tiến trình: {int(tong_phan_tram)}%")

        ui = self.danh_sach_ui.get(pm)
        if ui:
            ui['lbl_tt'].setText(txt_trang_thai)
            ui['prg'].setValue(phan_tram)
            if "Lỗi" in txt_trang_thai:
                ui['prg'].setStyleSheet("QProgressBar::chunk { background-color: #EF4444; border-radius: 4px; }")
                pm.ket_qua = " ❌"
                self.cap_nhat_danh_sach_chon()
            elif "Hoàn tất" in txt_trang_thai:
                pm.ket_qua = " ✔"
                self.cap_nhat_danh_sach_chon()

    def bat_dau_cai_dat(self):
        self.ds_dang_cai = [pm for pm in self.danh_sach_phan_mem if pm.chon]
        if not self.ds_dang_cai: return

        self.txt_log_terminal.clear() 
        self.prg_tong.setValue(0)
        self.lbl_phan_tram_tong.setText("Tổng tiến trình: 0%")
        
        self.thoi_gian_bat_dau = time.time()
        self.cap_nhat_thoi_gian()
        self.dong_ho.start(1000)

        for pm in self.ds_dang_cai: pm.ket_qua = ""
        self.cap_nhat_danh_sach_chon()

        self.btn_bat_dau.setEnabled(False)
        self.btn_bat_dau.setText("⏳ ĐANG XỬ LÝ...")
        self.btn_huy.setEnabled(True)

        self.luong_cai_dat = LuongCaiDat(self.ds_dang_cai)
        self.luong_cai_dat.cap_nhat_giao_dien.connect(self.cap_nhat_ui_phan_mem)
        self.luong_cai_dat.hoan_thanh_toan_bo.connect(self.ket_thuc_cai_dat)
        self.luong_cai_dat.ghi_log.connect(self.ghi_terminal_log) 
        self.luong_cai_dat.start()

    def huy_cai_dat(self):
        if self.luong_cai_dat:
            self.dong_ho.stop()
            self.luong_cai_dat.dung_tien_trinh()
            self.btn_huy.setText("ĐANG DỪNG...")
            self.btn_huy.setEnabled(False)

    def ket_thuc_cai_dat(self):
        self.dong_ho.stop()
        self.prg_tong.setValue(100)
        self.lbl_phan_tram_tong.setText("Tổng tiến trình: 100%")
        
        self.btn_bat_dau.setEnabled(True)
        self.btn_bat_dau.setText("▶ BẮT ĐẦU CÀI ĐẶT")
        self.btn_huy.setEnabled(False)
        self.btn_huy.setText("⏹ HỦY TIẾN TRÌNH")

    def closeEvent(self, event):
        try:
            if THU_MUC_LUU_TRU.exists():
                shutil.rmtree(THU_MUC_LUU_TRU, ignore_errors=True)
            if THU_MUC_TEMP.exists():
                shutil.rmtree(THU_MUC_TEMP, ignore_errors=True)
        except Exception:
            pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VietToolboxApp()
    window.show()
    sys.exit(app.exec())