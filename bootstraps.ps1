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
    Update-Progress 20 "Cài đặt thư viện giao diện..."
    python -m pip install customtkinter Pillow requests --quiet --disable-pip-version-check

    Update-Progress 40 "Tải cấu hình bảng điều khiển..."
    try {
        Invoke-RestMethod -Uri $menuUrl | Out-File -FilePath "menu.py" -Encoding UTF8
        Invoke-RestMethod -Uri $configUrl | Out-File -FilePath "config.json" -Encoding UTF8
        
        Update-Progress 60 "Đang đồng bộ các kịch bản cài đặt..."
        $cau_hinh = Get-Content -Raw -Path "config.json" -Encoding UTF8 | ConvertFrom-Json
        
        # Đã fix chữ "trong" thành "in" ở dòng này
        foreach ($muc in $cau_hinh) {
            $link_kem_chong_cache = $muc.link_tai + "?t=$t"
            Invoke-RestMethod -Uri $link_kem_chong_cache | Out-File -FilePath $muc.ten_file -Encoding UTF8
        }
   } catch {
        # Bắt và in ra lỗi chi tiết từ hệ thống
        $loi_chi_tiet = $_.Exception.Message
        Update-Progress 80 "LỖI: $loi_chi_tiet"
        
        # Tăng thời gian chờ lên 10 giây để Tuấn kịp đọc chữ
        Start-Sleep -Seconds 10
        $windowLoad.Close()
        exit
    }

    Update-Progress 100 "Đang bật bảng điều khiển..."
    Start-Sleep -Milliseconds 500; $windowLoad.Tag = "Success"; $windowLoad.Close()
})
$windowLoad.ShowDialog() | Out-Null

if ($windowLoad.Tag -eq "Success") {
    Start-Process python -ArgumentList "menu.py" -WindowStyle Hidden
}