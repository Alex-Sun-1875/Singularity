param(
 [string[]]$Actors=@('raphael','mira','nightqi','evelyn','lorn','kael','captain','raider','raider-archer','raider-shield'),
 [string]$CandidateRoot='',
 [string]$BackupRoot=''
)
$ErrorActionPreference='Stop'
$project=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$workspace=[IO.Path]::GetFullPath((Join-Path $project '../..'))
$candidate=if($CandidateRoot){[IO.Path]::GetFullPath($CandidateRoot)}else{Join-Path $workspace 'src/.tmp/native-production/actors'}
$backup=if($BackupRoot){[IO.Path]::GetFullPath($BackupRoot)}else{Join-Path $workspace 'src/.tmp/native-production/previous-production'}
if(!$candidate.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar) -or !$backup.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar)){throw 'Staged actors and backup must stay inside the workspace.'}
$production=Join-Path $project 'assets/resources/actors'
foreach($id in $Actors){
 if($id -notmatch '^[a-z][a-z-]*$'){throw 'Invalid actor directory name.'}
 $manifest=Get-Content -LiteralPath (Join-Path $candidate ($id+'/manifest.json')) -Raw|ConvertFrom-Json
 if($manifest.runtimeProfile -ne 'native-kit-v1' -or $manifest.pendingClips.Count -gt 0){throw ($id+' is not ready for native installation.')}
 if(@($manifest.clips.psobject.Properties).Count -ne 11){throw ($id+' does not have all 11 canonical clips.')}
 foreach($clip in @('idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact')){
  if(!$manifest.clips.psobject.Properties[$clip]){throw ($id+' is missing '+$clip)}
 }
 foreach($bone in @('attach_bow_l','attach_arrow_r')){if($manifest.bones -notcontains $bone){throw ($id+' is missing authored attachment '+$bone)}}
}
New-Item -ItemType Directory -Path $backup -Force|Out-Null
foreach($id in $Actors){
 $target=[IO.Path]::GetFullPath((Join-Path $production $id))
 $saved=[IO.Path]::GetFullPath((Join-Path $backup $id))
 if(!$target.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar) -or !$saved.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar)){throw 'Actor path escaped the workspace.'}
 if(!(Test-Path -LiteralPath $saved)){Copy-Item -LiteralPath $target -Destination $saved -Recurse}
 foreach($name in @(($id+'.fbx'),'manifest.json')){Copy-Item -LiteralPath (Join-Path $candidate ($id+'/'+$name)) -Destination (Join-Path $target $name) -Force}
 $manifestPath=Join-Path $target 'manifest.json'
 $native=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
 $native|Add-Member -NotePropertyName 'cocosBinding' -NotePropertyValue @{version='cocos-3.8.8-kaykit-v1';bowEuler=@(90,0,180);arrowEuler=@(0,0,0);arrowPosition=@(0,0.35595446825027466,0);verifiedFullHoldGapMetres=0.00028757} -Force
 foreach($clip in @($native.clips.interact,$native.libraryMotion.clips.interact)){
  $clip|Add-Member -NotePropertyName 'phaseSampling' -NotePropertyValue @{gameplayFractions=@(0,1);sourceFractions=@(0.3,0.55)} -Force
 }
 $native|ConvertTo-Json -Depth 50|Set-Content -LiteralPath $manifestPath -Encoding utf8
 # Retain root asset UUID; let the importer regenerate the new native hierarchy,
 # material names and complete clip ranges instead of the previous rig's cuts.
 $metaPath=Join-Path $target ($id+'.fbx.meta')
 $meta=Get-Content -LiteralPath $metaPath -Raw|ConvertFrom-Json
 $meta.subMetas=@{};$meta.userData=@{fbx=@{smartMaterialEnabled=$true}}
 $meta|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $metaPath -Encoding utf8
 # Retire the old per-role textures outside assets. Keep them for restoration;
 # the native FBX and material adapter use the shared author texture directory.
 $oldTextures=Join-Path $target 'textures'
 $retired=[IO.Path]::GetFullPath((Join-Path $backup ('retired-'+$id+'-textures')))
 if(!$retired.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar)){throw 'Retired texture path escaped the workspace.'}
 if((Test-Path -LiteralPath $oldTextures) -and !(Test-Path -LiteralPath $retired)){Move-Item -LiteralPath $oldTextures -Destination $retired}
 foreach($name in @('textures.meta','inspection.json','inspection.json.meta')){
  $old=Join-Path $target $name;$retiredFile=Join-Path $backup ('retired-'+$id+'-'+$name)
  if((Test-Path -LiteralPath $old) -and !(Test-Path -LiteralPath $retiredFile)){Move-Item -LiteralPath $old -Destination $retiredFile}
 }
 $inspection=Join-Path $candidate ($id+'/inspection.json')
 if(Test-Path -LiteralPath $inspection){Copy-Item -LiteralPath $inspection -Destination (Join-Path $target 'inspection.json') -Force}
 Write-Output ('Installed native actor '+$id)
}
$shared=Join-Path $production 'native-shared/textures'
$incoming=Join-Path $candidate 'native-shared/textures'
$retiredShared=[IO.Path]::GetFullPath((Join-Path $backup 'retired-native-shared'))
if(!$retiredShared.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar)){throw 'Shared texture backup escaped the workspace.'}
if(Test-Path -LiteralPath $shared){
 foreach($file in Get-ChildItem -LiteralPath $shared -Filter '*.png' -File){
  if(Test-Path -LiteralPath (Join-Path $incoming $file.Name)){continue}
  New-Item -ItemType Directory -Path $retiredShared -Force|Out-Null
  Move-Item -LiteralPath $file.FullName -Destination (Join-Path $retiredShared $file.Name)
  if(Test-Path -LiteralPath ($file.FullName+'.meta')){Move-Item -LiteralPath ($file.FullName+'.meta') -Destination (Join-Path $retiredShared ($file.Name+'.meta'))}
 }
}
Copy-Item -LiteralPath (Join-Path $candidate 'native-shared') -Destination $production -Recurse -Force
