param([ValidateSet('Query','Set','Restore')][string]$Action='Query',[ValidatePattern('^emulator-\d+$')][string]$Serial='emulator-5556',[switch]$PhysicalCoresOnly)
$ErrorActionPreference='Stop'
$project=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$port=[int]$Serial.Split('-')[1]
$owned=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^qemu-system-' -and $_.CommandLine -match ('-avd SingularityPerf34 -port '+$port+'(?:\s|$)')})
if($owned.Count -ne 1){throw 'Expected exactly one owned Singularity performance emulator process.'}
$process=Get-Process -Id $owned[0].ProcessId
$ledger=Join-Path $project 'temp/performance-host-affinity.json'
$previous=if(Test-Path -LiteralPath $ledger){Get-Content -LiteralPath $ledger -Raw | ConvertFrom-Json}else{$null}
if($previous -and ($previous.pid -ne $process.Id -or [datetime]$previous.created -ne $owned[0].CreationDate)){$previous=$null}
if($Action -eq 'Restore'){
 if(!$previous){throw 'No matching owned-process affinity ledger to restore.'}
 $process.ProcessorAffinity=[IntPtr][long]$previous.originalAffinity
}elseif($Action -eq 'Set'){
 Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;
public static class SingularityPerfCpuSets {
 [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetSystemCpuSetInformation(IntPtr buffer,uint size,out uint needed,IntPtr process,uint flags);
 public static object[] Read(){uint size;GetSystemCpuSetInformation(IntPtr.Zero,0,out size,IntPtr.Zero,0);IntPtr buffer=Marshal.AllocHGlobal((int)size);try{if(!GetSystemCpuSetInformation(buffer,size,out size,IntPtr.Zero,0))throw new System.ComponentModel.Win32Exception();var rows=new List<object>();for(int at=0;at<size;){int bytes=Marshal.ReadInt32(buffer,at);if(bytes<32)throw new Exception("Unexpected CPU set record");if(Marshal.ReadInt32(buffer,at+4)==0)rows.Add(new {Group=Marshal.ReadInt16(buffer,at+12),Logical=Marshal.ReadByte(buffer,at+14),Core=Marshal.ReadByte(buffer,at+15),Efficiency=Marshal.ReadByte(buffer,at+18)});at+=bytes;}return rows.ToArray();}finally{Marshal.FreeHGlobal(buffer);}}
}
'@
 $cpus=[SingularityPerfCpuSets]::Read()
 $level=($cpus | Measure-Object Efficiency -Maximum).Maximum
 $selected=@($cpus|Where-Object {$_.Group -eq 0 -and $_.Efficiency -eq $level})
 if($PhysicalCoresOnly){$selected=@($selected|Group-Object Core|ForEach-Object {$_.Group|Sort-Object Logical|Select-Object -First 1})}
 if(!$selected.Count -or @($selected|Where-Object Logical -ge 63).Count){throw 'Unsupported host CPU group layout for this benchmark fixture.'}
 $mask=[long]0
 foreach($cpu in $selected){$mask=$mask -bor ([long]1 -shl $cpu.Logical)}
 $original=if($previous){[long]$previous.originalAffinity}else{$process.ProcessorAffinity.ToInt64()}
 $process.ProcessorAffinity=[IntPtr]$mask
 @{pid=$process.Id;created=$owned[0].CreationDate;originalAffinity=$original;affinity=$mask;physicalCoresOnly=[bool]$PhysicalCoresOnly;selectedLogicalCpus=@($selected.Logical);efficiencyClass=$level}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $ledger -Encoding utf8
}
$gpuMatch=[regex]::Match($owned[0].CommandLine,'(?:^|\s)-gpu\s+(\S+)')
$featureOverrides=@([regex]::Matches($owned[0].CommandLine,'(?:^|\s)-feature\s+(\S+)') | ForEach-Object {$_.Groups[1].Value.Split(',')})
$vulkanOverrides=@($featureOverrides|Where-Object {$_ -in '-Vulkan','Vulkan'})
$vulkanDisabled=$vulkanOverrides.Count -gt 0 -and $vulkanOverrides[-1] -eq '-Vulkan'
$transportConfig=$null
$hardwarePath=Join-Path $project 'temp/performance-avd/SingularityPerf34.avd/hardware-qemu.ini'
if((Test-Path -LiteralPath $hardwarePath) -and (Get-Item -LiteralPath $hardwarePath).LastWriteTime -ge $owned[0].CreationDate.AddSeconds(-5)){
 $hardware=@{}
 foreach($line in Get-Content -LiteralPath $hardwarePath){
  $parts=$line.Split('=',2)
  if($parts.Length -eq 2){$hardware[$parts[0].Trim()]=$parts[1].Trim()}
 }
 $transportConfig=@{name=$hardware['hw.gltransport'];writeBufferSize=$hardware['hw.gltransport.asg.writeBufferSize'];writeStepSize=$hardware['hw.gltransport.asg.writeStepSize'];dataRingSize=$hardware['hw.gltransport.asg.dataRingSize'];drawFlushInterval=$hardware['hw.gltransport.drawFlushInterval']}
}
@{pid=$process.Id;created=$owned[0].CreationDate;affinity=$process.ProcessorAffinity.ToInt64();priority=$process.PriorityClass.ToString();action=$Action;graphics=@{hostGpuMode=$gpuMatch.Groups[1].Value;vulkanDisabled=$vulkanDisabled;featureOverrides=$featureOverrides;transportConfig=$transportConfig};scope='Owned emulator only; virtual CPU count and OS power plan are unchanged'}|ConvertTo-Json -Depth 5
