<#
.SYNOPSIS
    CÔNG CỤ TỰ ĐỘNG SYSPREP & BACKUP WINDOWS (CAPTURE TO WIM) - V1.6
    Chỉnh sửa: Kỹ sư Hệ thống | Ngôn ngữ: Tiếng Việt 100%
#>

# ==========================================
# 1. YÊU CẦU QUYỀN ADMIN & STA
# ==========================================
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms

# ==========================================
# 2. BIẾN TOÀN CỤC (Sử dụng Hashtable đồng bộ)
# ==========================================
$Global:SyncHash = [hashtable]::Synchronized(@{
    Progress = 0
    Log      = ""
    Status   = "Sẵn sàng"
    Finished = $false
    Error    = ""
})

# ==========================================
# 3. GIAO DIỆN WPF - FLAT DARK UI
# ==========================================
[xml]$XAML = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="Auto Sysprep &amp; Capture Tool V1.6"
        Width="720" Height="860" WindowStartupLocation="CenterScreen" Background="#0F172A">
    <DockPanel Margin="20">
        <TextBlock DockPanel.Dock="Top" Text="HỆ THỐNG TỰ ĐỘNG BACKUP WINDOWS (WIM)" 
                   FontSize="20" FontWeight="Bold" Foreground="#F8FAFC" HorizontalAlignment="Center" Margin="0,0,0,20"/>

        <StackPanel DockPanel.Dock="Bottom" Margin="0,15,0,0">
            <Grid Margin="0,0,0,8">
                <TextBlock Name="TxtStatus" Text="Sẵn sàng" FontSize="13" Foreground="#94A3B8"/>
                <TextBlock Name="TxtPercent" Text="0%" FontWeight="Bold" FontSize="14" Foreground="#38BDF8" HorizontalAlignment="Right"/>
            </Grid>
            <ProgressBar Name="ProgressBar" Height="12" Foreground="#38BDF8" Background="#1E293B" BorderThickness="0"/>
            <Button Name="BtnStart" Content="🚀 BẮT ĐẦU QUY TRÌNH" Height="50" 
                    Background="#38BDF8" Foreground="#0F172A" FontSize="16" FontWeight="Bold" Margin="0,15,0,0">
                <Button.Resources>
                    <Style TargetType="Border">
                        <Setter Property="CornerRadius" Value="5"/>
                    </Style>
                </Button.Resources>
            </Button>
        </StackPanel>

        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="*"/>
            </Grid.RowDefinitions>

            <!-- WinRE Section -->
            <Border Grid.Row="0" Background="#1E293B" CornerRadius="8" Padding="15" Margin="0,0,0,12">
                <StackPanel>
                    <Grid>
                        <TextBlock Text="1. Trạng thái WinRE" FontWeight="Bold" Foreground="#F1F5F9"/>
                        <TextBlock Name="TxtWinRE" Text="Đang kiểm tra..." HorizontalAlignment="Right" FontWeight="Bold"/>
                    </Grid>
                    <Grid Margin="0,10,0,0">
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="*"/>
                            <ColumnDefinition Width="100"/>
                        </Grid.ColumnDefinitions>
                        <TextBox Name="TxtWinREPath" IsReadOnly="True" Background="#0F172A" Foreground="#F8FAFC" BorderBrush="#334155" Padding="5"/>
                        <Button Name="BtnSelectWinRE" Grid.Column="1" Content="📂 Chọn WIM" Margin="5,0,0,0" Background="#334155" Foreground="White"/>
                    </Grid>
                </StackPanel>
            </Border>

            <!-- Destination Section -->
            <Border Grid.Row="1" Background="#1E293B" CornerRadius="8" Padding="15" Margin="0,0,0,12">
                <StackPanel>
                    <TextBlock Text="2. Nơi lưu file Backup (.wim)" FontWeight="Bold" Foreground="#F1F5F9" Margin="0,0,0,8"/>
                    <Grid>
                        <Grid.ColumnDefinitions>
                            <ColumnDefinition Width="*"/>
                            <ColumnDefinition Width="100"/>
                        </Grid.ColumnDefinitions>
                        <TextBox Name="TxtSavePath" IsReadOnly="True" Background="#0F172A" Foreground="#F8FAFC" BorderBrush="#334155" Padding="5"/>
                        <Button Name="BtnSelectPath" Grid.Column="1" Content="💾 Chọn ổ" Margin="5,0,0,0" Background="#334155" Foreground="White"/>
                    </Grid>
                </StackPanel>
            </Border>

            <!-- Config Section -->
            <Border Grid.Row="2" Background="#1E293B" CornerRadius="8" Padding="15" Margin="0,0,0,12">
                <StackPanel>
                    <TextBlock Text="3. Cấu hình" FontWeight="Bold" Foreground="#F1F5F9" Margin="0,0,0,10"/>
                    <TextBox Name="TxtImageName" Text="Windows_Professional_Custom" Height="30" Background="#0F172A" Foreground="#F8FAFC" BorderBrush="#334155" Padding="5" Margin="0,0,0,10"/>
                    <CheckBox Name="ChkDeepClean" Content="Dọn dẹp rác hệ thống (DISM + Temp)" IsChecked="True" Foreground="#CBD5E1" Margin="0,0,0,5"/>
                    <CheckBox Name="ChkOptimize" Content="Tối ưu Windows (Bloatware, Hibernate)" IsChecked="True" Foreground="#CBD5E1" Margin="0,0,0,5"/>
                    <CheckBox Name="ChkSysprep" Content="Chạy Sysprep (Generalize + OOBE)" IsChecked="True" Foreground="#F59E0B" FontWeight="Bold"/>
                </StackPanel>
            </Border>

            <!-- Log Section -->
            <Border Grid.Row="3" Background="#020617" CornerRadius="8" Padding="10">
                <TextBox Name="TxtLog" Background="Transparent" Foreground="#10B981" FontFamily="Consolas" FontSize="12"
                         IsReadOnly="True" TextWrapping="Wrap" VerticalScrollBarVisibility="Auto" BorderThickness="0"/>
            </Border>
        </Grid>
    </DockPanel>
