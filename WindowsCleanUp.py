import os
import shutil
import ctypes
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

def kiem_tra_quyen_quan_tri():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def tu_dong_nang_quyen():
    if not kiem_tra_quyen_quan_tri():
        duong_dan_file = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{duong_dan_file}"', None, 1)
        sys.exit()

tu_dong_nang_quyen()

# --- LỚP GIAO DIỆN CHÍNH (FLAT & DARK MODE CÓ LOG) ---
class UngDungDonDep:
    def __init__(self, root):
        self.root = root
        self.root.title("Công Cụ Dọn Dẹp Hệ Thống")
        self.root.geometry("500x480")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=20, background="#0078D7", troughcolor="#333333", bordercolor="#1e1e1e")

        tk.Label(root, text="TỐI ƯU HỆ THỐNG TOÀN DIỆN", font=("Segoe UI", 12, "bold"), bg="#1e1e1e", fg="white").pack(pady=(15, 5))
        
        self.nhan_trang_thai = tk.Label(root, text="Trạng thái: Sẵn sàng.", font=("Segoe UI", 9), bg="#1e1e1e", fg="#cccccc")
        self.nhan_trang_thai.pack(anchor="w", padx=20, pady=(5, 5))

        self.thanh_tien_trinh = ttk.Progressbar(root, style="TProgressbar", orient="horizontal", length=460, mode="determinate")
        self.thanh_tien_trinh.pack(padx=20, pady=5)

        self.nut_chay = tk.Button(root, text="BẮT ĐẦU DỌN DẸP", font=("Segoe UI", 9, "bold"), bg="#2d2d30", fg="white", 
                                  activebackground="#0078D7", activeforeground="white", relief="flat", bd=0, 
                                  command=self.bat_dau_luong_don_dep)
        self.nut_chay.pack(pady=10, ipadx=10, ipady=5)

        # Khung Log hiển thị tiến trình
        self.hop_log = scrolledtext.ScrolledText(root, width=55, height=12, bg="#141414", fg="#d4d4d4", 
                                                 font=("Consolas", 9), relief="flat", state="disabled")
        self.hop_log.pack(padx=20, pady=(5, 15), fill="both", expand=True)

    def ghi_log(self, noi_dung):
        """Hàm cập nhật text vào khung Log an toàn từ Thread"""
        def cap_nhat():
            self.hop_log.config(state="normal")
            # Đã sửa lại định dạng chuẩn: Giờ:Phút:Giây
            thoi_gian = datetime.now().strftime("%H:%M:%S")
            self.hop_log.insert(tk.END, f"[{thoi_gian}] {noi_dung}\n")
            self.hop_log.see(tk.END) # Tự động cuộn xuống dòng mới nhất
            self.hop_log.config(state="disabled")
        self.root.after(0, cap_nhat)

    def cap_nhat_ui(self, phan_tram, cau_trang_thai):
        self.thanh_tien_trinh["value"] = phan_tram
        self.nhan_trang_thai.config(text=f"Trạng thái: {cau_trang_thai}")

    def bat_dau_luong_don_dep(self):
        self.nut_chay.config(state="disabled", text="ĐANG XỬ LÝ...")
        self.hop_log.config(state="normal")
        self.hop_log.delete(1.0, tk.END)
        self.hop_log.config(state="disabled")
        
        luong_xu_ly = threading.Thread(target=self.thuc_thi_don_dep)
        luong_xu_ly.daemon = True
        luong_xu_ly.start()

    def thuc_thi_don_dep(self):
        try:
            self.ghi_log("Bắt đầu tiến trình dọn dẹp hệ thống...")

            # Bước 1
            self.root.after(0, self.cap_nhat_ui, 10, "Đang chạy Disk Cleanup (Dọn rác ổ đĩa)...")
            self.ghi_log("Gọi công cụ Disk Cleanup (cleanmgr.exe /autoclean)")
            subprocess.run(["cleanmgr.exe", "/autoclean"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.ghi_log("Hoàn thành Disk Cleanup.")

            # Bước 2
            self.root.after(0, self.cap_nhat_ui, 40, "Đang làm sạch các thư mục tạm...")
            thu_muc_rac = [
                os.environ.get('TEMP'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Prefetch'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'SoftwareDistribution', 'Download')
            ]
            for thu_muc in thu_muc_rac:
                if thu_muc and os.path.exists(thu_muc):
                    self.ghi_log(f"Đang quét và xóa: {thu_muc}")
                    for ten_file in os.listdir(thu_muc):
                        duong_dan = os.path.join(thu_muc, ten_file)
                        try:
                            if os.path.isfile(duong_dan) or os.path.islink(duong_dan):
                                os.unlink(duong_dan)
                            elif os.path.isdir(duong_dan):
                                shutil.rmtree(duong_dan)
                        except:
                            pass

            # Bước 3
            self.root.after(0, self.cap_nhat_ui, 60, "Đang dọn dẹp Thùng rác...")
            self.ghi_log("Đang làm sạch Thùng rác (Recycle Bin)...")
            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            except:
                pass

            # Bước 4
            self.root.after(0, self.cap_nhat_ui, 70, "Đang dọn sâu WinSxS...")
            self.ghi_log("Bắt đầu dọn dẹp DISM (Component Cleanup)... Vui lòng chờ...")
            subprocess.run(["DISM.exe", "/Online", "/Cleanup-Image", "/StartComponentCleanup"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.ghi_log("Hoàn thành dọn dẹp DISM.")

            # Hoàn tất
            self.ghi_log("TIẾN TRÌNH TỐI ƯU ĐÃ HOÀN TẤT THÀNH CÔNG.")
            self.root.after(0, self.cap_nhat_ui, 100, "Hoàn tất! Hệ thống đã được tối ưu.")
            self.root.after(0, lambda: messagebox.showinfo("Thông báo", "Quá trình dọn dẹp đã hoàn tất thành công!"))
            self.root.after(0, lambda: self.nut_chay.config(text="ĐÃ HOÀN TẤT"))
        
        except Exception as e:
            self.ghi_log(f"Đã xảy ra lỗi: {str(e)}")
            self.root.after(0, self.cap_nhat_ui, 0, "Quá trình bị gián đoạn do lỗi.")
            self.root.after(0, lambda: self.nut_chay.config(state="normal", text="THỬ LẠI"))

if __name__ == "__main__":
    cua_so_chinh = tk.Tk()
    ung_dung = UngDungDonDep(cua_so_chinh)
    cua_so_chinh.mainloop()