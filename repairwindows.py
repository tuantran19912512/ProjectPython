import os
import sys
import subprocess
import ctypes
import shutil
import tkinter as tk
from tkinter import ttk
import threading
import time

def kiem_tra_quyen_admin():
    """Kiểm tra xem phần mềm có đang chạy dưới quyền Admin hay không."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def yeu_cau_quyen_admin():
    """Tự động gọi hộp thoại UAC để xin cấp quyền Administrator."""
    if kiem_tra_quyen_admin():
        return True
    
    # Sử dụng __file__ an toàn hơn sys.argv[0] để tránh lỗi hiện khung đen Console khi chạy trên IDE
    if getattr(sys, 'frozen', False):
        thuc_thi = sys.executable
        tham_so = ""
    else:
        thuc_thi = sys.executable
        tham_so = f'"{os.path.abspath(__file__)}"'
    
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", thuc_thi, tham_so, None, 1)
        sys.exit()
    except Exception:
        sys.exit()

class ToiUuWindowsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công Cụ Sửa Chữa & Tối Ưu Windows")
        self.root.geometry("650x450")
        self.root.configure(bg="#202124") 
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", 
                        background="#8ab4f8", 
                        troughcolor="#303134", 
                        bordercolor="#202124", 
                        lightcolor="#8ab4f8", 
                        darkcolor="#8ab4f8", 
                        thickness=15)

        # 1. Ghim Tiêu đề ở trên cùng
        lbl_tieude = tk.Label(root, text="HỆ THỐNG TỐI ƯU HÓA TỰ ĐỘNG", 
                              font=("Segoe UI", 14, "bold"), bg="#202124", fg="#e8eaed")
        lbl_tieude.pack(side=tk.TOP, pady=(15, 10))

        # 2. Ghim Nút bấm ở dưới cùng (để không bao giờ bị log đè lên)
        self.btn_bat_dau = tk.Button(root, text="BẮT ĐẦU XỬ LÝ", font=("Segoe UI", 11, "bold"), 
                                     bg="#8ab4f8", fg="#202124", relief="flat", borderwidth=0, 
                                     activebackground="#aecbfa", activeforeground="#202124",
                                     cursor="hand2", command=self.khoi_dong_luong, width=20, height=2)
        self.btn_bat_dau.pack(side=tk.BOTTOM, pady=(10, 20))

        # 3. Ghim Thanh tiến trình nằm ngay trên Nút bấm
        self.thanh_tien_trinh = ttk.Progressbar(root, style="TProgressbar", orient="horizontal", 
                                                mode="determinate", length=610)
        self.thanh_tien_trinh.pack(side=tk.BOTTOM, padx=20, pady=(0, 15))

        # 4. Để Khung log chiếm toàn bộ khoảng trống còn lại ở giữa
        khung_log = tk.Frame(root, bg="#202124")
        khung_log.pack(side=tk.TOP, padx=20, pady=5, fill=tk.BOTH, expand=True)

        self.txt_log = tk.Text(khung_log, font=("Consolas", 10), bg="#303134", fg="#e8eaed", 
                               relief="flat", borderwidth=10, state=tk.DISABLED)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        Thanh_cuon = tk.Scrollbar(khung_log, command=self.txt_log.yview, bg="#202124", troughcolor="#303134")
        Thanh_cuon.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.config(yscrollcommand=Thanh_cuon.set)

    def ghi_log(self, thong_diep):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, thong_diep + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def cap_nhat_tien_trinh(self, gia_tri):
        self.thanh_tien_trinh['value'] = gia_tri
        self.root.update_idletasks()

    def chay_lenh_he_thong(self, lenh, mo_ta):
        self.ghi_log(f"[*] Đang xử lý: {mo_ta}...")
        try:
            CREATE_NO_WINDOW = 0x08000000
            ket_qua = subprocess.run(lenh, shell=True, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            if ket_qua.returncode == 0:
                self.ghi_log(f"  [+] Hoàn thành: {mo_ta}")
            else:
                self.ghi_log(f"  [-] Cảnh báo khi chạy: {mo_ta} (Mã: {ket_qua.returncode})")
        except Exception as loi:
            self.ghi_log(f"  [-] Đã xảy ra lỗi: {loi}")

    def don_dep_o_cung(self):
        self.ghi_log("[*] Đang dọn dẹp thư mục Temp và Prefetch...")
        cac_thu_muc = [
            os.environ.get('TEMP'),
            os.environ.get('TMP'),
            r"C:\Windows\Temp",
            r"C:\Windows\Prefetch"
        ]
        
        tong_so_file_xoa = 0
        for thu_muc in cac_thu_muc:
            if thu_muc and os.path.exists(thu_muc):
                for root_dir, dirs, files in os.walk(thu_muc):
                    for file in files:
                        try:
                            os.remove(os.path.join(root_dir, file))
                            tong_so_file_xoa += 1
                        except Exception:
                            pass
                    for dir in dirs:
                        try:
                            shutil.rmtree(os.path.join(root_dir, dir))
                        except Exception:
                            pass
        self.ghi_log(f"  [+] Đã giải phóng {tong_so_file_xoa} tệp tin rác khỏi hệ thống.")

    def khoi_dong_luong(self):
        self.btn_bat_dau.config(state=tk.DISABLED, bg="#5f6368", text="ĐANG XỬ LÝ...")
        self.thanh_tien_trinh['value'] = 0
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.config(state=tk.DISABLED)
        
        luong_xu_ly = threading.Thread(target=self.tien_trinh_xu_ly_chinh)
        luong_xu_ly.daemon = True
        luong_xu_ly.start()

    def tien_trinh_xu_ly_chinh(self):
        self.ghi_log("=== BẮT ĐẦU TIẾN TRÌNH TỐI ƯU HÓA ===")
        
        self.don_dep_o_cung()
        self.cap_nhat_tien_trinh(20)
        time.sleep(1)

        self.chay_lenh_he_thong("ipconfig /flushdns", "Xóa bộ nhớ cache DNS")
        self.cap_nhat_tien_trinh(35)

        self.chay_lenh_he_thong("sc config SysMain start= disabled & net stop SysMain", "Vô hiệu hóa dịch vụ SysMain (Giảm tải Disk 100%)")
        self.cap_nhat_tien_trinh(50)

        lenh_reg = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f'
        self.chay_lenh_he_thong(lenh_reg, "Điều chỉnh hiệu ứng Windows ưu tiên hiệu năng")
        self.cap_nhat_tien_trinh(65)

        self.ghi_log("\n[*] Đang quét cấu trúc tệp hệ thống (SFC). Việc này có thể mất vài phút...")
        self.chay_lenh_he_thong("sfc /scannow", "Quét và vá lỗi tệp tin hệ thống")
        self.cap_nhat_tien_trinh(85)

        self.ghi_log("\n[*] Đang kiểm tra và phục hồi Image Windows (DISM). Vui lòng chờ...")
        self.chay_lenh_he_thong("DISM /Online /Cleanup-Image /RestoreHealth", "Phục hồi Image Windows")
        self.cap_nhat_tien_trinh(100)

        self.ghi_log("\n=== HOÀN TẤT QUÁ TRÌNH TỐI ƯU HÓA ===")
        self.ghi_log("[!] Vui lòng khởi động lại máy tính để các thay đổi có hiệu lực.")
        
        self.btn_bat_dau.config(state=tk.NORMAL, bg="#8ab4f8", text="HOÀN TẤT (THOÁT)", command=self.root.quit)

def chay_ung_dung():
    yeu_cau_quyen_admin()
    
    root = tk.Tk()
    app = ToiUuWindowsApp(root)
    root.mainloop()

if __name__ == "__main__":
    chay_ung_dung()