</Window>
"@

$Reader = (New-Object System.Xml.XmlNodeReader $XAML)
$Window = [Windows.Markup.XamlReader]::Load($Reader)

# --- BIND CONTROLS ---
$nodes = "TxtWinRE","TxtWinREPath","BtnSelectWinRE","TxtSavePath","BtnSelectPath","TxtImageName","ChkDeepClean","ChkOptimize","ChkSysprep","TxtLog","TxtStatus","TxtPercent","ProgressBar","BtnStart"
foreach ($name in $nodes) { Set-Variable -Name $name -Value $Window.FindName($name) }

# ==========================================
# 4. LOGIC KIỂM TRA HỆ THỐNG
# ==========================================
function Test-WinREStatus {
    $info = reagentc /info
    if ($info -match "Enabled") {
        $TxtWinRE.Text = "✅ Hoạt động"; $TxtWinRE.Foreground = "#10B981"
    } else {
        $TxtWinRE.Text = "❌ Vô hiệu"; $TxtWinRE.Foreground = "#EF4444"
    }
}
Test-WinREStatus

$BtnSelectWinRE.Add_Click({
    $ofd = New-Object System.Windows.Forms.OpenFileDialog
    $ofd.Filter = "WinRE WIM|winre.wim"
    if ($ofd.ShowDialog() -eq "OK") { $TxtWinREPath.Text = $ofd.FileName }
})

$BtnSelectPath.Add_Click({
    $sfd = New-Object System.Windows.Forms.SaveFileDialog
    $sfd.Filter = "Windows Image (*.wim)|*.wim"
    $sfd.FileName = "Windows_Backup_$(Get-Date -Format 'yyyyMMdd').wim"
    if ($sfd.ShowDialog() -eq "OK") { $TxtSavePath.Text = $sfd.FileName }
})

# ==========================================
# 5. TIMER CẬP NHẬT UI
# ==========================================
$Timer = New-Object System.Windows.Threading.DispatcherTimer
$Timer.Interval = [TimeSpan]::FromMilliseconds(200)
$Timer.Add_Tick({
    if ($SyncHash.Log) {
        $TxtLog.AppendText($SyncHash.Log)
        $TxtLog.ScrollToEnd()
        $SyncHash.Log = ""
    }
    $ProgressBar.Value = $SyncHash.Progress
    $TxtPercent.Text = "$($SyncHash.Progress)%"
    $TxtStatus.Text = $SyncHash.Status

    if ($SyncHash.Finished) {
        $Timer.Stop()
        if ($SyncHash.Error) {
            [System.Windows.Forms.MessageBox]::Show("Lỗi: $($SyncHash.Error)", "Thông báo")
            $BtnStart.IsEnabled = $true
        } else {
            [System.Windows.Forms.MessageBox]::Show("Quy trình hoàn tất. Máy sẽ tắt để thực hiện Capture khi khởi động lại.", "Thành công")
            Stop-Computer -Force
        }
    }
})
$Timer.Start()

