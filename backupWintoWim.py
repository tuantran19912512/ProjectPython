import os
import sys
import ctypes
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# ==========================================
# 1. YÊU CẦU QUYỀN ADMIN
# ==========================================
def kiem_tra_quyen_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not kiem_tra_quyen_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# ==========================================
# 2. HÀM CHẠY LỆNH HỆ THỐNG
# ==========================================
def chay_lenh(lenh, la_powershell=False):
    try:
        if la_powershell:
            lenh = ["powershell", "-NoProfile", "-Command", lenh]
        ket_qua = subprocess.run(lenh, capture_output=True, text=True, shell=(not la_powershell), creationflags=subprocess.CREATE_NO_WINDOW)
        return ket_qua.stdout.strip(), ket_qua.returncode
    except Exception as e:
        return str(e), 1

# ==========================================
# 3. GIAO DIỆN & LOGIC HỆ THỐNG
# ==========================================
class CongCuBackupV17_Compact(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.title("Auto Sysprep & Capture Tool V1.7 - Compact Edition")
        # Đã thu gọn kích thước từ 750x880 xuống 700x650
        self.geometry("700x650")
        self.configure(fg_color="#0B0F19")
        
        self.duong_dan_winre = tk.StringVar()
        self.duong_dan_luu = tk.StringVar()
        
        self.tao_giao_dien()
        self.kiem_tra_winre()

    def tao_giao_dien(self):
        font_tieu_de = ("Segoe UI", 18, "bold")
        font_muc = ("Segoe UI", 13, "bold")
        font_chu = ("Segoe UI", 12)
        font_log = ("Consolas", 11)

        # Tiêu đề chính
        ctk.CTkLabel(self, text="HỆ THỐNG TỰ ĐỘNG BACKUP WINDOWS (WIM)", 
                     font=font_tieu_de, text_color="#00E5FF").pack(pady=(15, 10))

        # KHỐI 1: WINRE
        khung_1 = ctk.CTkFrame(self, fg_color="#161F33", corner_radius=8)
        khung_1.pack(fill="x", padx=20, pady=(0, 10))
        
        tieude_1 = ctk.CTkFrame(khung_1, fg_color="transparent")
        tieude_1.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(tieude_1, text="1. Hệ thống lõi WinRE", font=font_muc, text_color="#F8FAFC").pack(side="left")
        self.nhan_winre = ctk.CTkLabel(tieude_1, text="Đang quét...", font=font_muc, text_color="#00E5FF")
        self.nhan_winre.pack(side="right")
        
        nhap_1 = ctk.CTkFrame(khung_1, fg_color="transparent")
        nhap_1.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkEntry(nhap_1, textvariable=self.duong_dan_winre, state="readonly", font=font_chu, 
                     fg_color="#0B0F19", border_color="#2A3B5C", height=28).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(nhap_1, text="📂 Nạp WIM", font=font_chu, width=90, height=28, fg_color="#2A3B5C", hover_color="#3B5284", command=self.chon_winre).pack(side="right")

        # KHỐI 2: NƠI LƯU & TÊN IMAGE (Gộp cho gọn)
        khung_2 = ctk.CTkFrame(self, fg_color="#161F33", corner_radius=8)
        khung_2.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(khung_2, text="2. Nơi xuất file và Tên Image", font=font_muc, text_color="#F8FAFC").pack(anchor="w", padx=10, pady=(10, 5))
        
        nhap_2 = ctk.CTkFrame(khung_2, fg_color="transparent")
        nhap_2.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkEntry(nhap_2, textvariable=self.duong_dan_luu, state="readonly", font=font_chu,
                     fg_color="#0B0F19", border_color="#2A3B5C", height=28).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(nhap_2, text="💾 Chọn Ổ", font=font_chu, width=90, height=28, fg_color="#2A3B5C", hover_color="#3B5284", command=self.chon_noi_luu).pack(side="right")

        khung_nhap_ten = ctk.CTkFrame(khung_2, fg_color="transparent")
        khung_nhap_ten.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(khung_nhap_ten, text="Tên Image:", font=font_chu, text_color="#94A3B8").pack(side="left", padx=(0, 10))
        self.nhap_ten_win = ctk.CTkEntry(khung_nhap_ten, font=font_chu, fg_color="#0B0F19", border_color="#2A3B5C", height=28)
        self.nhap_ten_win.insert(0, "Tên Windows muốn đặt")
        self.nhap_ten_win.pack(side="left", fill="x", expand=True)

        # KHỐI 3: CẤU HÌNH
        khung_3 = ctk.CTkFrame(self, fg_color="#161F33", corner_radius=8)
        khung_3.pack(fill="x", padx=20, pady=(0, 10))
        
        khung_switch = ctk.CTkFrame(khung_3, fg_color="transparent")
        khung_switch.pack(fill="x", padx=10, pady=10)

        self.bien_don_rac = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(khung_switch, text="Dọn rác (DISM + Temp)", variable=self.bien_don_rac, font=font_chu, progress_color="#00E5FF", switch_height=14, switch_width=30).pack(side="left", expand=True, anchor="w")
        
        self.bien_toi_uu = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(khung_switch, text="Tối ưu (Gỡ Bloatware)", variable=self.bien_toi_uu, font=font_chu, progress_color="#00E5FF", switch_height=14, switch_width=30).pack(side="left", expand=True, anchor="w")
        
        self.bien_sysprep = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(khung_switch, text="Chạy Sysprep", variable=self.bien_sysprep, font=("Segoe UI", 12, "bold"), text_color="#F59E0B", progress_color="#F59E0B", switch_height=14, switch_width=30).pack(side="left", expand=True, anchor="w")

        # NHẬT KÝ (LOG) - Ép chiều cao cố định
        self.hop_nhat_ky = ctk.CTkTextbox(self, font=font_log, height=90, fg_color="#040812", text_color="#10B981", corner_radius=8, border_width=1, border_color="#1E293B")
        self.hop_nhat_ky.pack(fill="x", padx=20, pady=(0, 10))
        self.hop_nhat_ky.configure(state="disabled")

        # TIẾN ĐỘ & KÍCH HOẠT
        khung_duoi = ctk.CTkFrame(self, fg_color="transparent")
        khung_duoi.pack(fill="x", padx=20, pady=(0, 15))
        
        khung_trang_thai = ctk.CTkFrame(khung_duoi, fg_color="transparent")
        khung_trang_thai.pack(fill="x", pady=(0, 5))
        
        self.nhan_trang_thai = ctk.CTkLabel(khung_trang_thai, text="Sẵn sàng", font=font_chu, text_color="#94A3B8")
        self.nhan_trang_thai.pack(side="left")
        
        self.nhan_phan_tram = ctk.CTkLabel(khung_trang_thai, text="0%", font=font_muc, text_color="#00E5FF")
        self.nhan_phan_tram.pack(side="right")
        
        self.thanh_tien_do = ctk.CTkProgressBar(khung_duoi, height=10, corner_radius=5, progress_color="#00E5FF", fg_color="#1E293B")
        self.thanh_tien_do.set(0)
        self.thanh_tien_do.pack(fill="x", pady=(0, 10))
        
        self.nut_kich_hoat = ctk.CTkButton(khung_duoi, text="🚀 KHỞI ĐỘNG TIẾN TRÌNH", font=("Segoe UI", 14, "bold"), height=45, corner_radius=8, fg_color="#00ACC1", hover_color="#00838F", text_color="#FFFFFF", command=self.bat_dau)
        self.nut_kich_hoat.pack(fill="x")

    def in_log(self, text):
        self.after(0, self._cap_nhat_log, text)

    def _cap_nhat_log(self, text):
        self.hop_nhat_ky.configure(state="normal")
        thoi_gian = time.strftime("%H:%M:%S")
        self.hop_nhat_ky.insert("end", f"[{thoi_gian}] {text}\n")
        self.hop_nhat_ky.see("end")
        self.hop_nhat_ky.configure(state="disabled")

    def cap_nhat_tien_do(self, phan_tram, text_trang_thai):
        self.after(0, self._cap_nhat_ui, phan_tram, text_trang_thai)

    def _cap_nhat_ui(self, phan_tram, text_trang_thai):
        self.thanh_tien_do.set(phan_tram / 100)
        self.nhan_phan_tram.configure(text=f"{phan_tram}%")
        self.nhan_trang_thai.configure(text=text_trang_thai)

    def kiem_tra_winre(self):
        ket_qua, _ = chay_lenh("reagentc /info")
        if "Enabled" in ket_qua:
            self.nhan_winre.configure(text="✅ Hoạt động", text_color="#10B981")
        else:
            self.nhan_winre.configure(text="❌ Vô hiệu hóa", text_color="#F43F5E")

    def chon_winre(self):
        file = filedialog.askopenfilename(title="Chọn file winre.wim dự phòng", filetypes=[("WinRE WIM", "winre.wim")])
        if file:
            self.duong_dan_winre.set(file.replace("/", "\\"))

    def chon_noi_luu(self):
        file = filedialog.asksaveasfilename(title="Chọn nơi lưu bản WIM", defaultextension=".wim", initialfile=f"Windows_Backup_{time.strftime('%Y%m%d')}.wim", filetypes=[("Windows Image", "*.wim")])
        if file:
            self.duong_dan_luu.set(file.replace("/", "\\"))

    def bat_dau(self):
        if not self.duong_dan_luu.get().strip():
            messagebox.showerror("Lỗi hệ thống", "Chưa xác định phân vùng lưu trữ Backup!")
            return

        self.nut_kich_hoat.configure(state="disabled", fg_color="#475569")
        self.hop_nhat_ky.configure(state="normal")
        self.hop_nhat_ky.delete(1.0, "end")
        self.hop_nhat_ky.configure(state="disabled")
        
        threading.Thread(target=self.kich_ban_nen, daemon=True).start()

    def kich_ban_nen(self):
        try:
            # 1. Phục hồi WinRE
            self.cap_nhat_tien_do(10, "Đang khởi tạo lõi WinRE...")
            kt_winre, _ = chay_lenh("reagentc /info")
            if "Enabled" not in kt_winre and self.duong_dan_winre.get():
                self.in_log("Đang nạp dữ liệu WinRE từ nguồn ngoài...")
                chay_lenh("reagentc /disable")
                target_dir = r"C:\Windows\System32\Recovery"
                os.makedirs(target_dir, exist_ok=True)
                chay_lenh(f'copy /y "{self.duong_dan_winre.get()}" "{target_dir}\\winre.wim"')
                chay_lenh(f'reagentc /setreimage /path {target_dir}')
                chay_lenh("reagentc /enable")

            # 2. Dọn dẹp
            if self.bien_don_rac.get():
                self.cap_nhat_tien_do(30, "Đang dọn dẹp không gian lưu trữ...")
                self.in_log("Khởi động thuật toán DISM Cleanup và dọn dẹp Temp...")
                chay_lenh("dism /online /cleanup-image /startcomponentcleanup /resetbase")
                chay_lenh(r"del /q /f /s %TEMP%\*")
                chay_lenh(r"del /q /f /s C:\Windows\Temp\*")

            # 3. Tối ưu
            if self.bien_toi_uu.get():
                self.cap_nhat_tien_do(50, "Đang tinh chỉnh hệ điều hành...")
                self.in_log("Hủy kích hoạt Hibernate và gỡ bỏ Bloatware...")
                chay_lenh("powercfg /hibernate off")
                ps_debloat = '$apps = "Microsoft.ZuneVideo|Microsoft.ZuneMusic|Microsoft.GetHelp|Microsoft.YourPhone"; Get-AppxPackage -AllUsers | Where-Object { $_.Name -match $apps } | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue'
                chay_lenh(ps_debloat, True)

            # 4. Cấu hình Auto Capture
            self.cap_nhat_tien_do(70, "Thiết lập kịch bản WinRE Auto Capture...")
            chay_lenh("reagentc /disable")
            mnt_dir = r"C:\Offline_Mount"
            chay_lenh(f'rmdir /s /q "{mnt_dir}"')
            os.makedirs(mnt_dir, exist_ok=True)
            
            chay_lenh(f'dism /Mount-Image /ImageFile:"C:\\Windows\\System32\\Recovery\\winre.wim" /Index:1 /MountDir:"{mnt_dir}"')

            drv, rel = os.path.splitdrive(self.duong_dan_luu.get())
            img_name = self.nhap_ten_win.get()
            
            cmd_capture = f"""@echo off
color 0B
title WINDOWS AUTO CAPTURE - CYBER PROTOCOL
echo.
echo    [+] DANG TIEN HANH NEN HE THONG VAO: {self.duong_dan_luu.get()}
echo.
dism /Capture-Image /ImageFile:"{drv}{rel}" /CaptureDir:C:\\ /Name:"{img_name}" /Compress:max /CheckIntegrity
echo.
echo    [!] HOAN TAT! HE THONG SE KHOI DONG LAI SAU 10 GIAY...
del X:\\Windows\\System32\\winpeshl.ini
timeout /t 10
wpeutil reboot
"""
            with open(f"{mnt_dir}\\Windows\\System32\\AutoCapture.cmd", "w", encoding="ascii") as f:
                f.write(cmd_capture)
                
            with open(f"{mnt_dir}\\Windows\\System32\\winpeshl.ini", "w", encoding="ascii") as f:
                f.write("[LaunchApps]\nX:\\Windows\\System32\\AutoCapture.cmd")

            chay_lenh(f'dism /Unmount-Image /MountDir:"{mnt_dir}" /Commit')
            chay_lenh("reagentc /enable")
            chay_lenh("reagentc /boottore")
            self.in_log("✅ Đã chèn lịch trình Capture vào lõi WinRE thành công.")

            # 5. Sysprep
            if self.bien_sysprep.get():
                self.cap_nhat_tien_do(90, "Đang thực thi lệnh Sysprep...")
                self.in_log("CẢNH BÁO: Đang chạy Sysprep Generalize, máy sẽ tắt ngang sau khi xong...")
                chay_lenh(r"C:\Windows\System32\Sysprep\sysprep.exe /generalize /oobe /shutdown /quiet")
            else:
                self.cap_nhat_tien_do(100, "Hoàn thành!")
                self.in_log("Tiến trình hoàn tất. Phát tín hiệu ngắt nguồn (Shutdown)...")
                chay_lenh("shutdown /s /t 5")
                
            self.after(0, lambda: messagebox.showinfo("Hoàn Thành", "Quy trình đã hoàn tất.\nMáy tính sẽ tắt để chuẩn bị khởi động vào WinRE cho tiến trình Capture."))

        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("Lỗi Hệ Thống", f"Phát hiện ngoại lệ:\n{str(e)}"))
            self.after(0, lambda: self.nut_kich_hoat.configure(state="normal", fg_color="#00ACC1"))

if __name__ == "__main__":
    app = CongCuBackupV17_Compact()
    app.mainloop()