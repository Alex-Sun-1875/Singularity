[CmdletBinding()]
param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$manifestPath = Join-Path $PSScriptRoot 'latest-version-cleanup.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $projectRoot.Equals([IO.Path]::GetFullPath($manifest.root).TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The cleanup manifest belongs to another workspace. No files were removed.'
}
$projectPrefix = $projectRoot + '\'
$keptPaths = @($manifest.preserve_sha256.PSObject.Properties.Name)
foreach ($keptPath in $keptPaths) {
    $absoluteKeptPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $keptPath))
    if (-not (Test-Path -LiteralPath $absoluteKeptPath -PathType Leaf)) { throw "Retained file is missing: $keptPath" }
    $expectedHash = $manifest.preserve_sha256.PSObject.Properties[$keptPath].Value
    if ((Get-FileHash -LiteralPath $absoluteKeptPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
        throw "Retained asset changed since the manifest was reviewed: $keptPath"
    }
}
$verifiedTargets = foreach ($relativeTarget in @($manifest.directories) + @($manifest.files)) {
    $absoluteTarget = [IO.Path]::GetFullPath((Join-Path $projectRoot $relativeTarget))
    if (-not $absoluteTarget.StartsWith($projectPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Target escapes workspace: $relativeTarget" }
    if ($absoluteTarget -eq $projectRoot -or $absoluteTarget -eq (Join-Path $projectRoot '.git') -or $absoluteTarget.StartsWith((Join-Path $projectRoot '.git') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Protected target refused: $relativeTarget"
    }
    foreach ($keptPath in $keptPaths) {
        $absoluteKeptPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $keptPath))
        if ($absoluteKeptPath -eq $absoluteTarget -or $absoluteKeptPath.StartsWith($absoluteTarget + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "A retained asset falls inside target: $relativeTarget"
        }
    }
    if (Test-Path -LiteralPath $absoluteTarget) {
        $item = Get-Item -LiteralPath $absoluteTarget -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked target refused: $relativeTarget" }
        if ($item.PSIsContainer -and @(Get-ChildItem -LiteralPath $absoluteTarget -Force -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -gt 0) {
            throw "Target contains a link: $relativeTarget"
        }
    }
    $absoluteTarget
}
Write-Host "Reviewed plan: $($manifest.removed_file_count) old files, approximately $($manifest.removed_MiB) MiB."
Write-Host "Preserved assets verified: $($keptPaths.Count)."
if (-not $Apply) {
    Write-Host 'DRY RUN: no files removed. Run again with -Apply to execute this exact plan.'
    $verifiedTargets | ForEach-Object { Write-Host $_ }
    exit 0
}
foreach ($absoluteTarget in $verifiedTargets) {
    if (Test-Path -LiteralPath $absoluteTarget -PathType Container) { Remove-Item -LiteralPath $absoluteTarget -Recurse -Force }
    elseif (Test-Path -LiteralPath $absoluteTarget -PathType Leaf) { Remove-Item -LiteralPath $absoluteTarget -Force }
}
foreach ($keptPath in $keptPaths) {
    $absoluteKeptPath = Join-Path $projectRoot $keptPath
    if ((Get-FileHash -LiteralPath $absoluteKeptPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.preserve_sha256.PSObject.Properties[$keptPath].Value) {
        throw "Post-cleanup retained asset verification failed: $keptPath"
    }
}
Write-Host 'Old versions removed; retained asset hashes are unchanged.'