# ==========================================
# 6. LUỒNG XỬ LÝ NGẦM (BACKGROUND WORKER)
# ==========================================
$MainScript = {
    param($Sync, $SavePath, $ImgName, $DoClean, $DoOpt, $DoSys, $WinREFile)

    function Log($m) { $Sync.Log += "[$(Get-Date -Format 'HH:mm:ss')] $m`r`n" }

    try {
        # 1. Phục hồi WinRE nếu cần
        $Sync.Status = "Đang xử lý WinRE..."; $Sync.Progress = 10
        if ((reagentc /info) -notmatch "Enabled" -and $WinREFile) {
            Log "Đang nạp file WinRE từ nguồn ngoài..."
            reagentc /disable | Out-Null
            $target = "C:\Windows\System32\Recovery"
            if (-not (Test-Path $target)) { New-Item -ItemType Directory -Path $target }
            Copy-Item $WinREFile "$target\winre.wim" -Force
            reagentc /setreimage /path $target | Out-Null
            reagentc /enable | Out-Null
        }

        # 2. Dọn dẹp
        if ($DoClean) {
            $Sync.Status = "Đang dọn dẹp hệ thống..."; $Sync.Progress = 30
            Log "Đang chạy DISM Cleanup và xóa Temp..."
            dism /online /cleanup-image /startcomponentcleanup /resetbase | Out-Null
            $paths = @("$env:TEMP\*", "C:\Windows\Temp\*")
            foreach ($p in $paths) { Get-ChildItem $p -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }
        }

        # 3. Tối ưu
        if ($DoOpt) {
            $Sync.Status = "Đang tối ưu hóa..."; $Sync.Progress = 50
            Log "Tắt Hibernate và gỡ Bloatware..."
            powercfg /hibernate off | Out-Null
            $apps = "Microsoft.ZuneVideo|Microsoft.ZuneMusic|Microsoft.GetHelp|Microsoft.YourPhone"
            Get-AppxPackage -AllUsers | Where-Object { $_.Name -match $apps } | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue
        }

        # 4. Cấu hình Auto Capture trong WinRE
        $Sync.Status = "Cấu hình WinRE Auto Capture..."; $Sync.Progress = 70
        reagentc /disable | Out-Null
        $mnt = "C:\Offline_Mount"
        if (Test-Path $mnt) { Remove-Item $mnt -Recurse -Force }
        New-Item $mnt -ItemType Directory | Out-Null
        
        dism /Mount-Image /ImageFile:"C:\Windows\System32\Recovery\winre.wim" /Index:1 /MountDir:$mnt | Out-Null

        # Tạo script Capture tối ưu (Sửa lỗi đọc biến set /p)
        $drv = [System.IO.Path]::GetPathRoot($SavePath)
        $rel = $SavePath.Substring($drv.Length)
        
        $cmd = @"
@echo off
title WINDOWS AUTO CAPTURE
echo Dang tien hanh Capture o C: vao $SavePath
dism /Capture-Image /ImageFile:"$drv$rel" /CaptureDir:C:\ /Name:"$ImgName" /Compress:max /CheckIntegrity
echo Hoan tat! May se khoi dong lai trong 10 giay...
del X:\Windows\System32\winpeshl.ini
timeout /t 10
wpeutil reboot
"@
        $cmd | Out-File "$mnt\Windows\System32\AutoCapture.cmd" -Encoding ascii -Force
        "[LaunchApps]`r`nX:\Windows\System32\AutoCapture.cmd" | Out-File "$mnt\Windows\System32\winpeshl.ini" -Encoding ascii -Force

        dism /Unmount-Image /MountDir:$mnt /Commit | Out-Null
        reagentc /enable | Out-Null
        reagentc /boottore | Out-Null
        Log "✅ Đã nạp lịch trình Capture vào WinRE."

        # 5. Sysprep
        if ($DoSys) {
            $Sync.Status = "Đang chạy Sysprep..."; $Sync.Progress = 90
            Log "Hệ thống đang thực hiện Sysprep Generalize..."
            Start-Process "C:\Windows\System32\Sysprep\sysprep.exe" -ArgumentList "/generalize /oobe /shutdown /quiet" -Wait
        }
        
        $Sync.Progress = 100
        $Sync.Finished = $true
    } catch {
        $Sync.Error = $_.Exception.Message
        $Sync.Finished = $true
    }
}

# ==========================================
# 7. KHỞI CHẠY
# ==========================================
$BtnStart.Add_Click({
    if ([string]::IsNullOrWhiteSpace($TxtSavePath.Text)) { return }
    $BtnStart.IsEnabled = $false
    
    $rs = [runspacefactory]::CreateRunspace()
    $rs.ApartmentState = "STA"; $rs.Open()
    $ps = [powershell]::Create().AddScript($MainScript)
    $ps.AddArgument($Global:SyncHash)
    $ps.AddArgument($TxtSavePath.Text)
    $ps.AddArgument($TxtImageName.Text)
    $ps.AddArgument($ChkDeepClean.IsChecked)
    $ps.AddArgument($ChkOptimize.IsChecked)
    $ps.AddArgument($ChkSysprep.IsChecked)
    $ps.AddArgument($TxtWinREPath.Text)
    $ps.Runspace = $rs
    $ps.BeginInvoke()
})

$Window.ShowDialog() | Out-Null