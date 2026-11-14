param([string]$SdkRoot="$env:LOCALAPPDATA\Android\Sdk",[int]$Port=5556,[switch]$DisableVulkan)
$ErrorActionPreference='Stop'
$project=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$emulator=Join-Path $SdkRoot 'emulator/emulator.exe'
$adb=Join-Path $SdkRoot 'platform-tools/adb.exe'
$image=Join-Path $SdkRoot 'system-images/android-34/google_apis/x86_64'
if(!(Test-Path -LiteralPath (Join-Path $image 'system.img'))){throw 'The existing Android34 Google APIs x86_64 image is required. This command does not download SDKs or images.'}
$serial='emulator-'+$Port
$connected=& $adb devices
if($connected -match ($serial+'\s+device')){Write-Output ('Already running: '+$serial);return}
$performanceAvdRoot=Join-Path $project 'temp/performance-avd'
$performanceAvdData=Join-Path $performanceAvdRoot 'SingularityPerf34.avd'
New-Item -ItemType Directory -Force -Path $performanceAvdData | Out-Null
$definition=@"
avd.ini.encoding=UTF-8
path=$performanceAvdData
target=android-34
"@
$definition | Set-Content -LiteralPath (Join-Path $performanceAvdRoot 'SingularityPerf34.ini') -Encoding ascii
if(!(Test-Path -LiteralPath (Join-Path $performanceAvdData 'config.ini'))){
@"
AvdId=SingularityPerf34
avd.ini.encoding=UTF-8
abi.type=x86_64
hw.cpu.arch=x86_64
hw.cpu.ncore=4
hw.ramSize=4096
hw.gpu.enabled=yes
hw.gpu.mode=host
hw.keyboard=yes
hw.lcd.width=2412
hw.lcd.height=1080
hw.lcd.density=480
hw.audioInput=no
hw.camera.back=none
hw.camera.front=none
hw.sensors.orientation=yes
hw.sensors.proximity=yes
hw.mainKeys=no
image.sysdir.1=system-images/android-34/google_apis/x86_64/
tag.id=google_apis
tag.display=Google APIs
target=android-34
disk.dataPartition.size=6G
showDeviceFrame=no
fastboot.forceColdBoot=yes
PlayStore.enabled=false
"@ | Set-Content -LiteralPath (Join-Path $performanceAvdData 'config.ini') -Encoding ascii
}
$env:ANDROID_AVD_HOME=$performanceAvdRoot
$env:ANDROID_HOME=$SdkRoot
$arguments=@('-avd','SingularityPerf34','-port',$Port,'-no-window','-no-audio','-no-boot-anim','-no-snapshot','-gpu','host','-cores','4','-memory','4096','-skin','2412x1080')
# Official workaround for Chrome's API30+ Vulkan compositor compatibility.
# This does not change the game's WebGL renderer or quality settings.
if($DisableVulkan){$arguments+=@('-feature','-Vulkan')}
$run=Start-Process -FilePath $emulator -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $project 'temp/performance-emulator-out.log') -RedirectStandardError (Join-Path $project 'temp/performance-emulator-err.log')
Write-Output ('Started Android emulator launcher PID '+$run.Id+'; serial '+$serial+'. Existing image only; profile '+$performanceAvdData)
