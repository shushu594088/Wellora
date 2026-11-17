$ErrorActionPreference = 'Continue'
$PSNativeCommandUseErrorActionPreference = $false
$root = (Get-Location).Path
$roles = Join-Path $root 'evidence/transactions/P026-release-readiness'
$source = Join-Path $root 'app/src/main/java/com/nmy/wellora/ui/feature/shared/DemoUi.kt'
$baseline = Join-Path $roles 'BASELINE_FILE.kt'
$modified = Join-Path $roles 'MODIFIED_FILE.kt'
$rollback = Join-Path $roles 'ROLLBACK_COPY.kt'
$baselineOut = Join-Path $roles 'baseline-lint.stdout.txt'
$baselineErr = Join-Path $roles 'baseline-lint.stderr.txt'
$modifiedOut = Join-Path $roles 'modified-lint.stdout.txt'
$modifiedErr = Join-Path $roles 'modified-lint.stderr.txt'
$rollbackOut = Join-Path $roles 'rollback-lint.stdout.txt'
$rollbackErr = Join-Path $roles 'rollback-lint.stderr.txt'
function Hash($Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Run-Lint($Out, $Err) {
    & .\gradlew.bat :app:lintRelease --console=plain 1> $Out 2> $Err
    return $LASTEXITCODE
}
$expectedModifiedHash = Hash $modified
if ((Hash $source) -ne $expectedModifiedHash) { throw 'Working source differs from the recorded MODIFIED_FILE.' }
try {
    [IO.File]::WriteAllBytes($source, [IO.File]::ReadAllBytes($baseline))
    $baseStatus = Run-Lint $baselineOut $baselineErr
    [IO.File]::WriteAllBytes($source, [IO.File]::ReadAllBytes($modified))
    $modStatus = Run-Lint $modifiedOut $modifiedErr
    Copy-Item -LiteralPath $modified -Destination $rollback
    & 'C:\Program Files\Git\bin\bash.exe' (Join-Path $roles 'ROLLBACK.sh') 'evidence/transactions/P026-release-readiness/ROLLBACK_COPY.kt'
    $rollbackStatus = $LASTEXITCODE
    $rollbackHash = Hash $rollback
    if ($rollbackStatus -ne 0 -or $rollbackHash -ne (Hash $baseline)) { throw 'Rollback copy did not restore the exact baseline.' }
    [IO.File]::WriteAllBytes($source, [IO.File]::ReadAllBytes($rollback))
    $rollbackLintStatus = Run-Lint $rollbackOut $rollbackErr
    [IO.File]::WriteAllBytes($source, [IO.File]::ReadAllBytes($modified))
    $restoredHash = Hash $source
    $summary = @"
BASELINE_HASH=$(Hash $baseline)
MODIFIED_HASH=$(Hash $modified)
ROLLBACK_COPY_HASH=$rollbackHash
SOURCE_RESTORED_HASH=$restoredHash
BASELINE_LINT_EXIT=$baseStatus
MODIFIED_LINT_EXIT=$modStatus
ROLLBACK_COPY_SCRIPT_EXIT=$rollbackStatus
ROLLBACK_LINT_EXIT=$rollbackLintStatus
"@
    [IO.File]::WriteAllText((Join-Path $roles 'ROLE_SUMMARY.txt'), $summary, [Text.UTF8Encoding]::new($false))
    if ($restoredHash -ne $expectedModifiedHash) { throw 'Target source was not restored to MODIFIED bytes.' }
    Write-Output $summary
    if ($baseStatus -ne 1 -or $modStatus -ne 0 -or $rollbackLintStatus -ne 1) { exit 1 }
}
finally {
    if ((Test-Path -LiteralPath $modified) -and (Hash $source) -ne $expectedModifiedHash) {
        [IO.File]::WriteAllBytes($source, [IO.File]::ReadAllBytes($modified))
    }
}
