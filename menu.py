import subprocess
import sys
import os

# =================================================================
# TỰ ĐỘNG KIỂM TRA VÀ CÀI ĐẶT THƯ VIỆN THIẾU
# =================================================================
def auto_install_libraries():
    # Danh sách thư viện bên thứ 3 cần cài (pip)
    # Các thư viện như os, sys, re, threading... là mặc định nên không cần cài
    required_external_libs = ["customtkinter", "requests"]
    
    for lib in required_external_libs:
        try:
            __import__(lib)
        except ImportError:
            print(f"[!] Đang thiếu thư viện: {lib}. Tiến hành cài đặt tự động...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--quiet"])
            print(f"[OK] Đã cài đặt thành công: {lib}")

# Chạy kiểm tra trước khi import chính thức
auto_install_libraries()

# =================================================================
# IMPORT THƯ VIỆN CHÍNH
# =================================================================
import customtkinter as ctk
from tkinter import messagebox
import threading

# Cấu hình giao diện Dark Mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VietToolbox(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VietToolbox - IT Support Suite")
        self.geometry("550x450")
        self.resizable(False, False)

        # Header
        self.header = ctk.CTkLabel(self, text="VIETTOOLBOX", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00CCFF")
        self.header.pack(pady=(30, 5))
        
        self.status = ctk.CTkLabel(self, text="Hệ thống đã sẵn sàng", text_color="#4CAF50", font=ctk.CTkFont(size=12))
        self.status.pack(pady=(0, 30))

        # Khung chứa nút bấm
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=50)

        # Nút 1: Windows
        self.btn_win = ctk.CTkButton(self.container, text="1. CÀI ĐẶT WINDOWS TỐI ƯU", 
                                     command=lambda: self.launch_task("quickinstall.py"),
                                     height=55, font=ctk.CTkFont(size=15, weight="bold"),
                                     fg_color="#252525", border_color="#00CCFF", border_width=1)
        self.btn_win.pack(fill="x", pady=10)

        # Nút 2: Office
        self.btn_off = ctk.CTkButton(self.container, text="2. TRIỂN KHAI OFFICE TỰ ĐỘNG", 
                                     command=lambda: self.launch_task("officedeploy.py"),
                                     height=55, font=ctk.CTkFont(size=15, weight="bold"),
                                     fg_color="#252525", border_color="#FF5722", border_width=1)
        self.btn_off.pack(fill="x", pady=10)

        # Nút Thoát
        self.btn_exit = ctk.CTkButton(self, text="THOÁT HỆ THỐNG", command=self.quit,
                                      fg_color="#CF6679", text_color="black", hover_color="#B05566",
                                      font=ctk.CTkFont(weight="bold"))
        self.btn_exit.pack(pady=30)

    def launch_task(self, script_path):
       if not os.path.exists(script_name):
            messagebox.showerror("Lỗi", f"Không tìm thấy file: {script_name}")
            return
            
        self.withdraw() # Ẩn menu đi
        
        try:
            # Chạy script con trực tiếp, không in thông báo thừa
            subprocess.run([sys.executable, script_name], check=True)
        except Exception as e:
            messagebox.showerror("Lỗi thực thi", f"Có lỗi xảy ra: {e}")
        finally:
            # Chạy xong tự động gọi Menu hiện lại luôn
            self.deiconify()

if __name__ == "__main__":
    app = VietToolbox()
    app.mainloop()