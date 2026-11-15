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
 [switch]$ValidateOnly,
 [string]$Editor='',
 [string]$Python=''
)
$ErrorActionPreference='Stop'
if($TestPackage -and $Profile -ne 'test'){throw '-TestPackage is a legacy alias for -Profile test.'}
if($AuditOnly -and $WebPreview){throw 'Choose only one build mode.'}
if(($AuditOnly -and $Profile -ne 'test') -or ($WebPreview -and $Profile -eq 'release')){throw 'Audit uses test gameplay; a Web preview cannot be a release package.'}
if($GuestTest -and ($Profile -ne 'test' -or $AuditOnly -or $WebPreview)){throw '-GuestTest is allowed only in a test package.'}
if($ArtifactDirectory){throw 'Delivery is fixed at src/out/<version>/. Use npm run pack:taptap.'}
$mode=if($WebPreview){'preview'}elseif($AuditOnly){'audit'}else{$Profile}
$buildArgs=@((Join-Path $PSScriptRoot 'tools/build-taptap.cjs'),'--mode',$mode,'--profile',$Profile)
if($TapAppId){$buildArgs+=@('--app-id',$TapAppId)}
if($PreviousVersion){$buildArgs+=@('--previous-version',$PreviousVersion)}
if($OutputName){$buildArgs+=@('--output-name',$OutputName)}
if($EditorUserData){$buildArgs+=@('--editor-user-data',$EditorUserData)}
if($Editor){$buildArgs+=@('--editor',$Editor)}
if($Python){$buildArgs+=@('--python',$Python)}
if($GuestTest){$buildArgs+='--guest'}
if($ValidateOnly){$buildArgs+='--check'}
# Compatibility entry only: all stages and checks live in the shared Node script.
& node @buildArgs
if($LASTEXITCODE -ne 0){throw 'TapTap build failed. Inspect the printed logs.'}
