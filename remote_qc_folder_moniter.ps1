# -----------------------------
# PowerShell Folder Watcher Script
# -----------------------------

# Ask user for the subfolder name every time
$subfolder = Read-Host "Enter the subfolder of Remote_QC to watch (e.g., 'Subfolder1')"

# Build the full path to watch
$folderPath = Join-Path "\\SNB-WORKSTATION\Remote_QC\DIIB_QC" $subfolder

if (-not (Test-Path $folderPath)) {
    Write-Host "Folder '$folderPath' does not exist. Exiting."
    exit
}

Write-Host "Watching folder: $folderPath"

# SSH command to run remotely (with unbuffered Python output)
$sshCommand = 'cd C:\Users\MIDAS\Desktop\SCN_Analysis && python -u C:\Users\MIDAS\Desktop\SCN_Analysis\AD_Assessment_QC.py --data_path C:\Users\MIDAS\Desktop\Remote_QC\DIIB_QC --model yolov10l.pt --conf 0.2'

# Create FileSystemWatcher
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $folderPath
$watcher.Filter = "*.*"
$watcher.NotifyFilter = [System.IO.NotifyFilters]'FileName, LastWrite'
$watcher.IncludeSubdirectories = $false  # Watch only the folder itself

# Debounce: only run script once every 10 seconds
$lastRun = Get-Date "2000-01-01"
$cooldown = 10

# Action to take when a new file is created
$action = {
    $now = Get-Date
    if (($now - $lastRun).TotalSeconds -ge $cooldown) {
        $lastRun = $now
        Write-Host "$(Get-Date) - New file detected. Running remote script..."

        try {
            # Run SSH command and capture output
            $output = & ssh MIDAS@192.168.0.1 $sshCommand 2>&1

            # Split output into lines and print each line
            $output -split "`n" | ForEach-Object { Write-Host $_ }
        }
        catch {
            Write-Host "Error running SSH command: $_"
        }

    } 
}

# Register the Created event
Register-ObjectEvent $watcher Created -Action $action

# Keep the script running
Write-Host "Press Ctrl+C to stop."
while ($true) { Start-Sleep 5 }
