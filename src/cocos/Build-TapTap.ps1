param(
 [ValidateSet('dev','test','release')][string]$Profile='test',
 [string]$TapAppId='',
 [switch]$AuditOnly,
 [switch]$WebPreview,
 [switch]$TestPackage,
 [switch]$GuestTest,
 [string]$PreviousVersion='',
 [string]$ArtifactDirectory='',
 [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_-]*$')][string]$OutputName='',
 [string]$EditorUserData='',
 [switch]$ValidateOnly
)
$ErrorActionPreference='Stop'
$project=$PSScriptRoot
if($TestPackage -and $Profile -ne 'test'){throw '-TestPackage is a legacy alias for -Profile test.'}
if($AuditOnly -and $WebPreview){throw 'Choose only one of AuditOnly or WebPreview.'}
if(($AuditOnly -and $Profile -ne 'test') -or ($WebPreview -and $Profile -eq 'release')){throw 'Audit uses test gameplay; a Web preview cannot be a release package.'}
if($GuestTest -and ($Profile -ne 'test' -or $AuditOnly -or $WebPreview)){throw '-GuestTest is allowed only in a test package.'}
if($AuditOnly -and ![string]::IsNullOrWhiteSpace($TapAppId)){throw '-AuditOnly must not bind a platform identity.'}
$editor='C:\ProgramData\cocos\editors\Creator\3.8.8\CocosCreator.exe'
if(!$ValidateOnly -and !(Test-Path -LiteralPath $editor)){throw 'Cocos Creator 3.8.8 is not installed at the configured path.'}
$mode=if($WebPreview){'preview'}elseif($AuditOnly){'audit'}else{$Profile}
if([string]::IsNullOrWhiteSpace($OutputName)){$OutputName=if($WebPreview){'taptap-preview'}elseif($AuditOnly){'taptap-audit'}elseif($GuestTest){'taptap-guest'}else{'taptap'}}
if(!$OutputName.EndsWith('-'+$Profile,[System.StringComparison]::OrdinalIgnoreCase)){$OutputName+='-'+$Profile}
if([string]::IsNullOrWhiteSpace($ArtifactDirectory)){$ArtifactDirectory=Join-Path $project ('artifacts/'+$OutputName)}
$ArtifactDirectory=[System.IO.Path]::GetFullPath($ArtifactDirectory)
if(!$ArtifactDirectory.EndsWith('-'+$Profile,[System.StringComparison]::OrdinalIgnoreCase)){$ArtifactDirectory+='-'+$Profile}
if($Profile -eq 'release'){
 $baselineJson=& node (Join-Path $project 'tools/release-notes.cjs') --check-baseline
 if($LASTEXITCODE -ne 0){throw 'Published release baseline is unavailable.'}
}
if($ValidateOnly){
 $checkArgs=@((Join-Path $project 'tools/taptap-config.cjs'),'--json','--mode',$mode,'--profile',$Profile)
 if($TapAppId){$checkArgs+=@('--app-id',$TapAppId)}
 if($PreviousVersion){$checkArgs+=@('--previous-version',$PreviousVersion)}
 & node @checkArgs
 if($LASTEXITCODE -ne 0){throw 'Build configuration validation failed.'}
 @{profile=$Profile;mode=$mode;outputName=$OutputName;artifactDirectory=$ArtifactDirectory;guestTest=[bool]$GuestTest;versionAllocated=$false}|ConvertTo-Json -Compress
 return
}
$temp=Join-Path $project 'temp'
New-Item -ItemType Directory -Path $temp -Force | Out-Null
# One project mutates generated sources and one version sequence; serialize packages.
try{$buildLock=[System.IO.File]::Open((Join-Path $temp 'taptap-build.lock'),[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)}catch{throw 'Another TapTap build is using this project; wait for it to finish.'}
$preparedProfile=$false
try{
$prepareArgs=@((Join-Path $project 'tools/taptap-config.cjs'),'--prepare','--json','--mode',$mode,'--profile',$Profile)
# Allocate one version per package invocation, before resource preparation or Creator retries.
if(!$WebPreview){$prepareArgs+=@('--version','patch')}
if($TapAppId){$prepareArgs+=@('--app-id',$TapAppId)}
if($PreviousVersion){$prepareArgs+=@('--previous-version',$PreviousVersion)}
$preparedProfile=$true
$releaseJson=& node @prepareArgs
if($LASTEXITCODE -ne 0){throw 'TapTap release configuration validation failed.'}
$release=$releaseJson|ConvertFrom-Json
if(!$WebPreview){Write-Output ('TapTap package version auto-incremented to '+$release.version)}
if(!$AuditOnly){$TapAppId=$release.miniAppId}
$platform=if($WebPreview){'web-mobile'}else{'wechatgame'}
& node (Join-Path $project 'tools/prepare-navigation-wasm.cjs') --prepare
if($LASTEXITCODE -ne 0){throw 'Navigation WASM source verification failed.'}
& python (Join-Path $project 'tools/prepare-taptap.py') --platform $platform --output-name $OutputName --mode $mode --profile $Profile
if($LASTEXITCODE -ne 0){throw 'TapTap resource profile preparation failed.'}
& python (Join-Path $project 'tools/refresh-morph-build-cache.py') --project $project
if($LASTEXITCODE -ne 0){throw 'Mesh cache validation failed.'}
if($Profile -eq 'release'){
 $notesDirectory=Join-Path $temp ('release-notes-'+$OutputName)
 & node (Join-Path $project 'tools/release-notes.cjs') --prepare --version $release.version --output $notesDirectory
 if($LASTEXITCODE -ne 0){throw 'Release update log generation failed.'}
}
$configPath=Join-Path $project ('temp/build-'+$OutputName+'.json')
$outLog=Join-Path $project ('temp/build-'+$OutputName+'-out.log')
$errLog=Join-Path $project ('temp/build-'+$OutputName+'-err.log')
$arguments=@('--project',('"'+$project.Replace('\','/')+'"'),'--build',('"configPath='+$configPath.Replace('\','/')+'"'))
if($EditorUserData){
 $profilePath=[System.IO.Path]::GetFullPath($EditorUserData).Replace('\','/')
 $profileArgument=if($profilePath -match '\s'){'--user-data-dir="'+$profilePath+'"'}else{'--user-data-dir='+$profilePath}
 $arguments=@($profileArgument)+$arguments
}
$completion='build Task \('+[regex]::Escape($OutputName)+'\) Finished'
for($attempt=1;$attempt -le 2;$attempt++){
 $run=Start-Process -FilePath $editor -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
 Write-Output ('Cocos build PID '+$run.Id+'. Log: '+$outLog)
 $run.WaitForExit()
 $completed=($run.ExitCode -eq 36 -or $run.ExitCode -eq 0) -and (Select-String -LiteralPath $outLog -Pattern $completion -Quiet)
 if($completed){
  if(Select-String -LiteralPath @($outLog,$errLog) -Pattern 'Script .* attached to .* is missing or invalid|Missing class:' -Quiet){
   throw ('Cocos exported a scene with a missing script component. Inspect '+$outLog+' and '+$errLog)
  }
  break
 }
 # A transient Windows file-open failure can stop Creator before it starts building.
 $settingsOpenFailure='UNKNOWN: unknown error, open.*[\\/]settings[\\/]v2[\\/]packages[\\/]engine\.json'
 $retryable=@(Select-String -LiteralPath @($outLog,$errLog) -Pattern $settingsOpenFailure).Count -gt 0
 if($attempt -eq 1 -and $retryable){
  Copy-Item -LiteralPath $outLog -Destination ($outLog+'.attempt1') -Force
  Copy-Item -LiteralPath $errLog -Destination ($errLog+'.attempt1') -Force
  Write-Warning 'Creator could not open engine settings during startup; retrying once. First-attempt logs are preserved.'
  Start-Sleep -Seconds 1
  continue
 }
 throw ('Cocos build did not complete (exit '+$run.ExitCode+'). Inspect '+$outLog+' and '+$errLog)
}
$buildRoot=Join-Path $project ('build/'+$OutputName)
& node (Join-Path $project 'tools/build-profile.cjs') --verify-build $buildRoot --profile $Profile
if($LASTEXITCODE -ne 0){throw 'Cocos export does not contain the requested gameplay profile.'}
if($Profile -eq 'release'){
 & node (Join-Path $project 'tools/release-notes.cjs') --verify-source $notesDirectory
 if($LASTEXITCODE -ne 0){throw 'Release inputs changed during export.'}
 foreach($noteFile in @('RELEASE_NOTES.md','source-manifest.json','release-changes.json')){Copy-Item -LiteralPath (Join-Path $notesDirectory $noteFile) -Destination (Join-Path $buildRoot $noteFile) -Force}
}
& node (Join-Path $project 'tools/render-policy.cjs') --build $buildRoot
if($LASTEXITCODE -ne 0){throw 'Generated rendering configuration violated the performance policy.'}
& node (Join-Path $project 'tools/prepare-navigation-wasm.cjs') --build $buildRoot
if($LASTEXITCODE -ne 0){throw 'Navigation WASM export failed.'}
$notices=Join-Path $project 'build-templates/web-desktop/THIRD_PARTY_NOTICES.txt'
if(Test-Path -LiteralPath $notices){Copy-Item -LiteralPath $notices -Destination (Join-Path $buildRoot 'THIRD_PARTY_NOTICES.txt') -Force}
if($WebPreview){
 $entry=Join-Path $buildRoot 'index.html'
 $html=Get-Content -LiteralPath $entry -Raw -Encoding UTF8
 $html=$html.Replace('<head>','<head><script>globalThis.__TAP_RELEASE__=true;</script>')
 [System.IO.File]::WriteAllText($entry,$html,[System.Text.UTF8Encoding]::new($false))
 & node (Join-Path $project 'tools/copy-branding.cjs') $buildRoot
 if($LASTEXITCODE -ne 0){throw 'Web game icon export failed.'}
 Write-Output ('Local browser verification build: '+$buildRoot)
}else{
 $packageRoot=Join-Path $project ('build/'+$OutputName+'-package')
 if([string]::IsNullOrWhiteSpace($ArtifactDirectory)){$ArtifactDirectory=Join-Path $project ('artifacts/'+$OutputName)}
 $ArtifactDirectory=[System.IO.Path]::GetFullPath($ArtifactDirectory)
 $version=$release.version
 $convertArgs=@((Join-Path $project 'tools/convert-taptap.cjs'),'--source',$buildRoot,'--target',$packageRoot,'--version',$version,'--profile',$Profile)
 if($AuditOnly){$convertArgs+='--audit-only'}else{$convertArgs+=@('--app-id',$TapAppId)}
 if($Profile -eq 'test' -and !$AuditOnly){$convertArgs+='--test-package'}
 if($GuestTest){$convertArgs+='--guest-test'}
 & node @convertArgs
 if($LASTEXITCODE -ne 0){throw 'TapTap conversion failed.'}
 & python (Join-Path $project 'tools/report-taptap.py') $packageRoot --output $ArtifactDirectory
 if($LASTEXITCODE -ne 0){throw 'TapTap package verification failed.'}
 $settingsPath=Join-Path $ArtifactDirectory 'upload-settings.json'
 $settings=Get-Content -LiteralPath $settingsPath -Raw|ConvertFrom-Json
 Write-Output ''
 Write-Output ('TapTap package built: '+$release.title+' v'+$version)
 Write-Output ('MiniApp ID: '+$TapAppId)
 Write-Output ('ZIP: '+$settings.packageFilename)
 Write-Output ('Build information and SHA-256: '+(Split-Path -Parent $settings.packageFilename))
 Write-Output ('Size: '+[Math]::Round($settings.uploadZipBytes/1000000,2)+' MB')
 Write-Output ('Cocos WASM: '+$settings.wasm.engineTransport.wasmBytes+' bytes; '+$settings.wasm.engineTransport.wasmBytesInMainPackage+' bytes in main package; transport validation='+$settings.wasm.engineTransport.localValidationPassed)
 Write-Output 'Platform WASM function split: not verified; requires a compatible SDK export and console function collection.'
 Write-Output ('Upload settings: '+$settingsPath)
 if($settings.localBlockers.Count){Write-Warning ('Package generated; game integration still requires: '+($settings.localBlockers -join ' '))}
 if($Profile -ne 'release'){Write-Output ($Profile+' package only. Complete the recorded platform/device checks before release.')}
 if($Profile -eq 'release'){Write-Output ('Release notes: '+(Join-Path (Split-Path -Parent $settings.packageFilename) 'RELEASE_NOTES.md'))}
}
}finally{
 try{
  # A dev package must not leave the editor or the next preview running accelerated rules.
  if($preparedProfile -and $Profile -ne 'test'){
   $restoredConfig=& node (Join-Path $project 'tools/taptap-config.cjs') --prepare --json --mode preview --profile test
   if($LASTEXITCODE -ne 0){throw 'Could not restore normal test gameplay configuration after packaging.'}
  }
 }finally{$buildLock.Dispose()}
}
