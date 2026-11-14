/* Gate exported physical-device measurements; never invent missing telemetry. */
const fs=require('node:fs');
const {cpuUsage,median}=require('./metrics.cjs');
const budget=require('./budget.json');
function evaluateDeviceReport(report){
 const errors=[],warnings=[],rows=report.runs||[],required=['idle','run','combat','move-combat'];
 if(report.platform!=='TapTap')errors.push('physical TapTap environment required');
 if(!report.device||!report.os||!report.appId||!report.telemetrySource)errors.push('missing physical device identity/telemetry provenance');
 if(report.energySource!=='measured-mWh'&&report.energySource!=='device-battery-delta')errors.push('energy requires measured mWh or device battery delta; OS app-share is invalid');
 for(const build of ['baseline','candidate'])if(new Set(rows.filter(r=>r.build===build).map(r=>r.buildHash)).size>1)errors.push(`${build}: multiple build hashes in one comparison`);
 for(const r of rows){
  const label=`${r.build}/${r.mode}/${r.family||''}`;
  if(!Number.isFinite(r.durationSeconds)||r.durationSeconds<900)errors.push(`${label}: at least 15 minutes required`);
  if(r.targetFps!==60||r.charging!==false||!Number.isFinite(r.brightnessPercent)||!Number.isFinite(r.ambientCelsius)||!Number.isFinite(r.startBatteryPercent))errors.push(`${label}: missing controlled conditions`);
  if(!Number.isFinite(r.fps)||!Number.isFinite(r.p99Ms)||!Number.isFinite(r.over33Ratio)||!Number.isFinite(r.energy)||r.energy<=0)errors.push(`${label}: missing frame/energy measurements`);
  if(!Number.isFinite(r.minOneSecondFps)||r.minOneSecondFps<0)errors.push(`${label}: missing minimum 1-second FPS`);
  if(!Number.isFinite(r.peakProcessMemoryBytes)||r.peakProcessMemoryBytes<=0||!r.memorySource||!Number.isFinite(r.memorySampleIntervalMs)||r.memorySampleIntervalMs<=0||r.memorySampleIntervalMs>budget.memorySampleIntervalMs)errors.push(`${label}: missing peak process memory/provenance at 1-second cadence`);
  if(r.build==='candidate'){
   if(r.fps<budget.minimumFps||r.minOneSecondFps<budget.minimumFps)errors.push(`${label}: FPS below floor 50`);
   if(r.peakProcessMemoryBytes>budget.maximumProcessMemoryBytes)errors.push(`${label}: process memory exceeds 1000MB hard limit`);
   if(r.peakProcessMemoryBytes>budget.targetProcessMemoryBytes)warnings.push(`${label}: process memory exceeds 800MB optimization target`);
  }
  if(!Number.isFinite(r.temperatureStartCelsius)||!Number.isFinite(r.temperatureEndCelsius))errors.push(`${label}: missing temperature measurement`);
  if(!r.buildHash||!r.route||!r.quality||!r.rawEvidencePaths?.length)errors.push(`${label}: missing build/route/raw evidence`);
  if(report.energySource==='device-battery-delta'&&(!Number.isFinite(r.endBatteryPercent)||r.startBatteryPercent-r.endBatteryPercent<=0||Math.abs(r.energy-(r.startBatteryPercent-r.endBatteryPercent))>.01))errors.push(`${label}: energy must equal start minus end device battery percentage`);
  if(!Number.isFinite(r.cpuNormalizedPercent)||r.cpuNormalizedPercent<0||r.cpuNormalizedPercent>100)errors.push(`${label}: missing or invalid normalized CPU usage`);
  else try{r.cpu=cpuUsage(r.cpuNormalizedPercent/100*r.logicalCores*r.durationSeconds,r.durationSeconds,r.logicalCores);}catch{errors.push(`${label}: invalid normalized CPU/cores`);}
 }
 const summary=[];
 for(const mode of required)for(const family of mode.includes('combat')?['WAR','BOW','FIR','THU']:['']){
  const before=rows.filter(r=>r.build==='baseline'&&r.mode===mode&&(r.family||'')===family),after=rows.filter(r=>r.build==='candidate'&&r.mode===mode&&(r.family||'')===family),label=`${mode}/${family}`;
  if(before.length<2||after.length<2){errors.push(`${label}: need two valid runs per build (ABBA)`);continue;}
  const ordered=rows.filter(r=>r.mode===mode&&(r.family||'')===family).map(r=>r.build);
  if(ordered.length%4||ordered.some((_,i)=>i%4===0&&!['baseline,candidate,candidate,baseline','candidate,baseline,baseline,candidate'].includes(ordered.slice(i,i+4).join(','))))errors.push(`${label}: runs must be chronological ABBA or BAAB blocks`);
  const controls=r=>JSON.stringify([r.targetFps,r.charging,r.brightnessPercent,r.ambientCelsius,r.startBatteryPercent,r.quality,r.route]);
  if(new Set([...before,...after].map(controls)).size!==1){errors.push(`${label}: conditions differ`);continue;}
  if(Math.max(...[...before,...after].map(r=>r.temperatureStartCelsius))-Math.min(...[...before,...after].map(r=>r.temperatureStartCelsius))>1)errors.push(`${label}: initial temperature differs >1C`);
  const energy=rs=>median(rs.map(r=>r.energy/r.durationSeconds*3600)),b=energy(before),a=energy(after);
  const cpu=rs=>median(rs.map(r=>r.cpu?.corePercent)),peak=rs=>Math.max(...rs.map(r=>r.peakProcessMemoryBytes));
  summary.push({mode,family,baselineEnergyPerHour:b,candidateEnergyPerHour:a,energySource:report.energySource,changePercent:(a/b-1)*100,baselineCpuCorePercent:cpu(before),candidateCpuCorePercent:cpu(after),candidatePeakMemoryMB:peak(after)/1e6,candidateMinOneSecondFps:Math.min(...after.map(r=>r.minOneSecondFps))});
  if(cpu(after)>cpu(before)*budget.cpuRegressionRatio+budget.cpuCoreNoisePercent)errors.push(`${label}: CPU usage regression >15% +3 core percentage points`);
  if(peak(after)>peak(before)*budget.memoryRegressionRatio+budget.memoryRegressionNoiseBytes)errors.push(`${label}: process memory regression >15% +32MB`);
  if(a>b*1.05)errors.push(`${label}: energy regression >5%`);
  if(median(after.map(r=>r.fps))<median(before.map(r=>r.fps))*.95)errors.push(`${label}: FPS regression >5%`);
  if(median(after.map(r=>r.p99Ms))>median(before.map(r=>r.p99Ms))*1.15+2)errors.push(`${label}: p99 regression`);
  if(median(after.map(r=>r.temperatureEndCelsius-r.temperatureStartCelsius))>median(before.map(r=>r.temperatureEndCelsius-r.temperatureStartCelsius))+2)errors.push(`${label}: temperature rise regression >2C`);
 }
 return {status:errors.length?'failed':'passed',budget,errors,warnings,summary};
}
if(require.main===module){const filename=process.argv[2];if(!filename)throw Error('Usage: node tools/performance/device-gate.cjs physical-device.json');const result=evaluateDeviceReport(JSON.parse(fs.readFileSync(filename,'utf8')));console.log(JSON.stringify(result,null,2));if(result.status!=='passed')process.exitCode=1;}
module.exports={evaluateDeviceReport};
