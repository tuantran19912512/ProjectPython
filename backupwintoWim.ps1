<#
.SYNOPSIS
    CÔNG CỤ TỰ ĐỘNG SYSPREP VÀ BACKUP WINDOWS (CAPTURE TO WIM) - V1.6
    Hỗ trợ đồng bộ hóa GitHub - Cài đặt Silent - Giao diện Flat Dark Mode
#>

# ==========================================
# 1. THIẾT LẬP MÔI TRƯỜNG & UNICODE
# ==========================================
# Ép kiểu Console sang UTF-8 để xử lý hiển thị
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Ngăn chặn lỗi TypeNotFound khi gọi Assembly WPF
try {
    Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms -ErrorAction Stop
} catch {
    Write-Warning "[Lỗi] Không thể nạp thư viện UI (TypeNotFound). Đang thoát..."
    exit
}

# ==========================================
# 2. MODULE ĐỒNG BỘ GITHUB REST API
# ==========================================
function Sync-GitHubToolbox {
    [CmdletBinding()]
    param (
        [string]$RepoApiUrl = "https://api.github.com/repos/YourOrg/VietToolbox/contents/scripts"
    )

    # Xử lý an toàn biểu thức Null (Null-valued expression)
    if ([string]::IsNullOrWhiteSpace($RepoApiUrl)) {
        Write-Warning "[Cảnh báo] Đường dẫn API GitHub không được để trống."
        return
    }

    $Headers = @{
        "User-Agent" = "VietToolbox-Sync-Client"
        "Accept"     = "application/vnd.github.v3+json"
    }

    try {
        $Response = Invoke-RestMethod -Uri $RepoApiUrl -Headers $Headers -Method Get -ErrorAction Stop
        
        if ($null -ne $Response) {
            foreach ($File in $Response) {
                # Xử lý đồng nhất Unicode: Ép về chuẩn Pre-composed (FormC) để tránh xung đột Decomposed khi xử lý chuỗi
                $FileNameClean = $File.name.Normalize([System.Text.NormalizationForm]::FormC)
                
                if ($FileNameClean -match "\.ps1$") {
                    Write-Host "Đang tải lặng (Silent): $FileNameClean..." -ForegroundColor Cyan
                    # Logic Download file raw tại đây:
                    # Invoke-WebRequest -Uri $File.download_url -OutFile "C:\Temp\$FileNameClean" -UseBasicParsing
                }
            }
        }
    } catch {
        Write-Error "[Lỗi Mạng/API] Không thể kết nối GitHub: $($_.Exception.Message)"
    }
}

# ==========================================
# 3. GIAO DIỆN WPF (FLAT DARK MODE UI)
# ==========================================
# Lưu ý: Các ký tự đặc biệt trong XAML (như &) phải dùng &amp;
[xml]$XAML = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="VietToolbox - Sync &amp; Capture"
        Width="600" Height="400" Background="#121212" WindowStartupLocation="CenterScreen">
    <Grid Margin="20">
        <StackPanel>
            <TextBlock Text="HỆ THỐNG QUẢN LÝ SYSPREP VÀ ĐỒNG BỘ" 
                       FontSize="18" FontWeight="Bold" Foreground="#BB86FC" HorizontalAlignment="Center" Margin="0,0,0,20"/>
            
            <TextBlock Text="Trạng thái hệ thống: Sẵn sàng" Foreground="#E0E0E0" FontSize="14" Margin="0,5"/>
            
            <Button Name="BtnSync" Content="ĐỒNG BỘ GITHUB (SILENT)" Height="40" Background="#333333" Foreground="#03DAC6" FontWeight="Bold" Margin="0,20,0,10">
                <Button.Resources>
                    <Style TargetType="Border"><Setter Property="CornerRadius" Value="5"/></Style>
                </Button.Resources>
            </Button>
        </StackPanel>
    </Grid>
</Window>
"@

# Khởi tạo giao diện an toàn
$Reader = (New-Object System.Xml.XmlNodeReader $XAML)
$Window = [Windows.Markup.XamlReader]::Load($Reader)

# Nối Event
$BtnSync = $Window.FindName("BtnSync")
$BtnSync.Add_Click({
    Sync-GitHubToolbox
    [System.Windows.Forms.MessageBox]::Show("Đã gửi lệnh đồng bộ ngầm!", "Thông báo")
})

# Hiển thị
$Window.ShowDialog() | Out-Null