$ErrorActionPreference='Stop'
$workspace=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$toolsDir=Join-Path $workspace 'src/.tools'
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
$version='4.5.15'
$name="blender-$version-windows-x64.zip"
$archive=Join-Path $toolsDir $name
$executable=Join-Path $toolsDir "blender-$version-windows-x64/blender.exe"
if (!(Test-Path -LiteralPath $executable)) {
    $checksums=(Invoke-WebRequest -Uri "https://download.blender.org/release/Blender4.5/blender-$version.sha256").Content
    if ($checksums -is [byte[]]) { $checksums=[Text.Encoding]::UTF8.GetString($checksums) }
    $line=($checksums -split "`n" | Where-Object { $_ -match [regex]::Escape($name) } | Select-Object -First 1)
    if (!$line) { throw 'Official Blender checksum not found.' }
    $expected=($line.Trim() -split '\s+')[0]
    if (!(Test-Path -LiteralPath $archive)) { Invoke-WebRequest -Uri "https://download.blender.org/release/Blender4.5/$name" -OutFile $archive }
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) { throw 'Blender archive checksum mismatch.' }
    Expand-Archive -LiteralPath $archive -DestinationPath $toolsDir
}
$mpfbDir=Join-Path $toolsDir 'mpfb2-2.0.18'
$mpfbArchive=Join-Path $toolsDir 'mpfb-2.0.18.zip'
$mpfbSha256='ADA7C4FF11E79CF6ED9B441BCCABC52C9359F2848B988F66E89C14C30B21FED7'
if (!(Test-Path -LiteralPath $mpfbDir)) {
    if (!(Test-Path -LiteralPath $mpfbArchive)) { Invoke-WebRequest -Uri 'https://codeload.github.com/makehumancommunity/mpfb2/zip/refs/tags/v2.0.18' -OutFile $mpfbArchive }
    if ((Get-FileHash -LiteralPath $mpfbArchive -Algorithm SHA256).Hash -ne $mpfbSha256) { throw 'MPFB 2.0.18 archive checksum mismatch.' }
    Expand-Archive -LiteralPath $mpfbArchive -DestinationPath $toolsDir
}
$assetDir=Join-Path $toolsDir 'makehuman-assets'
if (!(Test-Path -LiteralPath (Join-Path $assetDir 'packs/makehuman_system_assets.json'))) {
    $assetArchive=Join-Path $toolsDir 'makehuman_system_assets_cc0.zip'
    if (!(Test-Path -LiteralPath $assetArchive)) {
        Invoke-WebRequest -Uri 'https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip' -OutFile $assetArchive
    }
    if ((Get-FileHash -LiteralPath $assetArchive -Algorithm SHA256).Hash -ne 'B542127A8E25547C7C29C19F2D1D2ADB9A664C80396ECD694095DBC8028A0107') { throw 'Pinned MakeHuman CC0 asset archive checksum mismatch.' }
    Expand-Archive -LiteralPath $assetArchive -DestinationPath $assetDir
}
Write-Output "Blender: $executable"
Write-Output "MPFB: $mpfbDir"
Write-Output "CC0 assets: $assetDir"
