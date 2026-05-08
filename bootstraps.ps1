
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# =================================================================
# 2. KHAI BÁO MÔI TRƯỜNG & CHỐNG LƯU CACHE (ANTI-CACHE)
# =================================================================
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$workDir = "$env:TEMP\VietToolbox"
if (!(Test-Path $workDir)) { New-Item -ItemType Directory -Path $workDir | Out-Null }
Set-Location $workDir

# Thêm tham số thời gian ?t=... để lừa GitHub luôn tải bản mới nhất
$t = (Get-Date -UFormat %s)
$menuUrl = "https://raw.githubusercontent.com/tuantran19912512/ProjectPython/refs/heads/main/menu.py?t=$t"
$winUrl = "https://raw.githubusercontent.com/tuantran19912512/quickinstallwindows/refs/heads/main/quickinstall.py?t=$t"
$winmanualUrl="https://raw.githubusercontent.com/tuantran19912512/caiwin/refs/heads/main/caiwinv4.ps1=$t"
$officeUrl = "https://raw.githubusercontent.com/tuantran19912512/pythonoffice/refs/heads/main/officedeploy.py?t=$t"
$officeGoogleUrl = "https://raw.githubusercontent.com/tuantran19912512/caioffice/main/officegoogle.ps1?t=$t"


# =================================================================
# 3. GIAO DIỆN TẢI DỮ LIỆU
# =================================================================
[xml]$xamlLoad = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="Hệ Thống" Height="180" Width="450" 
        WindowStartupLocation="CenterScreen" Background="#121212" AllowsTransparency="True" WindowStyle="None">
    <Border BorderBrush="#00CCFF" BorderThickness="1" CornerRadius="10">
        <StackPanel Margin="20">
            <TextBlock Text="VIETTOOLBOX - ĐANG CHUẨN BỊ" Foreground="#00CCFF" 
                       FontSize="16" FontWeight="Bold" HorizontalAlignment="Center" Margin="0,0,0,20"/>
            <ProgressBar Name="ProgBar" Height="15" Minimum="0" Maximum="100" Value="0" 
                         Background="#252525" Foreground="#00CCFF" BorderThickness="0">
                <ProgressBar.Resources>
                    <Style TargetType="Border"><Setter Property="CornerRadius" Value="5"/></Style>
                </ProgressBar.Resources>
            </ProgressBar>
            <TextBlock Name="TxtStatus" Text="Khởi động môi trường..." Foreground="#AAAAAA" 
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
    Update-Progress 10 "Kiểm tra phiên bản Python..."
    Start-Sleep -Milliseconds 500

    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        Update-Progress 20 "Lỗi: Không tìm thấy Python!"
        Start-Sleep -Seconds 3
        $windowLoad.Close()
        exit
    }

    Update-Progress 40 "Cài đặt thư viện giao diện..."
    python -m pip install customtkinter Pillow requests --quiet --disable-pip-version-check

    Update-Progress 70 "Đồng bộ kịch bản từ máy chủ..."
    try {
        # Sử dụng Invoke-RestMethod kết hợp Out-File -Encoding UTF8 
        # để ép hệ thống lưu file chuẩn tiếng Việt (có BOM), sửa triệt để lỗi vỡ font
        Invoke-RestMethod -Uri $menuUrl | Out-File -FilePath "menu.py" -Encoding UTF8
        Invoke-RestMethod -Uri $winUrl | Out-File -FilePath "quickinstall.py" -Encoding UTF8
		Invoke-RestMethod -Uri $winmanualUrl | Out-File -FilePath "caiwinv4.ps1" -Encoding UTF8
        Invoke-RestMethod -Uri $officeUrl | Out-File -FilePath "officedeploy.py" -Encoding UTF8
        Invoke-RestMethod -Uri $officeGoogleUrl | Out-File -FilePath "officegoogle.ps1" -Encoding UTF8

    } catch {
        Update-Progress 80 "Lỗi kết nối máy chủ!"
        Start-Sleep -Seconds 3
        $windowLoad.Close()
        exit
    }

    Update-Progress 100 "Đang bật bảng điều khiển..."
    Start-Sleep -Milliseconds 800
    $windowLoad.Tag = "Success"
    $windowLoad.Close()
})

$windowLoad.ShowDialog() | Out-Null

# =================================================================
# 4. KHỞI CHẠY MENU VÀ ẨN CONSOLE POWER SHELL
# =================================================================
if ($windowLoad.Tag -eq "Success") {
    # Khởi chạy menu bằng pythonw để ẩn hoàn toàn các cửa sổ đen phụ
    Start-Process python -ArgumentList "menu.py" -WindowStyle Hidden
}