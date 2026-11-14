param([string]$Entry='main.lua',[string]$Name='chapter',[int]$Width=1280,[int]$Height=720,[string[]]$ExtraArgs=@())
$ErrorActionPreference='Stop'
$runtime=Join-Path $PSScriptRoot '.runtime/UrhoXRuntime.exe'
$directory=Join-Path $PSScriptRoot 'screenshots'
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$path=Join-Path $directory "$Name.png"
$sizeArgs=@("-width=$Width","-height=$Height")+$ExtraArgs
$process=Start-Process -FilePath $runtime -WindowStyle Hidden -PassThru -WorkingDirectory (Split-Path $runtime) -RedirectStandardOutput (Join-Path $directory "$Name-out.log") -RedirectStandardError (Join-Path $directory "$Name-err.log") -ArgumentList (@($Entry,"-tapcode_dir=`"$PSScriptRoot`"",'-tool_mode','-screenshot-frame=120',"-screenshot=`"$path`"","-x$Width","-y$Height",'-w','-nosound','-log','info')+$sizeArgs)
if (!$process.WaitForExit(45000)) { $process.Kill(); throw 'Screenshot timed out.' }
if (!(Test-Path -LiteralPath $path) -or (Get-Item -LiteralPath $path).Length -eq 0) { throw "Screenshot missing: $path" }
Write-Output $path
