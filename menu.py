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

        self.title("VietToolbox - Bảng Điều Khiển")
        self.geometry("500x420")
        self.resizable(False, False)

        # Giao diện chữ
        self.label_title = ctk.CTkLabel(self, text="VIETTOOLBOX", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00CCFF")
        self.label_title.pack(pady=(30, 5))
        
        self.label_ver = ctk.CTkLabel(self, text="HỆ THỐNG TỰ ĐỘNG HÓA", font=ctk.CTkFont(size=12), text_color="#555555")
        self.label_ver.pack(pady=(0, 25))

        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=40)

        # Nút bấm chức năng
        self.add_menu_button("1. CÀI ĐẶT WINDOWS TỐI ƯU", "#007ACC", "quickinstall.py")
        self.add_menu_button("2. TRIỂN KHAI OFFICE TỰ ĐỘNG", "#2B579A", "officedeploy.py")

        self.btn_exit = ctk.CTkButton(self, text="THOÁT", command=self.quit, fg_color="#333333", hover_color="#CF6679", width=120)
        self.btn_exit.pack(pady=20)

    def add_menu_button(self, text, color, script):
        btn = ctk.CTkButton(self.frame, text=text, height=50, 
                            font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#1E1E1E", border_color=color, border_width=1,
                            hover_color="#252525",
                            command=lambda: self.launch_task(script))
        btn.pack(fill="x", pady=10)

    def launch_task(self, script_name):
        if not os.path.exists(script_name):
            messagebox.showerror("Lỗi hệ thống", f"Không tìm thấy kịch bản: {script_name}")
            return
            
        # Ẩn giao diện Menu
        self.withdraw() 
        
        try:
            # Tham số tạo cửa sổ CMD hoàn toàn mới biệt lập
            subprocess.run(
                [sys.executable, script_name], 
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                check=True
            )
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Cảnh báo", f"Kịch bản đóng với mã lỗi: {e.returncode}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{e}")
        finally:
            # Chạy xong cửa sổ tự tắt và gọi lại Menu
            self.deiconify()

if __name__ == "__main__":
    app = VietToolbox()
    app.mainloop()