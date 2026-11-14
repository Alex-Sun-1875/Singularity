param([string]$OutputFile='')
$ErrorActionPreference='Stop'
if(!$OutputFile){$OutputFile=Join-Path $PSScriptRoot 'navigation.wasm'}
$OutputFile=[System.IO.Path]::GetFullPath($OutputFile)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputFile) | Out-Null
# No dependency downloads here. Install a verified, direct-downloaded Rust
# wasm32-unknown-unknown standard library before invoking this experiment.
& rustc (Join-Path $PSScriptRoot 'navigation.rs') --edition=2021 --crate-type=cdylib --target=wasm32-unknown-unknown -C opt-level=3 -C lto=fat -C panic=abort -C strip=symbols -C target-cpu=mvp -C link-arg=--max-memory=33554432 -o $OutputFile
if($LASTEXITCODE -ne 0){throw 'Navigation WASM compilation failed.'}
$taskManifest=[ordered]@{abi=3;sourceSha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'navigation.rs') -Algorithm SHA256).Hash.ToLowerInvariant();sha256=(Get-FileHash -LiteralPath $OutputFile -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $OutputFile).Length;compiler=(& rustc --version);target='wasm32-unknown-unknown';cpu='mvp';maximumMemoryBytes=33554432}
[System.IO.File]::WriteAllText([System.IO.Path]::ChangeExtension($OutputFile,'.json'),($taskManifest|ConvertTo-Json).Replace([string][char]13,'')+[char]10)
[pscustomobject]@{File=$OutputFile;Bytes=$taskManifest.bytes;Sha256=$taskManifest.sha256}
