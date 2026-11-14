$ErrorActionPreference = "Stop"

Write-Host "This script accepts a fresh least-privilege OSS RAM key only."
Write-Host "Do not use any key previously posted in chat."
$confirmation = Read-Host "After revoking that key, type ROTATED to continue"
if ($confirmation -cne "ROTATED") {
    throw "Cancelled. No credential was requested or sent."
}

$accessKeyIdSecure = Read-Host "New OSS AccessKey ID" -AsSecureString
$accessKeySecretSecure = Read-Host "New OSS AccessKey Secret" -AsSecureString
$accessKeyId = [System.Net.NetworkCredential]::new("", $accessKeyIdSecure).Password
$accessKeySecret = [System.Net.NetworkCredential]::new("", $accessKeySecretSecure).Password
$accessKeyIdSecure.Dispose()
$accessKeySecretSecure.Dispose()

if ([string]::IsNullOrWhiteSpace($accessKeyId) -or [string]::IsNullOrWhiteSpace($accessKeySecret)) {
    $accessKeyId = $null
    $accessKeySecret = $null
    throw "Both new OSS values are required. Nothing was sent."
}

$payload = [ordered]@{
    OSS_REGION = "cn-shanghai"
    OSS_ENDPOINT = "https://oss-cn-shanghai.aliyuncs.com"
    OSS_BUCKET = "oss-pai-nj0fx54125p7y7intd-cn-shanghai"
    OSS_ACCESS_KEY_ID = $accessKeyId
    OSS_ACCESS_KEY_SECRET = $accessKeySecret
} | ConvertTo-Json -Compress
$accessKeyId = $null
$accessKeySecret = $null
$oldOutputEncoding = $OutputEncoding

try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $payload | ssh -T server1 "sudo -n python3 /opt/wellora-hk/server/deploy/configure-hk-oss.py"
    $sshExitCode = $LASTEXITCODE
    $OutputEncoding = $oldOutputEncoding
    if ($sshExitCode -ne 0) {
        throw "Remote configuration failed with exit code $sshExitCode. Do not paste credentials into chat."
    }
}
finally {
    $OutputEncoding = $oldOutputEncoding
    $payload = $null
    [GC]::Collect()
}
