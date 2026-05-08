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
        
        try:
            # Đọc file với utf-8-sig để chống lỗi tàng hình
            with open('config.json', 'r', encoding='utf-8-sig') as f:
                danh_sach_cong_cu = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", f"Không đọc được file cấu hình!\n{e}")
            danh_sach_cong_cu = []

        chieu_cao_cung = 220 
        chieu_cao_nut = len(danh_sach_cong_cu) * 65
        self.geometry(f"500x{chieu_cao_cung + chieu_cao_nut}")
        self.resizable(False, False)

        self.label_title = ctk.CTkLabel(self, text="VIETTOOLBOX", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00CCFF")
        self.label_title.pack(pady=(30, 5))
        self.label_ver = ctk.CTkLabel(self, text="HỆ THỐNG TỰ ĐỘNG HÓA", font=ctk.CTkFont(size=12), text_color="#555555")
        self.label_ver.pack(pady=(0, 15))

        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=40)

        for cong_cu in danh_sach_cong_cu:
            # Lấy danh sách thư viện từ JSON (nếu không có thì hệ thống tự hiểu là bỏ qua)
            thu_vien_can_cai = cong_cu.get("thu_vien", "")
            self.tao_nut(cong_cu["ten_nut"], cong_cu["mau_sac"], cong_cu["ten_file"], thu_vien_can_cai)

        self.btn_exit = ctk.CTkButton(self, text="THOÁT", command=self.quit, fg_color="#333333", hover_color="#CF6679", width=120)
        self.btn_exit.pack(pady=20)

    def tao_nut(self, text, color, script, thu_vien_can_cai):
        btn = ctk.CTkButton(self.frame, text=text, height=50, 
                            font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#1E1E1E", border_color=color, border_width=1,
                            hover_color="#252525",
                            command=lambda: self.thuc_thi_kich_ban(script, thu_vien_can_cai))
        btn.pack(fill="x", pady=8)

    def thuc_thi_kich_ban(self, script_name, thu_vien_can_cai):
        if not os.path.exists(script_name):
            messagebox.showerror("Lỗi", f"Không tìm thấy file: {script_name}")
            return
            
        self.withdraw() 
        
        try:
            # 1. TỰ ĐỘNG CÀI THƯ VIỆN NGẦM NẾU CÓ YÊU CẦU
            if thu_vien_can_cai:
                danh_sach_tv = thu_vien_can_cai.split() # Tách "psutil selenium" thành mảng
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + danh_sach_tv + ["--quiet", "--disable-pip-version-check"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True
                )

            # 2. CHẠY KỊCH BẢN CHÍNH
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