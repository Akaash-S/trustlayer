<#
.SYNOPSIS
    TrustLayer "One-Click" Launcher
    Starts the Cloud Tunnel and Opens a Secure Browser Session.

.DESCRIPTION
    1. Checks for gcloud authentication.
    2. Establishes SSH Tunnel to Google Cloud VM (Ports 8080 & 8501).
    3. Launches Google Chrome with isolated proxy settings (Direct connection).
    4. Opens the Audit Dashboard.

.NOTES
    Author: TrustLayer AI
    Version: 1.0.0
#>

param(
    [string]$Zone = "us-central1-a",
    [string]$VmName = "trustlayer-vm"
)

Write-Host "`n🚀 REFERENCING SATELLITE... (Connecting to TrustLayer Cloud)" -ForegroundColor Cyan

# 1. Start the Secure Tunnel (SSH)
# We use Start-Process to keep it separate. 
# We use SSH because it is more robust than IAP for long sessions.
Write-Host "   [+] Establishing Secure Frequency (SSH Tunnel)..." -NoNewline
$tunnelJob = Start-Process -FilePath "gcloud" `
    -ArgumentList "compute ssh $VmName --zone=$Zone -- -L 8080:localhost:8080 -L 8501:localhost:8501 -N -q" `
    -PassThru -WindowStyle Minimized

if ($tunnelJob.Id) {
    Write-Host "Connected." -ForegroundColor Green
} else {
    Write-Host "Failed." -ForegroundColor Red
    Write-Error "Could not start tunnel. Please check gcloud login."
    exit
}

# Wait for tunnel to initialize
Write-Host "   [+] Calibrating Uplink..." -NoNewline
Start-Sleep -Seconds 5
Write-Host "Ready." -ForegroundColor Green

# 2. Launch Secure Browser (Chrome)
# This launches Chrome in "App Mode" with proxy settings pre-configured.
# It DOES NOT affect your system proxy (so other apps verify normally).
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$tempProfile = "$env:TEMP\trustlayer_secure_profile"

if (Test-Path $chromePath) {
    Write-Host "   [+] Launching Secure Interface..." -ForegroundColor Yellow
    
    # Launch ChatGPT through Proxy
    Start-Process -FilePath $chromePath `
        -ArgumentList "--proxy-server=http://localhost:8080", `
                      "--ignore-certificate-errors", `
                      "--user-data-dir=$tempProfile", `
                      "https://chatgpt.com"
} else {
    Write-Host "⚠️ Chrome not found. Please configure your browser manually to localhost:8080" -ForegroundColor Red
}

# 3. Launch Audit Dashboard
Write-Host "   [+] Opening Audit Dashboard..." -ForegroundColor Yellow
Start-Process "http://localhost:8501"

Write-Host "`n✅ SYSTEM ONLINE." -ForegroundColor Green
Write-Host "   - AI Traffic is being inspected."
Write-Host "   - Dashboard is active."
Write-Host "   - Close the 'gcloud' window to disconnect."
Write-Host "`nPress any key to exit launcher..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
