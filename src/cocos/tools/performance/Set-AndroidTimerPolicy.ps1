param([ValidateSet('Query','Honor','Restore')][string]$Action='Query',[ValidatePattern('^emulator-\d+$')][string]$Serial='emulator-5556')
$ErrorActionPreference='Stop'
# Only our dedicated emulator. No global timer, power-plan or priority changes.
# Microsoft API + reset semantics: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation
# Installed SDK22621 processthreadsapi.h: ProcessPowerThrottling=4, IGNORE_TIMER_RESOLUTION=0x4.
$project=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$port=[int]$Serial.Split('-')[1]
$owned=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^qemu-system-' -and $_.CommandLine -match ('-avd SingularityPerf34 -port '+$port+'(?:\s|$)')})
if($owned.Count -ne 1){throw 'Expected exactly one owned Singularity performance emulator.'}
$process=Get-Process -Id $owned[0].ProcessId
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SingularityTimerPolicy {
 [StructLayout(LayoutKind.Sequential)] public struct State {public uint Version,ControlMask,StateMask;}
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetProcessInformation(IntPtr p,int kind,ref State state,uint size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetProcessInformation(IntPtr p,int kind,ref State state,uint size);
 public static State Read(IntPtr p){var s=new State{Version=1};if(!GetProcessInformation(p,4,ref s,12))throw new System.ComponentModel.Win32Exception();return s;}
 public static void Write(IntPtr p,uint control,uint state){var s=new State{Version=1,ControlMask=control,StateMask=state};if(!SetProcessInformation(p,4,ref s,12))throw new System.ComponentModel.Win32Exception();}
}
'@
$before=[SingularityTimerPolicy]::Read($process.Handle)
$ledger=Join-Path $project 'temp/performance-host-timer-policy.json'
$previous=if(Test-Path -LiteralPath $ledger){Get-Content -LiteralPath $ledger -Raw | ConvertFrom-Json}else{$null}
if($previous -and ($previous.pid -ne $process.Id -or [datetime]$previous.created -ne $owned[0].CreationDate)){$previous=$null}
if($Action -eq 'Honor'){
 if(!$previous){$previous=[ordered]@{pid=$process.Id;created=$owned[0].CreationDate;originalControlMask=$before.ControlMask;originalStateMask=$before.StateMask};$previous|ConvertTo-Json|Set-Content -LiteralPath $ledger -Encoding utf8}
 $control=[uint32]($before.ControlMask -bor 4);$state=[uint32]($before.StateMask -band [uint32]4294967291)
 [SingularityTimerPolicy]::Write($process.Handle,$control,$state)
}elseif($Action -eq 'Restore'){
 if(!$previous){throw 'No matching owned-process timer policy ledger to restore.'}
 [SingularityTimerPolicy]::Write($process.Handle,[uint32]$previous.originalControlMask,[uint32]$previous.originalStateMask)
}
$after=[SingularityTimerPolicy]::Read($process.Handle)
if($Action -eq 'Honor' -and (($after.ControlMask -band 4) -ne 4 -or ($after.StateMask -band 4) -ne 0)){throw 'Timer request policy did not match requested per-process setting.'}
if($Action -eq 'Restore' -and ($after.ControlMask -ne $previous.originalControlMask -or $after.StateMask -ne $previous.originalStateMask)){throw 'Original timer policy was not restored.'}
[ordered]@{action=$Action;pid=$process.Id;created=$owned[0].CreationDate;version=$after.Version;controlMask=$after.ControlMask;stateMask=$after.StateMask;timerRequests=if($after.ControlMask -band 4){if($after.StateMask -band 4){'ignored'}else{'honored'}}else{'system-managed'};scope='Owned emulator only; does not itself request a timer resolution; not game performance improvement'}|ConvertTo-Json
