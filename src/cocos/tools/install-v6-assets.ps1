param(
 [string[]]$Actors=@('raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer'),
 [switch]$PropsOnly
)
$ErrorActionPreference='Stop'
$project=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$workspace=[IO.Path]::GetFullPath((Join-Path $project '../..'))
$workspacePrefix=$workspace.TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
function Safe-Path([string]$Path){
 $absolute=[IO.Path]::GetFullPath($Path)
 if(!$absolute.StartsWith($workspacePrefix,[StringComparison]::OrdinalIgnoreCase)){throw ('Path escaped the intended workspace: '+$absolute)}
 return $absolute
}
function Hash([string]$Path){return (Get-FileHash -LiteralPath (Safe-Path $Path) -Algorithm SHA256).Hash.ToLowerInvariant()}
function Read-Json([string]$Path){return Get-Content -LiteralPath (Safe-Path $Path) -Raw -Encoding utf8|ConvertFrom-Json}
function Same-Hash([string]$Path,[string]$Expected){if($Expected -notmatch '^[a-fA-F0-9]{64}$' -or (Hash $Path) -ne $Expected.ToLowerInvariant()){throw ('Candidate hash mismatch: '+$Path)}}
$stage=Safe-Path(Join-Path $workspace 'src/.tmp/character-redesign-v6')
$props=Safe-Path(Join-Path $stage 'props')
$candidateActors=Safe-Path(Join-Path $stage 'actors')
$production=Safe-Path(Join-Path $project 'assets/resources/actors')
$productionProps=Safe-Path(Join-Path $production 'props-native')
$backup=Safe-Path(Join-Path $stage 'previous-production')
$propsBackup=Safe-Path(Join-Path $backup 'props-native')
$manifest=Read-Json(Join-Path $props 'manifest.json')
$expectedProps=@('sword','oath-sword','greatsword','bow','wind-bow','astra-bow','arrow','staff','dagger','shield','lorn-shield','captain-shield','hammer','map-kit')
$actualProps=@($manifest.props.psobject.Properties.Name)
if($actualProps.Count -ne 14 -or @($actualProps|Where-Object {$_ -notin $expectedProps}).Count){throw 'Expected the exact 14 reviewed v6 prop resources.'}
if($manifest.runtimeProfile -ne 'native-kit-v1'){throw 'Unsupported prop runtime profile.'}
$textures=@{};$rootUuids=@{}
foreach($id in $expectedProps){
 $record=$manifest.props.$id
 $fbx=Safe-Path(Join-Path $props ($id+'/'+$id+'.fbx'))
 if((Safe-Path(Join-Path $workspace $record.fbx)) -ne $fbx){throw ('Unexpected candidate FBX location: '+$id)}
 Same-Hash $fbx $record.exportSHA256
 Same-Hash (Safe-Path(Join-Path $workspace $record.source)) $record.sourceSHA256
 if(!$record.fbxRoundtrip.passed -or $record.uv.zeroAreaUVTriangles -ne 0){throw ('Prop roundtrip/UV validation failed: '+$id)}
 if(@($record.textures).Count -ne 3){throw ('Prop must provide three reviewed PBR maps: '+$id)}
 foreach($texture in $record.textures){
  $path=Safe-Path(Join-Path $workspace $texture.path)
  $name=[IO.Path]::GetFileName($path)
  if($name -notmatch '^[a-z][a-z0-9_-]*\.png$' -or $path -ne (Safe-Path(Join-Path $props ('textures/'+$name)))){throw ('Unexpected candidate texture path: '+$path)}
  Same-Hash $path $texture.sha256
  if($textures.ContainsKey($name) -and $textures[$name].sha256 -ne $texture.sha256){throw ('Conflicting shared prop texture: '+$name)}
  $textures[$name]=@{path=$path;sha256=$texture.sha256}
 }
 $meta=Safe-Path(Join-Path $productionProps ($id+'/'+$id+'.fbx.meta'))
 if(Test-Path -LiteralPath $meta){$rootUuids[$id]=(Read-Json $meta).uuid}
}
if($textures.Count -ne 42){throw 'Expected exactly 42 reviewed prop PBR maps.'}
$canonicalClips=@('idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact')
if(!$PropsOnly){
 foreach($id in $Actors){
  if($id -notin @('raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer')){throw ('Invalid actor ID: '+$id)}
  $folder=Safe-Path(Join-Path $candidateActors $id);$actor=Read-Json(Join-Path $folder 'manifest.json')
  $existingTarget=Safe-Path(Join-Path $production $id);$existingMeta=Safe-Path(Join-Path $existingTarget ($id+'.fbx.meta'))
  if(!(Test-Path -LiteralPath $existingMeta) -or !(Read-Json $existingMeta).uuid){throw ('Missing existing actor root UUID for safe replacement: '+$id)}
  $null=Safe-Path(Join-Path $backup $id)
  if($actor.runtimeProfile -ne 'native-kit-v1' -or $actor.skinJointCount -ne 65 -or $actor.skeletonJointCount -ne 67 -or @($actor.bones).Count -ne 67 -or @($actor.pendingClips).Count -gt 0){throw ('Actor skeleton is not ready: '+$id)}
  if(@($actor.clips.psobject.Properties).Count -ne 11){throw ('Actor must contain all eleven canonical clips: '+$id)}
  foreach($clip in $canonicalClips){if(!$actor.clips.psobject.Properties[$clip]){throw ($id+' is missing '+$clip)}}
  foreach($bone in @('attach_bow_l','attach_arrow_r')){if($actor.bones -notcontains $bone){throw ($id+' is missing '+$bone)}}
  $actorFbx=Safe-Path(Join-Path $folder ($id+'.fbx'));if(!(Test-Path -LiteralPath $actorFbx)){throw ('Missing candidate actor FBX: '+$id)}
  $sharedPrefix=(Safe-Path(Join-Path $candidateActors 'native-shared/textures')).TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
  foreach($texture in $actor.textures){$path=Safe-Path(Join-Path $folder $texture);if(!$path.StartsWith($sharedPrefix,[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path -LiteralPath $path)){throw ('Missing or misplaced native actor texture: '+$path)}}
 }
 if($Actors.Count){
  # Reuse the existing FBX reader, checking actual bytes rather than only the
  # manifest. This introduces no tests, framework or authoring dependencies.
  $actualFbxCheck=@'
import sys,json,importlib.util
from pathlib import Path
root=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('existing_fbx_reader',root/'tools/model-pipeline/cocos_test_assets.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
report=[]
for identity in sys.argv[2].split(','):
 path=root/'src/.tmp/character-redesign-v6/actors'/identity/(identity+'.fbx');nodes=reader.fbx_nodes(path.read_bytes());objects=next(n for n in nodes if n['name']=='Objects')['children'];bones=[n for n in objects if n['name']=='Model' and n['properties'][2]=='LimbNode'];clips={n['properties'][1].split(chr(0))[0].split('|')[-1]for n in objects if n['name']=='AnimationStack'}
 assert len(bones)==67,(identity,len(bones));assert clips==reader.CLIPS,(identity,clips);report.append({'id':identity,'actualBones':len(bones),'actualClips':len(clips)})
print(json.dumps(report))
'@
  $checkOutput=$actualFbxCheck|& python - $workspace ($Actors -join ',')
  if($LASTEXITCODE -ne 0){throw 'Actual candidate actor FBX skeleton/clip verification failed.'}
  Write-Output $checkOutput
 }
}
# All candidates and paths are checked before the first production mutation.
New-Item -ItemType Directory -Path $backup -Force|Out-Null
if(!(Test-Path -LiteralPath $propsBackup)){
 if(!(Test-Path -LiteralPath $productionProps)){throw 'Missing original props-native directory for first backup.'}
 Copy-Item -LiteralPath $productionProps -Destination $propsBackup -Recurse
 $directoryMeta=Safe-Path($productionProps+'.meta')
 if(Test-Path -LiteralPath $directoryMeta){Copy-Item -LiteralPath $directoryMeta -Destination (Safe-Path(Join-Path $backup 'props-native.meta'))}
}
$targetTextures=Safe-Path(Join-Path $productionProps 'textures');New-Item -ItemType Directory -Path $targetTextures -Force|Out-Null
foreach($entry in $textures.GetEnumerator()){Copy-Item -LiteralPath $entry.Value.path -Destination (Safe-Path(Join-Path $targetTextures $entry.Key)) -Force}
foreach($id in $expectedProps){
 $target=Safe-Path(Join-Path $productionProps $id);New-Item -ItemType Directory -Path $target -Force|Out-Null
 Copy-Item -LiteralPath (Safe-Path(Join-Path $props ($id+'/'+$id+'.fbx'))) -Destination (Safe-Path(Join-Path $target ($id+'.fbx'))) -Force
 Same-Hash (Join-Path $target ($id+'.fbx')) $manifest.props.$id.exportSHA256
 if($rootUuids.ContainsKey($id) -and (Read-Json(Join-Path $target ($id+'.fbx.meta'))).uuid -ne $rootUuids[$id]){throw ('Existing prop root UUID changed: '+$id)}
}
Copy-Item -LiteralPath (Safe-Path(Join-Path $props 'manifest.json')) -Destination (Safe-Path(Join-Path $productionProps 'manifest.json')) -Force
if(!$PropsOnly){
 foreach($id in $Actors){
  $target=Safe-Path(Join-Path $production $id);$saved=Safe-Path(Join-Path $backup $id)
  if(!(Test-Path -LiteralPath $saved)){Copy-Item -LiteralPath $target -Destination $saved -Recurse}
  $candidate=Safe-Path(Join-Path $candidateActors $id)
  foreach($name in @(($id+'.fbx'),'manifest.json')){Copy-Item -LiteralPath (Safe-Path(Join-Path $candidate $name)) -Destination (Safe-Path(Join-Path $target $name)) -Force}
  $metaPath=Safe-Path(Join-Path $target ($id+'.fbx.meta'));$meta=Read-Json $metaPath;$originalUuid=$meta.uuid
  $meta.subMetas=@{};$meta.userData=@{fbx=@{smartMaterialEnabled=$true}}
  $meta|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $metaPath -Encoding utf8
  if((Read-Json $metaPath).uuid -ne $originalUuid){throw ('Actor root UUID changed: '+$id)}
  $inspection=Safe-Path(Join-Path $candidate 'inspection.json')
  if(Test-Path -LiteralPath $inspection){Copy-Item -LiteralPath $inspection -Destination (Safe-Path(Join-Path $target 'inspection.json')) -Force}
 }
 if($Actors.Count){
  $incoming=Safe-Path(Join-Path $candidateActors 'native-shared/textures');$shared=Safe-Path(Join-Path $production 'native-shared/textures')
  New-Item -ItemType Directory -Path $shared -Force|Out-Null
  foreach($image in Get-ChildItem -LiteralPath $incoming -Filter '*.png' -File){Copy-Item -LiteralPath $image.FullName -Destination (Safe-Path(Join-Path $shared $image.Name)) -Force}
 }
}
$report=@{propsOnly=[bool]$PropsOnly;actors=@($(if(!$PropsOnly){$Actors}));props=$expectedProps;propTextures=$textures.Count;backup=$propsBackup;preservedPropRootUuids=$rootUuids;sharedTexturePolicy='Copy incoming PNGs; retain existing metadata and unreferenced old maps for root final cleanup';completed=(Get-Date).ToString('o')}
$report|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Safe-Path(Join-Path $stage 'install-v6-assets-latest.json')) -Encoding utf8
Write-Output ('Installed v6 props '+$expectedProps.Count+' / textures '+$textures.Count+'; actors '+$(if($PropsOnly){0}else{$Actors.Count}))
