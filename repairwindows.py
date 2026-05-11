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
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def yeu_cau_quyen_admin():
    if kiem_tra_quyen_admin():
        return True
    
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
        self.root.title("Công Cụ Sửa Chữa & Tối Ưu Windows (Live Log)")
        self.root.geometry("680x500")
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

        lbl_tieude = tk.Label(root, text="HỆ THỐNG TỐI ƯU HÓA TỰ ĐỘNG", 
                              font=("Segoe UI", 14, "bold"), bg="#202124", fg="#e8eaed")
        lbl_tieude.pack(side=tk.TOP, pady=(15, 10))

        self.btn_bat_dau = tk.Button(root, text="BẮT ĐẦU XỬ LÝ", font=("Segoe UI", 11, "bold"), 
                                     bg="#8ab4f8", fg="#202124", relief="flat", borderwidth=0, 
                                     activebackground="#aecbfa", activeforeground="#202124",
                                     cursor="hand2", command=self.khoi_dong_luong, width=20, height=2)
        self.btn_bat_dau.pack(side=tk.BOTTOM, pady=(10, 20))

        self.thanh_tien_trinh = ttk.Progressbar(root, style="TProgressbar", orient="horizontal", 
                                                mode="determinate", length=640)
        self.thanh_tien_trinh.pack(side=tk.BOTTOM, padx=20, pady=(0, 15))

        khung_log = tk.Frame(root, bg="#202124")
        khung_log.pack(side=tk.TOP, padx=20, pady=5, fill=tk.BOTH, expand=True)

        self.txt_log = tk.Text(khung_log, font=("Consolas", 10), bg="#303134", fg="#00ff00", # Đổi màu chữ xanh lá phong cách hacker/console
                               relief="flat", borderwidth=10, state=tk.DISABLED)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        Thanh_cuon = tk.Scrollbar(khung_log, command=self.txt_log.yview, bg="#202124", troughcolor="#303134")
        Thanh_cuon.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.config(yscrollcommand=Thanh_cuon.set)

    def ghi_log(self, thong_diep, ghi_de=False):
        """
        Ghi nội dung ra màn hình. Nếu ghi_de=True, sẽ xóa dòng hiển thị cuối cùng và đè nội dung mới lên.
        Thao tác này giúp mô phỏng hiệu ứng đếm % liên tục của SFC/DISM.
        """
        self.txt_log.config(state=tk.NORMAL)
        if ghi_de:
            self.txt_log.delete("end-2l", "end-1c")
        
        self.txt_log.insert(tk.END, thong_diep + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def cap_nhat_tien_trinh(self, gia_tri):
        self.thanh_tien_trinh['value'] = gia_tri
        self.root.update_idletasks()

    def chay_lenh_thoi_gian_thuc(self, lenh, mo_ta):
        """Thực thi lệnh và bắt kết quả in ra liên tục theo thời gian thực (Live Stream)"""
        self.ghi_log(f"\n[*] Đang chạy: {mo_ta}...")
        try:
            CREATE_NO_WINDOW = 0x08000000
            # Dùng Popen và encoding 'mbcs' để đọc chuẩn tiếng Việt/Anh từ Windows Console
            tien_trinh = subprocess.Popen(
                lenh, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, encoding='mbcs', errors='replace', creationflags=CREATE_NO_WINDOW
            )
            
            dong_tam = ""
            vua_ghi_de = False 

            # Đọc từng ký tự một để bắt được ngắt dòng (\n) và đè dòng (\r)
            while True:
                kytu = tien_trinh.stdout.read(1)
                if not kytu:
                    break
                
                if kytu == '\n':
                    if dong_tam.strip():
                        self.ghi_log(f"  > {dong_tam.strip()}", ghi_de=vua_ghi_de)
                        vua_ghi_de = False
                    dong_tam = ""
                elif kytu == '\r':
                    if dong_tam.strip():
                        # Gặp \r (Carriage Return), in dòng này ra nhưng đánh dấu lần sau sẽ ghi đè lên nó
                        self.ghi_log(f"  > {dong_tam.strip()}", ghi_de=vua_ghi_de)
                        vua_ghi_de = True
                    dong_tam = ""
                else:
                    dong_tam += kytu

            # Quét nốt những chữ cuối cùng nếu chưa có ngắt dòng
            if dong_tam.strip():
                self.ghi_log(f"  > {dong_tam.strip()}", ghi_de=vua_ghi_de)

            tien_trinh.wait()
            if tien_trinh.returncode == 0:
                self.ghi_log(f"[+] Đã xong bước: {mo_ta}")
            else:
                self.ghi_log(f"[-] Cảnh báo (Mã lỗi: {tien_trinh.returncode})")
        except Exception as e:
            self.ghi_log(f"[-] Lỗi phát sinh: {e}")

    def don_dep_o_cung(self):
        self.ghi_log("\n[*] Đang dọn dẹp thư mục Temp và Prefetch...")
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
        self.ghi_log(f"  [+] Đã giải phóng {tong_so_file_xoa} tệp tin rác.")

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
        self.cap_nhat_tien_trinh(15)
        time.sleep(0.5)

        self.chay_lenh_thoi_gian_thuc("ipconfig /flushdns", "Xóa bộ nhớ cache DNS")
        self.cap_nhat_tien_trinh(30)

        self.chay_lenh_thoi_gian_thuc("sc config SysMain start= disabled & net stop SysMain", "Tắt dịch vụ SysMain (Giảm tải Disk 100%)")
        self.cap_nhat_tien_trinh(45)

        lenh_reg = 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f'
        self.chay_lenh_thoi_gian_thuc(lenh_reg, "Thiết lập đồ họa ưu tiên hiệu năng")
        self.cap_nhat_tien_trinh(60)

        # Hai lệnh này giờ đây sẽ nhảy % liên tục trên màn hình
        self.chay_lenh_thoi_gian_thuc("sfc /scannow", "Quét và vá lỗi tệp tin hệ thống (SFC)")
        self.cap_nhat_tien_trinh(80)

        self.chay_lenh_thoi_gian_thuc("DISM /Online /Cleanup-Image /RestoreHealth", "Phục hồi Image Windows (DISM)")
        self.cap_nhat_tien_trinh(100)

        self.ghi_log("\n" + "="*45)
        self.ghi_log("HOÀN TẤT TOÀN BỘ QUÁ TRÌNH!")
        self.ghi_log("Khuyến nghị khởi động lại máy tính.")
        
        self.btn_bat_dau.config(state=tk.NORMAL, bg="#8ab4f8", text="HOÀN TẤT (THOÁT)", command=self.root.quit)

def chay_ung_dung():
    yeu_cau_quyen_admin()
    
    root = tk.Tk()
    app = ToiUuWindowsApp(root)
    root.mainloop()

if __name__ == "__main__":
    chay_ung_dung()