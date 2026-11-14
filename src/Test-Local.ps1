param([string]$Entry = 'validation/TestMain.lua', [int]$Frames = 12)
$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$runtime = Join-Path $project '.runtime/UrhoXRuntime.exe'
if (!(Test-Path -LiteralPath $runtime)) { throw 'Run .\Setup-Local.ps1 first.' }
$outputDir = Join-Path $project '.tmp'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$report = Join-Path $outputDir 'validate.json'
$argsList = @($Entry, "-tapcode_dir=`"$project`"", '-tool_mode', '-graphicsheadless', '-validate', "-validate-frames=$Frames", '-validate-timeout=25', "-validate-output=`"$report`"", '-nosound', '-log', 'info')
$process = Start-Process -FilePath $runtime -WindowStyle Hidden -PassThru -WorkingDirectory (Split-Path $runtime) -RedirectStandardOutput (Join-Path $outputDir 'validate-out.log') -RedirectStandardError (Join-Path $outputDir 'validate-err.log') -ArgumentList $argsList
if (!$process.WaitForExit(35000)) { $process.Kill(); throw 'Runtime validation timed out.' }
$data = Get-Content -Raw -LiteralPath $report | ConvertFrom-Json
Get-Content (Join-Path $outputDir 'validate-out.log') | Select-String '\[.*Test\]'
Write-Output ($data | ConvertTo-Json -Depth 10)
if ($data.result -ne 'PASS' -or $data.summary.lua_errors -gt 0 -or $data.missing_resources.Count -gt 0) { throw 'Runtime validation failed. See src/.tmp/validate.json' }
