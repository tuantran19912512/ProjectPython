import customtkinter as ctk
import subprocess
import sys
import os
import json
from tkinter import messagebox

# Thiết lập giao diện tổng thể
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VietToolbox(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VietToolbox - Bảng Điều Khiển")
        
        # Cấu hình kích thước cố định cho Dashboard
        self.geometry("900x550")
        self.resizable(False, False)

        # Thiết lập bố cục chia lưới: 1 Hàng, 2 Cột (Cột 0: Sidebar, Cột 1: Nội dung chính)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Đọc dữ liệu từ cấu hình
        try:
            with open('config.json', 'r', encoding='utf-8-sig') as f:
                danh_sach_cong_cu = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", f"Không đọc được file cấu hình!\n{e}")
            danh_sach_cong_cu = []

        # ==========================================
        # PHẦN 1: THANH BÊN CẠNH (SIDEBAR)
        # ==========================================
        self.khung_ben_trai = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.khung_ben_trai.grid(row=0, column=0, sticky="nsew")
        self.khung_ben_trai.grid_rowconfigure(4, weight=1) # Đẩy nút Thoát xuống đáy

        self.nhan_tieu_de = ctk.CTkLabel(self.khung_ben_trai, text="VIET\nTOOLBOX", 
                                         font=ctk.CTkFont(size=28, weight="bold"), text_color="#00CCFF")
        self.nhan_tieu_de.grid(row=0, column=0, padx=20, pady=(40, 5))

        self.nhan_phien_ban = ctk.CTkLabel(self.khung_ben_trai, text="HỆ THỐNG TỰ ĐỘNG", 
                                           font=ctk.CTkFont(size=12), text_color="#888888")
        self.nhan_phien_ban.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Đường kẻ ngang trang trí
        self.duong_ke = ctk.CTkFrame(self.khung_ben_trai, height=2, fg_color="#333333")
        self.duong_ke.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        self.nut_thoat = ctk.CTkButton(self.khung_ben_trai, text="THOÁT HỆ THỐNG", 
                                       command=self.quit, fg_color="#2A2A2A", 
                                       hover_color="#CF6679", border_width=1, border_color="#CF6679")
        self.nut_thoat.grid(row=5, column=0, padx=20, pady=30)

        # ==========================================
        # PHẦN 2: KHU VỰC CHÍNH (MAIN DASHBOARD)
        # ==========================================
        self.khung_chinh = ctk.CTkFrame(self, fg_color="transparent")
        self.khung_chinh.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.nhan_danh_muc = ctk.CTkLabel(self.khung_chinh, text="Bảng Điều Khiển Chức Năng", 
                                          font=ctk.CTkFont(size=20, weight="bold"))
        self.nhan_danh_muc.pack(anchor="w", pady=(0, 15))

        # Khung cuộn chứa các nút công cụ (Đề phòng có quá nhiều công cụ)
        self.khung_luoi_cong_cu = ctk.CTkScrollableFrame(self.khung_chinh, fg_color="transparent")
        self.khung_luoi_cong_cu.pack(fill="both", expand=True)

        # Cấu hình lưới cho khung cuộn (2 cột)
        self.khung_luoi_cong_cu.grid_columnconfigure((0, 1), weight=1)

        # Vòng lặp rải các nút theo dạng thẻ (Card) lên lưới
        for chi_so, cong_cu in enumerate(danh_sach_cong_cu):
            hang = chi_so // 2  # Chia 2 để xếp 2 thẻ trên 1 hàng
            cot = chi_so % 2
            
            thu_vien_can_cai = cong_cu.get("thu_vien", "")
            self.tao_the_cong_cu(hang, cot, cong_cu["ten_nut"], cong_cu["mau_sac"], cong_cu["ten_file"], thu_vien_can_cai)

    def tao_the_cong_cu(self, hang, cot, van_ban, mau_sac, ten_kich_ban, thu_vien_can_cai):
        """Tạo các nút bấm dạng Thẻ (Tile/Card) cho Dashboard"""
        nut_bam = ctk.CTkButton(
            self.khung_luoi_cong_cu, 
            text=van_ban, 
            height=80, # Chiều cao lớn hơn để giống cái thẻ
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#242424", 
            border_color=mau_sac, 
            border_width=2,
            hover_color="#2A2D2E",
            corner_radius=12,
            command=lambda: self.thuc_thi_kich_ban(ten_kich_ban, thu_vien_can_cai)
        )
        nut_bam.grid(row=hang, column=cot, padx=10, pady=10, sticky="nsew")

    def thuc_thi_kich_ban(self, ten_kich_ban, thu_vien_can_cai):
        if not os.path.exists(ten_kich_ban):
            messagebox.showerror("Lỗi", f"Không tìm thấy file: {ten_kich_ban}")
            return
            
        self.withdraw() 
        
        try:
            # 1. TỰ ĐỘNG CÀI THƯ VIỆN NGẦM NẾU CÓ YÊU CẦU
            if thu_vien_can_cai:
                danh_sach_tv = thu_vien_can_cai.split()
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + danh_sach_tv + ["--quiet", "--disable-pip-version-check"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    check=True
                )

            # 2. CHẠY KỊCH BẢN CHÍNH
            if ten_kich_ban.endswith('.ps1'):
                subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", ten_kich_ban],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    capture_output=True, text=True, errors='replace',
                    check=True
                )
            else:
                subprocess.run(
                    [sys.executable, ten_kich_ban], 
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
    ung_dung = VietToolbox()
    ung_dung.mainloop()