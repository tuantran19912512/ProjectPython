import customtkinter as ctk
import subprocess
import sys
import os
import json
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VietToolbox(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VietToolbox - Bảng Điều Khiển")
        
        # 1. ĐỌC FILE CẤU HÌNH TỪ HỆ THỐNG
        try:
            with open('config.json', 'r', encoding='utf-8-sig') as f:
                danh_sach_cong_cu = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", f"Không đọc được file cấu hình!\n{e}")
            danh_sach_cong_cu = []

        # 2. TỰ ĐỘNG TÍNH TOÁN CHIỀU CAO GIAO DIỆN
        chieu_cao_cung = 220  # Chỗ trống cho tiêu đề và nút thoát
        chieu_cao_nut = len(danh_sach_cong_cu) * 65 # Mỗi nút chiếm 65px
        self.geometry(f"500x{chieu_cao_cung + chieu_cao_nut}")
        self.resizable(False, False)

        # Tiêu đề
        self.label_title = ctk.CTkLabel(self, text="VIETTOOLBOX", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00CCFF")
        self.label_title.pack(pady=(30, 5))
        self.label_ver = ctk.CTkLabel(self, text="HỆ THỐNG TỰ ĐỘNG HÓA", font=ctk.CTkFont(size=12), text_color="#555555")
        self.label_ver.pack(pady=(0, 15))

        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=40)

        # 3. VÒNG LẶP TỰ ĐỘNG SINH RA CÁC NÚT BẤM
        for cong_cu in danh_sach_cong_cu:
            self.tao_nut(cong_cu["ten_nut"], cong_cu["mau_sac"], cong_cu["ten_file"])

        self.btn_exit = ctk.CTkButton(self, text="THOÁT", command=self.quit, fg_color="#333333", hover_color="#CF6679", width=120)
        self.btn_exit.pack(pady=20)

    def tao_nut(self, text, color, script):
        btn = ctk.CTkButton(self.frame, text=text, height=50, 
                            font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#1E1E1E", border_color=color, border_width=1,
                            hover_color="#252525",
                            command=lambda: self.thuc_thi_kich_ban(script))
        btn.pack(fill="x", pady=8)

    def thuc_thi_kich_ban(self, script_name):
        if not os.path.exists(script_name):
            messagebox.showerror("Lỗi", f"Không tìm thấy file: {script_name}")
            return
            
        self.withdraw() 
        
        try:
            if script_name.endswith('.ps1'):
                subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", script_name],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, errors='replace',
                    check=True
                )
            else:
                subprocess.run(
                    [sys.executable, script_name], 
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, errors='replace',
                    check=True
                )
        except subprocess.CalledProcessError as e:
            loi_chi_tiet = e.stderr.strip() if e.stderr else "Lỗi không xác định."
            messagebox.showerror("Lỗi kịch bản", f"Mã lỗi: {e.returncode}\n\n[CHI TIẾT LỖI]:\n{loi_chi_tiet}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{e}")
        finally:
            self.deiconify()

if __name__ == "__main__":
    app = VietToolbox()
    app.mainloop()