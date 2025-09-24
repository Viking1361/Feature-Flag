<#
Validate GitHub API access for a repository using a Personal Access Token (PAT).
This script checks:
  1) Token identity (GET /user)
  2) Repository visibility (GET /repos/{owner}/{repo})
  3) Releases list (GET /repos/{owner}/{repo}/releases)
  4) Latest release (GET /repos/{owner}/{repo}/releases/latest) with fallback to list

USAGE EXAMPLES (PowerShell):
  # Using a parameter
  .\scripts\validate_github_api.ps1 -Owner "Viking1361" -Repo "Feature-Flag" -Pat "<YOUR_PAT>"

  # Using environment variable
  $env:GITHUB_TOKEN = "<YOUR_PAT>"
  .\scripts\validate_github_api.ps1 -Owner "Viking1361" -Repo "Feature-Flag"

Notes:
- Do NOT paste or print your PAT to the console. The script will not echo it.
- Prefer a Classic PAT with 'repo' scope, or fine-grained with access to the repo and Contents:Read, Metadata:Read.
- ASCII-only output to avoid encoding issues in logs.
#>

param(
  [string]$Owner = "Viking1361",
  [string]$Repo  = "Feature-Flag",
  [string]$Pat,
  [switch]$VerboseOutput
)

# Ensure TLS 1.2
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

function Get-PlainFromSecureString([Security.SecureString]$sec) {
  if (-not $sec) { return $null }
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringUni($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

function New-GHHeaders([string]$Token) {
  $h = @{
    Accept       = "application/vnd.github+json"
    "User-Agent" = "FeatureFlagValidator/1.0"
  }
  if ($Token) { $h["Authorization"] = "token $Token" }
  return $h
}

function Invoke-GH([string]$Uri, [hashtable]$Headers) {
  try {
    if ($VerboseOutput) { Write-Host "GET $Uri" -ForegroundColor DarkGray }
    return Invoke-RestMethod -Uri $Uri -Headers $Headers -Method GET -ErrorAction Stop
  } catch {
    $status = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
      $status = [int]$_.Exception.Response.StatusCode
    }
    if ($status -eq $null) { $status = "unknown" }
    $msg = ("HTTP error {0} for {1}: {2}" -f $status, $Uri, $_.Exception.Message)
    throw [System.Exception]::new($msg)
  }
}

# --- Resolve token ---
if (-not $Pat) { $Pat = $env:GITHUB_TOKEN }
if (-not $Pat) {
  Write-Host "No token provided by -Pat or env:GITHUB_TOKEN. Prompting..." -ForegroundColor Yellow
  $sec = Read-Host -AsSecureString -Prompt "Enter GitHub PAT (input hidden)"
  $Pat = Get-PlainFromSecureString $sec
}

if (-not $Pat) { Write-Error "No token provided. Aborting."; exit 2 }

$headers = New-GHHeaders -Token $Pat

Write-Host "=== Step 1: Token identity (/user) ===" -ForegroundColor Cyan
try {
  $userResp = Invoke-GH -Uri "https://api.github.com/user" -Headers $headers
  Write-Host ("OK: Authenticated as '{0}' (id {1})" -f $userResp.login, $userResp.id) -ForegroundColor Green
} catch {
  Write-Error $_.Exception.Message
  Write-Host "Hint: Ensure PAT is valid, not expired, and SSO-authorized if needed." -ForegroundColor Yellow
  exit 2
}

Write-Host "=== Step 2: Repository visibility ===" -ForegroundColor Cyan
$repoUri = "https://api.github.com/repos/$Owner/$Repo"
try {
  $repoResp = Invoke-GH -Uri $repoUri -Headers $headers
  $priv = if ($repoResp.private) { "private" } else { "public" }
  Write-Host ("OK: Repo visible: {0}/{1} ({2})" -f $Owner, $Repo, $priv) -ForegroundColor Green
} catch {
  Write-Error $_.Exception.Message
  Write-Host "Hint: Token must have access to this repository. For fine-grained PAT, grant explicit repo access and Contents:Read, Metadata:Read." -ForegroundColor Yellow
  exit 3
}

Write-Host "=== Step 3: Releases list ===" -ForegroundColor Cyan
$releasesUri = "https://api.github.com/repos/$Owner/$Repo/releases?per_page=5"
try {
  $rels = Invoke-GH -Uri $releasesUri -Headers $headers
  if (-not $rels -or $rels.Count -eq 0) {
    Write-Host "No releases found (array empty)." -ForegroundColor Yellow
  } else {
    $tags = ($rels | ForEach-Object { $_.tag_name }) -join ", "
    Write-Host ("OK: Found releases: {0}" -f $tags) -ForegroundColor Green
  }
} catch {
  Write-Error $_.Exception.Message
  Write-Host "Hint: If this 404s, the token may not have release read permissions." -ForegroundColor Yellow
}

Write-Host "=== Step 4: Latest release ===" -ForegroundColor Cyan
$latestUri = "https://api.github.com/repos/$Owner/$Repo/releases/latest"
$latest = $null
try {
  $latest = Invoke-GH -Uri $latestUri -Headers $headers
  Write-Host ("OK: Latest release tag: {0}" -f $latest.tag_name) -ForegroundColor Green
} catch {
  Write-Host ("WARN: /releases/latest failed: {0}" -f $_.Exception.Message) -ForegroundColor Yellow
  # Fallback: query list and pick the latest published
  try {
    $rels2 = Invoke-GH -Uri $releasesUri -Headers $headers
    if ($rels2 -and $rels2.Count -gt 0) {
      $latest = $rels2 | Sort-Object {[datetime]$_.published_at} -Descending | Select-Object -First 1
      if ($latest) {
        Write-Host ("OK: Fallback picked latest published: {0}" -f $latest.tag_name) -ForegroundColor Green
      } else {
        Write-Host "No published releases found in list." -ForegroundColor Yellow
      }
    } else {
      Write-Host "No releases found to fallback." -ForegroundColor Yellow
    }
  } catch {
    Write-Error ("Fallback list failed: {0}" -f $_.Exception.Message)
  }
}

Write-Host "=== Summary ===" -ForegroundColor Cyan
if ($latest) {
  Write-Host ("Repo: {0}/{1}" -f $Owner, $Repo)
  Write-Host ("Latest: {0}" -f $latest.tag_name)
  if ($latest.assets) {
    $exe = $latest.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1
    if ($exe) {
      Write-Host ("Asset: {0} (size {1} bytes)" -f $exe.name, $exe.size)
      Write-Host ("Asset API URL: {0}" -f $exe.url)
      Write-Host ("Browser URL: {0}" -f $exe.browser_download_url)
    } else {
      Write-Host "No .exe asset found in latest release." -ForegroundColor Yellow
    }
  }
} else {
  Write-Host "Latest release not resolved." -ForegroundColor Yellow
}
