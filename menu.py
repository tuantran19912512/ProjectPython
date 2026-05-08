import customtkinter as ctk
import subprocess
import sys
import os
from tkinter import messagebox

# Cấu hình giao diện
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VietToolbox(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VietToolbox - Hệ Thống Điều Khiển")
        self.geometry("500x450")
        self.resizable(False, False)

        # Tiêu đề
        self.label_title = ctk.CTkLabel(self, text="VIETTOOLBOX", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00CCFF")
        self.label_title.pack(pady=(30, 5))
        
        self.label_ver = ctk.CTkLabel(self, text="HỆ THỐNG TỰ ĐỘNG HÓA", font=ctk.CTkFont(size=12), text_color="#555555")
        self.label_ver.pack(pady=(0, 30))

        # Khung chức năng
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=40)

        # Danh sách các nút bấm
        self.add_menu_button("1. CÀI ĐẶT WINDOWS TỐI ƯU", "#007ACC", "quickinstall.py")
        self.add_menu_button("2. TRIỂN KHAI OFFICE TỰ ĐỘNG", "#2B579A", "officedeploy.py")

        # Nút Thoát
        self.btn_exit = ctk.CTkButton(self, text="THOÁT", command=self.quit, fg_color="#333333", hover_color="#CF6679", width=120)
        self.btn_exit.pack(pady=30)

    def add_menu_button(self, text, color, script):
        btn = ctk.CTkButton(self.frame, text=text, height=50, 
                            font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#1E1E1E", border_color=color, border_width=1,
                            hover_color="#252525",
                            command=lambda: self.launch_task(script))
        btn.pack(fill="x", pady=10)

    def launch_task(self, script_name):
        if not os.path.exists(script_name):
            messagebox.showerror("Lỗi", f"Không tìm thấy tệp: {script_name}")
            return
            
        self.withdraw() # Tạm ẩn Menu đi
        
        try:
            # Tham số CREATE_NEW_CONSOLE giúp mở script con trong một cửa sổ CMD mới, nhìn cực kỳ chuyên nghiệp
            subprocess.run(
                [sys.executable, script_name], 
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                check=True
            )
        except Exception as e:
            messagebox.showerror("Lỗi thực thi", f"Có lỗi xảy ra: {e}")
        finally:
            self.deiconify() # Khi cửa sổ CMD của script con đóng lại, Menu sẽ tự động hiện ra

if __name__ == "__main__":
    app = VietToolbox()
    app.mainloop()