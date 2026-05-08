# =================================================================
# 1. TỰ ĐỘNG NÂNG QUYỀN ADMINISTRATOR
# =================================================================
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# =================================================================
# 2. KHAI BÁO THƯ VIỆN & MÔI TRƯỜNG
# =================================================================
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Tạo thư mục làm việc tạm thời
$workDir = "$env:TEMP\VietToolbox"
if (!(Test-Path $workDir)) { New-Item -ItemType Directory -Path $workDir | Out-Null }
Set-Location $workDir

# Các đường link RAW trực tiếp từ GitHub của Tuấn
$menuUrl = "https://raw.githubusercontent.com/tuantran19912512/ProjectPython/refs/heads/main/menu.py"
$winUrl = "https://raw.githubusercontent.com/tuantran19912512/quickinstallwindows/refs/heads/main/quickinstall.py"
$officeUrl = "https://raw.githubusercontent.com/tuantran19912512/pythonoffice/refs/heads/main/officedeploy.py"

# =================================================================
# 3. GIAO DIỆN CỬA SỔ TẢI DỮ LIỆU (LOADING UI)
# =================================================================
[xml]$xamlLoad = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="Khởi tạo hệ thống" Height="180" Width="450" 
        WindowStartupLocation="CenterScreen" Background="#121212" AllowsTransparency="True" WindowStyle="None">
    <Border BorderBrush="#00CCFF" BorderThickness="1" CornerRadius="10">
        <StackPanel Margin="20">
            <TextBlock Name="TxtTitle" Text="VIETTOOLBOX - ĐANG CHUẨN BỊ" Foreground="#00CCFF" 
                       FontSize="16" FontWeight="Bold" HorizontalAlignment="Center" Margin="0,0,0,20"/>
            <ProgressBar Name="ProgBar" Height="15" Minimum="0" Maximum="100" Value="0" 
                         Background="#252525" Foreground="#00CCFF" BorderThickness="0">
                <ProgressBar.Resources>
                    <Style TargetType="Border"><Setter Property="CornerRadius" Value="5"/></Style>
                </ProgressBar.Resources>
            </ProgressBar>
            <TextBlock Name="TxtStatus" Text="Đang khởi động..." Foreground="#AAAAAA" 
                       FontSize="11" HorizontalAlignment="Center" Margin="0,10,0,0"/>
        </StackPanel>
    </Border>
</Window>
"@

$readerLoad = New-Object System.Xml.XmlNodeReader $xamlLoad
$windowLoad = [Windows.Markup.XamlReader]::Load($readerLoad)
$progBar = $windowLoad.FindName("ProgBar")
$txtStatus = $windowLoad.FindName("TxtStatus")

function Update-Progress ($value, $status) {
    $progBar.Value = $value
    $txtStatus.Text = $status
    [System.Windows.Forms.Application]::DoEvents()
}

$windowLoad.Add_ContentRendered({
    Update-Progress 10 "Đang kiểm tra môi trường Python..."
    Start-Sleep -Milliseconds 500

    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        Update-Progress 20 "Lỗi: Không tìm thấy Python trên hệ thống!"
        Start-Sleep -Seconds 3
        $windowLoad.Close()
        exit
    }

    Update-Progress 40 "Đang cài đặt các thư viện hệ thống cần thiết..."
    # Cài trực tiếp customtkinter, Pillow và requests không cần qua file requirements.txt
    python -m pip install customtkinter Pillow requests --quiet --disable-pip-version-check

    Update-Progress 70 "Đang tải mã nguồn từ máy chủ..."
    try {
        # Sử dụng các biến link RAW đã khai báo ở trên
        Invoke-WebRequest -Uri $menuUrl -OutFile "menu.py" -ErrorAction Stop
        Invoke-WebRequest -Uri $winUrl -OutFile "quickinstall.py" -ErrorAction Stop
        Invoke-WebRequest -Uri $officeUrl -OutFile "officedeploy.py" -ErrorAction Stop
    } catch {
        Update-Progress 80 "Lỗi tải file! Vui lòng kiểm tra lại kết nối mạng."
        Start-Sleep -Seconds 3
        $windowLoad.Close()
        exit
    }

    Update-Progress 100 "Hoàn tất! Đang mở bảng điều khiển..."
    Start-Sleep -Milliseconds 800
    $windowLoad.Tag = "Success"
    $windowLoad.Close()
})

$windowLoad.ShowDialog() | Out-Null

# =================================================================
# 4. KHỞI CHẠY MENU CHÍNH
# =================================================================
if ($windowLoad.Tag -eq "Success") {
    Clear-Host
    # Chỉ chạy thẳng menu.py, bỏ dòng thông báo đã sẵn sàng
    python menu.py
}