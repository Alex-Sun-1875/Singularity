[CmdletBinding()]
param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path.TrimEnd('\')
if ($workspaceRoot -ne 'F:\workspace\Singularity') { throw 'This reviewed cleanup belongs to F:\workspace\Singularity.' }
$workspacePrefix = $workspaceRoot + '\'
$targets = @(
  'tmp\art-reference',
  'source-art\characters\2d-concepts\identity-reference-v1\identity-install-rm06cvm2',
  'source-art\characters\2d-concepts\run-reference-v3\install-20261106T180439Z-_xea2g1y',
  'source-art\characters\2d-concepts\locomotion-alignment-v1\locomotion-install-5y_b8qqd',
  'source-art\characters\2d-concepts\locomotion-alignment-v1\head-scale-v2\locomotion-install-t_ahx5_y',
  'src\cocos\library',
  'src\cocos\temp\asset-db',
  'src\cocos\temp\programming'
)
foreach ($cacheRoot in @('source-art', 'tools', 'src\cocos\tools', 'src\cocos\asset-pipeline')) {
  $cacheRootPath = Join-Path $workspaceRoot $cacheRoot
  if (Test-Path -LiteralPath $cacheRootPath) {
    Get-ChildItem -LiteralPath $cacheRootPath -Directory -Filter '__pycache__' -Recurse -Force |
      ForEach-Object { $targets += $_.FullName.Substring($workspacePrefix.Length) }
  }
}
$reviewed = @()
foreach ($relative in ($targets | Select-Object -Unique)) {
  $absolute = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $relative))
  if (-not $absolute.StartsWith($workspacePrefix, [StringComparison]::OrdinalIgnoreCase) -or
      $absolute.StartsWith((Join-Path $workspaceRoot '.git'), [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe target refused: $absolute"
  }
  if (-not (Test-Path -LiteralPath $absolute)) { continue }
  $item = Get-Item -LiteralPath $absolute -Force
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked target refused: $absolute" }
  $children = @(Get-ChildItem -LiteralPath $absolute -Recurse -Force)
  if (@($children | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
    throw "Nested link refused: $absolute"
  }
  $files = @($children | Where-Object { -not $_.PSIsContainer })
  $reviewed += [pscustomobject]@{ path=$relative.Replace('\','/'); absolute=$absolute; files=$files.Count; bytes=($files | Measure-Object Length -Sum).Sum }
}
$report = [pscustomobject]@{
  date='2026-11-07'; workspace=$workspaceRoot; disposal='Windows Recycle Bin'; status='reviewed';
  targets=$reviewed; files=($reviewed | Measure-Object files -Sum).Sum; bytes=($reviewed | Measure-Object bytes -Sum).Sum;
  retained=@('src/cocos/temp/tsconfig.cocos.json','src/cocos/temp/declarations','src/cocos/temp/concept-2d-server-out.log','src/cocos/temp/concept-2d-server-err.log','src/cocos/build','src/cocos/artifacts','src/cocos/node_modules','source art, prompts, licenses and referenced verification records')
}
$manifest = Join-Path $PSScriptRoot 'git-hygiene-cleanup-2026-11-07.json'
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifest
Write-Output "Reviewed $($reviewed.Count) targets; $($report.files) files; $([math]::Round($report.bytes/1MB,2)) MiB."
if (-not $Apply) { $reviewed | Select-Object path,files,@{n='MiB';e={[math]::Round($_.bytes/1MB,2)}}; return }
Add-Type -AssemblyName Microsoft.VisualBasic
foreach ($target in $reviewed) {
  [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
    $target.absolute,
    [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
    [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin,
    [Microsoft.VisualBasic.FileIO.UICancelOption]::ThrowException)
  if (Test-Path -LiteralPath $target.absolute) { throw "Target was not recycled: $($target.path)" }
}
$report.status = 'completed'
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifest
Write-Output 'Reviewed temporary files moved to the Windows Recycle Bin.'
