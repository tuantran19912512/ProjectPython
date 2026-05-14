if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`"" -Verb RunAs; exit
}

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$workDir = "$env:TEMP\VietToolbox"
if (!(Test-Path $workDir)) { New-Item -ItemType Directory -Path $workDir | Out-Null }
Set-Location $workDir

$t = (Get-Date -UFormat %s)
$menuUrl = "https://raw.githubusercontent.com/tuantran19912512/ProjectPython/main/menu.py?t=$t"
$configUrl = "https://raw.githubusercontent.com/tuantran19912512/ProjectPython/main/config.json?t=$t"

[xml]$xamlLoad = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" Title="Hệ Thống" Height="180" Width="450" WindowStartupLocation="CenterScreen" Background="#121212" AllowsTransparency="True" WindowStyle="None">
    <Border BorderBrush="#00CCFF" BorderThickness="1" CornerRadius="10">
        <StackPanel Margin="20">
            <TextBlock Text="VIETTOOLBOX - ĐANG CHUẨN BỊ" Foreground="#00CCFF" FontSize="16" FontWeight="Bold" HorizontalAlignment="Center" Margin="0,0,0,20"/>
            <ProgressBar Name="ProgBar" Height="15" Minimum="0" Maximum="100" Value="0" Background="#252525" Foreground="#00CCFF" BorderThickness="0"><ProgressBar.Resources><Style TargetType="Border"><Setter Property="CornerRadius" Value="5"/></Style></ProgressBar.Resources></ProgressBar>
            <TextBlock Name="TxtStatus" Text="Đang khởi động..." Foreground="#AAAAAA" FontSize="11" HorizontalAlignment="Center" Margin="0,10,0,0"/>
        </StackPanel>
    </Border>
</Window>
"@

$readerLoad = New-Object System.Xml.XmlNodeReader $xamlLoad; $windowLoad = [Windows.Markup.XamlReader]::Load($readerLoad)
$progBar = $windowLoad.FindName("ProgBar"); $txtStatus = $windowLoad.FindName("TxtStatus")
function Update-Progress ($value, $status) { $progBar.Value = $value; $txtStatus.Text = $status; [System.Windows.Forms.Application]::DoEvents() }

$windowLoad.Add_ContentRendered({
    
    # 1. KIỂM TRA VÀ BỎ QUA FILE ẢO CỦA WINDOWS STORE
    Update-Progress 10 "Kiểm tra môi trường Python..."
    
    $canCaiDat = $true
    $lenhPy = Get-Command python.exe -ErrorAction SilentlyContinue
    
    if ($lenhPy) {
        # Đo kích thước file. Nếu là file ảo của Windows, dung lượng sẽ là 0 byte.
        $duongDanPy = $lenhPy.Source
        if (Test-Path $duongDanPy) {
            $thongTinFile = Get-Item -LiteralPath $duongDanPy
            if ($thongTinFile.Length -gt 0) {
                $canCaiDat = $false
            }
        }
    }

    if ($canCaiDat) {
        Update-Progress 15 "Đang tải thư viện(vui lòng đợi)..."
        $fileCaiDat = "$workDir\python_installer.exe"
        
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe" -OutFile $fileCaiDat -UseBasicParsing
        
        Update-Progress 25 "Đang cài đặt thư viện vào hệ thống..."
        Start-Process -FilePath $fileCaiDat -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait -NoNewWindow
        
        # Làm mới lại biến môi trường, ép hệ thống ưu tiên đường dẫn thật của Python (Machine Path)
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }

    # ĐỂ CHẮC CÚ 100%: Quét lại toàn bộ và lấy đích danh file exe thật (bỏ qua file ảo)
    $pythonThat = "python.exe"
    $tatCaPython = Get-Command python.exe -All -ErrorAction SilentlyContinue
    foreach ($p in $tatCaPython) {
        if ((Get-Item -LiteralPath $p.Source).Length -gt 0) {
            $pythonThat = $p.Source
            break
        }
    }

    # 2. CÀI ĐẶT THƯ VIỆN GIAO DIỆN VÀ PIP (Dùng đúng file thật vừa tìm được)
    Update-Progress 40 "Cài đặt thư viện hỗ trợ (pip)..."
    & $pythonThat -m pip install --upgrade pip --quiet --disable-pip-version-check
    & $pythonThat -m pip install customtkinter Pillow requests --quiet --disable-pip-version-check

    # 3. TẢI CẤU HÌNH BẢNG ĐIỀU KHIỂN
    Update-Progress 60 "Tải cấu hình bảng điều khiển..."
    try {
        Invoke-RestMethod -Uri $menuUrl | Out-File -FilePath "menu.py" -Encoding UTF8
        
        $cau_hinh_text = (Invoke-WebRequest -Uri $configUrl -UseBasicParsing).Content
        [System.IO.File]::WriteAllText("$workDir\config.json", $cau_hinh_text, [System.Text.Encoding]::UTF8)
        
        Update-Progress 80 "Đang đồng bộ các kịch bản cài đặt..."
        $cau_hinh = $cau_hinh_text | ConvertFrom-Json
        
        foreach ($muc in $cau_hinh) {
            $link_kem_chong_cache = $muc.link_tai + "?t=$t"
            Invoke-RestMethod -Uri $link_kem_chong_cache | Out-File -FilePath $muc.ten_file -Encoding UTF8
        }
    } catch {
        $loi_chi_tiet = $_.Exception.Message
        Update-Progress 90 "LỖI: $loi_chi_tiet"
        Start-Sleep -Seconds 10; $windowLoad.Close(); exit
    }

    Update-Progress 100 "Đang bật bảng điều khiển..."
    Start-Sleep -Milliseconds 500; 
    $windowLoad.Tag = $pythonThat; # Ném đường dẫn Python thật ra ngoài
    $windowLoad.Close()
})
$windowLoad.ShowDialog() | Out-Null

# Chạy menu.py bằng đúng đường dẫn Python thật đã lấy từ bên trong GUI
if ($windowLoad.Tag) {
    $khoiChayPython = $windowLoad.Tag
    Start-Process $khoiChayPython -ArgumentList "menu.py" -WindowStyle Hidden
}