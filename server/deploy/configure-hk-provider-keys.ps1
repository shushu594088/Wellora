$ErrorActionPreference = "Stop"

Write-Host "This stores selected DeepSeek/XFYUN settings in the Hong Kong server's private .env."
Write-Host "Do not use or paste any credential previously posted in chat."
$confirmation = Read-Host "After creating fresh provider credentials, type NEW_KEYS to continue"
if ($confirmation -cne "NEW_KEYS") {
    throw "Cancelled. No provider credential was requested or sent."
}

$selection = (Read-Host "Provider(s): DEEPSEEK, XFYUN, or BOTH").Trim().ToUpperInvariant()
if ($selection -notin @("DEEPSEEK", "XFYUN", "BOTH")) {
    throw "Select DEEPSEEK, XFYUN, or BOTH. No credential was requested or sent."
}

$values = [ordered]@{}
$secureValues = [System.Collections.Generic.List[System.Security.SecureString]]::new()

function Read-SecretValue([string]$Prompt) {
    $secure = Read-Host $Prompt -AsSecureString
    $secureValues.Add($secure)
    return [System.Net.NetworkCredential]::new("", $secure).Password
}

if ($selection -in @("DEEPSEEK", "BOTH")) {
    $values.DEEPSEEK_API_KEY = Read-SecretValue "New DeepSeek API key"
    $values.DEEPSEEK_MODEL = Read-Host "DeepSeek model ID (optional; leave blank until confirmed)"
}

if ($selection -in @("XFYUN", "BOTH")) {
    $values.XFYUN_APP_ID = Read-Host "New XFYUN App ID"
    $values.XFYUN_API_KEY = Read-SecretValue "New XFYUN API key"
    $values.XFYUN_API_SECRET = Read-SecretValue "New XFYUN API secret"
    $values.XFYUN_OCR_PRODUCT = Read-Host "XFYUN OCR product ID (optional; leave blank until confirmed)"
    $values.XFYUN_ASR_PRODUCT = Read-Host "XFYUN ASR product ID (optional; leave blank until confirmed)"
}

$missing = @()
foreach ($key in @("DEEPSEEK_API_KEY", "XFYUN_APP_ID", "XFYUN_API_KEY", "XFYUN_API_SECRET")) {
    if ($values.Contains($key) -and [string]::IsNullOrWhiteSpace($values[$key])) { $missing += $key }
}
if ($missing.Count -gt 0) {
    foreach ($key in @("DEEPSEEK_API_KEY", "XFYUN_API_KEY", "XFYUN_API_SECRET")) {
        if ($values.Contains($key)) { $values[$key] = $null }
    }
    throw "Required provider values are missing. No provider configuration was sent."
}

$payload = $values | ConvertTo-Json -Compress
foreach ($key in @("DEEPSEEK_API_KEY", "XFYUN_API_KEY", "XFYUN_API_SECRET")) {
    if ($values.Contains($key)) { $values[$key] = $null }
}
$values.Clear()
$oldOutputEncoding = $OutputEncoding

try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $payload | ssh -T server1 "sudo -n python3 /opt/wellora-hk/server/deploy/configure-hk-provider-keys.py"
    $sshExitCode = $LASTEXITCODE
    $OutputEncoding = $oldOutputEncoding
    if ($sshExitCode -ne 0) {
        throw "Remote provider configuration failed with exit code $sshExitCode. Do not paste credentials into chat."
    }
}
finally {
    $OutputEncoding = $oldOutputEncoding
    $payload = $null
    foreach ($secure in $secureValues) { $secure.Dispose() }
    [GC]::Collect()
}
