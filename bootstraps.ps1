# 1. Tự động nâng quyền Administrator
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "--- VIETTOOLBOX: ĐANG KHỞI TẠO HỆ THỐNG ---" -ForegroundColor Cyan

# 2. Kiểm tra Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Lỗi: Máy chưa cài Python. Vui lòng cài Python trước!" -ForegroundColor Red
    Pause; exit
}

# 3. Cài đặt các thư viện mồi (cần thiết để chạy Menu)
Write-Host "Đang chuẩn bị thư viện giao diện..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install customtkinter requests --quiet --disable-pip-version-check

# 4. Tải script từ GitHub (Nếu chưa có)
$baseUrl = "https://raw.githubusercontent.com/tuantran19912512"
Write-Host "Đang đồng bộ dữ liệu từ GitHub..." -ForegroundColor Green

Invoke-WebRequest -Uri "$baseUrl/quickinstallwindows/refs/heads/main/quickinstall.py" -OutFile "quickinstall.py" -ErrorAction SilentlyContinue
Invoke-WebRequest -Uri "$baseUrl/pythonoffice/refs/heads/main/officedeploy.py" -OutFile "officedeploy.py" -ErrorAction SilentlyContinue
# Lưu ý: Tuấn cần đảm bảo file menu.py có sẵn hoặc tải về tương tự

# 5. Gọi Menu chính
Write-Host "Khởi động giao diện điều khiển..." -ForegroundColor Cyan
python menu.py