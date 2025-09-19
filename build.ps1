param(
    [switch]$EmbedConfig = $true,
    [string]$ConfigPath = "config.json",
    [string]$Python = "py",
    [switch]$RecreateVenv = $false,
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
Write-Info "Project root: $root"

# 1) Setup venv
$venvActivate = Join-Path $root ".venv/Scripts/Activate.ps1"
if ($RecreateVenv -or -not (Test-Path $venvActivate)) {
    Write-Info "Creating virtual environment (.venv)"
    & $Python -m venv .venv
}
. $venvActivate
Write-Info "Upgrading pip and installing requirements"
python -m pip install -U pip
pip install -r requirements.txt

# 2) Optionally embed config into shared/config_loader.py (temporary patch)
$cfgLoaderPath = Join-Path $root "shared/config_loader.py"
$backupPath    = "$cfgLoaderPath.bak"
$modified = $false

try {
    if ($EmbedConfig -and (Test-Path $ConfigPath)) {
        Write-Info "Embedding config from '$ConfigPath' into config_loader.py (temporary)"
        $cfgRaw = Get-Content -Raw -Path $ConfigPath -Encoding UTF8
        try {
            $cfg = $cfgRaw | ConvertFrom-Json
        } catch {
            Write-Err "Failed to parse $ConfigPath as JSON"; throw
        }

        # Build minimal embed object with only present keys
        $embed = @{}
        foreach ($key in @("LAUNCHDARKLY_API_KEY", "PROJECT_KEY", "GITHUB_TOKEN", "LOG_FILE", "HISTORY_FILE")) {
            if ($cfg.PSObject.Properties.Match($key).Count -gt 0) {
                $val = [string]$cfg.$key
                if ($null -ne $val -and $val.Length -gt 0) { $embed[$key] = $val }
            }
        }
        if ($embed.Count -eq 0) {
            Write-Warn "No recognized keys found in $ConfigPath. Skipping embed."
        } else {
            $embedJson = ($embed | ConvertTo-Json -Compress)
            $embedBlock = @"
# --- BEGIN EMBEDDED CONFIG (auto-injected by build.ps1; INTERNAL USE ONLY) ---
import json as _json
try:
    _EMBED_CFG = _json.loads("""$embedJson""")
    if not LAUNCHDARKLY_API_KEY:
        LAUNCHDARKLY_API_KEY = _EMBED_CFG.get("LAUNCHDARKLY_API_KEY", LAUNCHDARKLY_API_KEY)
    if not PROJECT_KEY:
        PROJECT_KEY = _EMBED_CFG.get("PROJECT_KEY", PROJECT_KEY)
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = _EMBED_CFG.get("GITHUB_TOKEN", GITHUB_TOKEN)
    if not LOG_FILE:
        LOG_FILE = _EMBED_CFG.get("LOG_FILE", LOG_FILE)
    if not HISTORY_FILE:
        HISTORY_FILE = _EMBED_CFG.get("HISTORY_FILE", HISTORY_FILE)
except Exception:
    pass
# --- END EMBEDDED CONFIG ---
"@

            $content = Get-Content -Raw -Path $cfgLoaderPath -Encoding UTF8
            $marker = "# Final sanity: keep types consistent"
            if ($content.Contains($marker)) {
                $newContent = $content -replace [regex]::Escape($marker), ("$embedBlock`r`n$marker")
            } else {
                $newContent = "$content`r`n$embedBlock"
            }
            Copy-Item -Path $cfgLoaderPath -Destination $backupPath -Force
            Set-Content -Path $cfgLoaderPath -Value $newContent -Encoding UTF8
            $modified = $true
        }
    } else {
        if ($EmbedConfig) { Write-Warn "Config file '$ConfigPath' not found. Proceeding without embed." }
    }

    # 3) Optional clean
    if ($Clean) {
        Write-Info "Cleaning build artifacts"
        if (Test-Path (Join-Path $root "build")) { Remove-Item -Recurse -Force (Join-Path $root "build") }
        if (Test-Path (Join-Path $root "dist"))  { Remove-Item -Recurse -Force (Join-Path $root "dist") }
        Get-ChildItem $root -Filter "*.spec" | ForEach-Object { Remove-Item -Force $_.FullName }
    }

    # 4) Build
    Write-Info "Starting build via build_exe.py"
    & $Python build_exe.py
    Write-Info "Build finished. EXE path: dist/FeatureFlagManager.exe"

} finally {
    # Restore original file if modified
    if ($modified -and (Test-Path $backupPath)) {
        Write-Info "Restoring original shared/config_loader.py"
        Move-Item -Force -Path $backupPath -Destination $cfgLoaderPath
    }
}
