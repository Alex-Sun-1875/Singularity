const {_android:android}=require('playwright');
const {execFileSync}=require('node:child_process');
const path=require('node:path');
function parseProcStat(text,hz){
  const close=text.lastIndexOf(')'),pid=text.slice(0,text.indexOf(' ')),fields=text.slice(close+1).trim().split(/\s+/);
  if(close<0||fields.length<20||!Number.isFinite(hz)||hz<=0)throw Error('Invalid Android proc stat');
  const ticks=Number(fields[11])+Number(fields[12]),start=fields[19];
  if(!Number.isFinite(ticks)||!/^[0-9]+$/.test(start))throw Error('Invalid Android CPU counters');
  return {key:`${pid}:${start}`,cpuSeconds:ticks/hz,ticks};
}
function parseGraphicsLog(log,marker){
  const at=log.lastIndexOf(marker);
  if(at<0)throw Error('Android graphics log window marker is missing or rotated out');
  const window=log.slice(at+marker.length);
  return {log:window,errors:window.split(/\r?\n/).filter(line=>/GL ERROR|GL_INVALID_|GPU process (?:exited|has crashed)|CONTEXT_LOST|WebGL.*context.*lost/i.test(line))};
}
function inspectNativeUi(xml){
  const nodes=[...xml.matchAll(/<node\b[^>]*>/g)].map(([node])=>Object.fromEntries([...node.matchAll(/([\w-]+)="([^"]*)"/g)].map(([,k,v])=>[k,v])));
  if(!nodes.length)throw Error('Android native UI hierarchy is empty');
  const help=nodes.some(n=>n['resource-id']==='android:id/immersive_cling_title'),ok=nodes.find(n=>n['resource-id']==='android:id/ok'&&n.package==='android'&&n.clickable==='true'&&n.enabled==='true');
  if(help&&ok){const b=/^\[(\d+),(\d+)\]\[(\d+),(\d+)\]$/.exec(ok.bounds);if(!b)throw Error('Invalid native fullscreen acknowledgement bounds');return {clean:false,immersiveHelp:true,tap:[Math.floor((+b[1]+ +b[3])/2),Math.floor((+b[2]+ +b[4])/2)]};}
  const unexpected=nodes.filter(n=>n.package&&n.package!=='com.android.chrome'||/Button$/.test(n.class||''));
  return {clean:!unexpected.length,immersiveHelp:false,unexpected:unexpected.map(n=>({package:n.package,id:n['resource-id'],text:n.text}))};
}
async function openAndroid(serial,url){
  if(!/^emulator-\d+$/.test(serial))throw Error('Android performance backend requires an emulator serial');
  const hostControl=process.platform==='win32'?JSON.parse(execFileSync('pwsh',['-NoProfile','-File',path.join(__dirname,'Set-AndroidHostAffinity.ps1'),'-Action','Query','-Serial',serial],{encoding:'utf8'}).replace(/^\uFEFF/,'')):null;
  const hostTimerPolicy=process.platform==='win32'?JSON.parse(execFileSync('pwsh',['-NoProfile','-File',path.join(__dirname,'Set-AndroidTimerPolicy.ps1'),'-Action','Query','-Serial',serial],{encoding:'utf8'}).replace(/^\uFEFF/,'')):null;
  const device=(await android.devices()).find(d=>d.serial()===serial);
  if(!device)throw Error(`Android emulator ${serial} is not online`);
  const shell=async command=>(await device.shell(command)).toString().trim();
  const hz=Number(await shell('getconf CLK_TCK')),online=await shell('cat /sys/devices/system/cpu/online');
  const logicalCores=online.split(',').reduce((n,r)=>{const [a,b=a]=r.split('-').map(Number);return n+b-a+1;},0);
  if(!Number.isInteger(logicalCores)||logicalCores<1||!Number.isFinite(hz)||hz<=0)throw Error('Cannot determine Android CPU core/time units');
  if(await shell('id -u')!=='0')throw Error('Use adb root on this dedicated emulator before reading Chrome process CPU');
  const logMarker=`performance-start-${Date.now()}`;
  await shell(`log -t SingularityPerf ${logMarker}`);
  execFileSync(process.env.ADB_PATH||'adb',['-s',serial,'reverse',`tcp:${url.port||80}`,`tcp:${url.port||80}`],{stdio:'pipe'});
  const context=await device.launchBrowser({viewport:null});
  await context.addInitScript(()=>{try{localStorage.clear();}catch{/* about:blank has no local storage */}});
  const pids=async()=>{
    const output=await shell('ps -A -o PID,NAME');
    return output.split('\n').map(line=>line.trim().split(/\s+/)).filter(([,name])=>name?.startsWith('com.android.chrome')).map(([pid])=>pid);
  };
  const processes=async()=>{
    const snapshotStartTicks=Math.floor(Number((await shell('cat /proc/uptime')).split(/\s+/)[0])*hz);
    if(!Number.isFinite(snapshotStartTicks))throw Error('Cannot determine Android CPU snapshot start');
    const list=await pids(),result=new Map();
    if(!list.length)throw Error('No Android Chrome processes found');
    for(const pid of list){const stat=parseProcStat(await shell(`cat /proc/${pid}/stat`),hz);result.set(stat.key,stat.cpuSeconds);}
    const cpu=(await shell('cat /proc/stat')).split('\n')[0].trim().split(/\s+/).slice(1).map(Number);
    result.counters={clocksource:await shell('cat /sys/devices/system/clocksource/clocksource0/current_clocksource'),source:'Android /proc PID utime+stime; CPU seconds already sum threads',clockTicksPerSecond:hz,snapshotStartTicks,online,systemTicks:cpu.slice(0,8).reduce((a,b)=>a+b,0),idleTicks:cpu[3]+cpu[4]};
    return result;
  };
  const memory=async()=>{
    // One ADB round trip instead of one per process: polling itself must not
    // introduce repeated scheduling/transport overhead into every game second.
    const data=await shell('ps -A -o PID,NAME | while read memoryPid memoryName; do case "$memoryName" in com.android.chrome*) printf "PID %s\\n" "$memoryPid"; cat "/proc/$memoryPid/smaps_rollup";; esac; done');
    return parsePssSnapshot(data);
  };
  const nativeUi=async(dismissHelp=false)=>{
    const dump=async()=>{await shell('uiautomator dump /sdcard/performance-ui.xml');return shell('cat /sdcard/performance-ui.xml');};
    const initial=await dump();let xml=initial,state=inspectNativeUi(xml),dismissed=false;
    if(dismissHelp&&state.immersiveHelp){await shell(`input tap ${state.tap.join(' ')}`);await new Promise(r=>setTimeout(r,500));xml=await dump();state=inspectNativeUi(xml);dismissed=true;}
    if(!state.clean)throw Error(`Android native overlay blocks the game: ${JSON.stringify(state)}`);
    return {initial,xml,dismissed};
  };
  const clocksource=await shell('cat /sys/devices/system/clocksource/clocksource0/current_clocksource'),availableClocksources=(await shell('cat /sys/devices/system/clocksource/clocksource0/available_clocksource')).split(/\s+/);
  const emulatorGraphics={hostGpuMode:hostControl?.graphics?.hostGpuMode??null,vulkanDisabled:hostControl?.graphics?.vulkanDisabled??null,hostFeatureOverrides:hostControl?.graphics?.featureOverrides??null,hostTransportConfig:hostControl?.graphics?.transportConfig??null,guestEgl:await shell('getprop ro.hardware.egl'),guestBootEgl:await shell('getprop ro.boot.hardwareegl'),guestHwuiRenderer:await shell('getprop debug.hwui.renderer'),guestVulkan:await shell('getprop ro.hardware.vulkan'),guestGlTransport:await shell('getprop ro.boot.qemu.gltransport.name'),guestGlDrawFlushInterval:await shell('getprop ro.boot.qemu.gltransport.drawFlushInterval'),guestVsync:await shell('getprop ro.boot.qemu.vsync'),bluetoothOn:await shell('settings get global bluetooth_on')};
  return {context,device,logicalCores,processes,memory,hostControl,hostTimerPolicy,nativeUi,graphicsLog:async()=>parseGraphicsLog(await shell('logcat -b main -d -v brief -s chromium SingularityPerf'),logMarker),environment:{backend:'android-emulator',serial,emulatorGraphics,clocksource,availableClocksources,model:await shell('getprop ro.product.model'),androidRelease:await shell('getprop ro.build.version.release'),api:await shell('getprop ro.build.version.sdk'),abi:await shell('getprop ro.product.cpu.abi'),online,logicalCores,clockTicksPerSecond:hz,wmSize:await shell('wm size'),wmDensity:await shell('wm density'),...(hostControl?{hostAffinity:hostControl.affinity,hostPriority:hostControl.priority}:{}),...(hostTimerPolicy?{hostTimerPolicy:{version:hostTimerPolicy.version,controlMask:hostTimerPolicy.controlMask,stateMask:hostTimerPolicy.stateMask}}:{})},close:async()=>{await context.close();await device.shell('am force-stop com.android.chrome');await device.close();}};
}
function parsePssSnapshot(text){
 const parts=text.split(/^PID (\d+)\r?$/m),perProcess=[];
 for(let i=1;i<parts.length;i+=2){const match=parts[i+1].match(/^Pss:\s+(\d+)\s+kB/m);if(!match)throw Error(`Cannot read Android Chrome PSS for ${parts[i]}`);perProcess.push({pid:parts[i],pssBytes:Number(match[1])*1024});}
 if(!perProcess.length||new Set(perProcess.map(p=>p.pid)).size!==perProcess.length)throw Error('Incomplete Android Chrome PSS snapshot');
 return {chromeProcessPssBytes:perProcess.reduce((n,p)=>n+p.pssBytes,0),perProcess};
}
module.exports={openAndroid,parseProcStat,parseGraphicsLog,inspectNativeUi,parsePssSnapshot};
