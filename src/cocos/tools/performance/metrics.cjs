const crypto = require('node:crypto');
const fs=require('node:fs'),path=require('node:path');
const budget=require('./budget.json');
const {memoryBudget,validateMemoryCoverage}=require('./resources.cjs');
const quantile = (sorted, q) => sorted[Math.min(sorted.length-1,Math.ceil(sorted.length*q)-1)] ?? null;
const median = values => quantile([...values].sort((a,b)=>a-b),.5);
// Cocos3.8.8 WebGL2 reports TRIANGLES as indexCount/3 without rounding.
// Preserve the native fractional estimate; draw-call counts remain integers.
const validRenderCounter=(key,value)=>Number.isFinite(value)&&value>=0&&value<=Number.MAX_SAFE_INTEGER&&(key!=='drawCalls'||Number.isSafeInteger(value));

// Task-manager-style percentages divide by all logical CPUs. Keep that display
// and its N-times core equivalent together; raw CPU seconds already sum cores.
function cpuUsage(cpuSeconds, wallSeconds, logicalCores) {
  if(!Number.isFinite(cpuSeconds)||cpuSeconds<0||!Number.isFinite(wallSeconds)||wallSeconds<=0||!Number.isInteger(logicalCores)||logicalCores<1)throw Error('Invalid CPU sample');
  const normalizedPercent=cpuSeconds/wallSeconds/logicalCores*100;
  return {cpuSeconds,logicalCores,normalizedPercent,corePercent:normalizedPercent*logicalCores,coreEquivalents:normalizedPercent*logicalCores/100};
}
function processCpuDelta(before,after) {
  let seconds=0;
  for(const [key,value]of after){
    let initial=before.get(key);
    if(initial===undefined){
      const start=Number(/^\d+:(\d+)$/.exec(String(key))?.[1]);
      if(!Number.isFinite(before.counters?.snapshotStartTicks)||!Number.isFinite(start)||start<before.counters.snapshotStartTicks)throw Error(`CPU process ${key} appeared with unknown pre-window CPU; rerun`);
      // A process born inside this Android window starts its own utime/stime
      // counters at zero. Include its full CPU time, never silently drop it.
      initial=0;
    }
    if(!Number.isFinite(value)||!Number.isFinite(initial)||value<initial)throw Error(`Invalid CPU counter for process ${key}`);
    seconds+=value-initial;
  }
  for(const key of before.keys())if(!after.has(key))throw Error(`CPU process ${key} exited during sample; final CPU is unknown; rerun`);
  return seconds;
}
function summarize(sample) {
  if(!Array.isArray(sample.frames)||sample.frames.some(n=>!Number.isFinite(n)||n<=0))throw Error('Invalid rendered frame intervals');
  if(!Number.isFinite(sample.mainThreadCpuSeconds)||sample.mainThreadCpuSeconds<0)throw Error('Invalid main-thread CPU counter');
  const sorted=[...sample.frames].sort((a,b)=>a-b),n=sorted.length;
  if(!n)throw Error('No rendered frames');
  const clock=sample.frameClock,lastDrawMs=clock?.firstDrawMs+sample.frames.reduce((sum,dt)=>sum+dt,0);
  if(clock?.schema!=='render-window-clock-v1'||![clock.durationMs,clock.firstDrawMs,clock.lastDrawMs].every(Number.isFinite)||clock.firstDrawMs<0||clock.durationMs<=0||clock.drawCount!==n+1||Math.abs(lastDrawMs-clock.lastDrawMs)>1e-5||clock.lastDrawMs>clock.durationMs+1e-5)throw Error('Invalid or incomplete rendered-window clock');
  const renderStats={schema:'render-counter-series-v1',samples:n};
  for(const key of ['drawCalls','triangles']){
    const values=sample.renderCounters?.[key];
    if(!Array.isArray(values)||values.length!==n||values.some(v=>!validRenderCounter(key,v)))throw Error(`Invalid or incomplete per-frame ${key}`);
    const ordered=[...values].sort((a,b)=>a-b);renderStats[key]={min:ordered[0],p50:quantile(ordered,.5),p95:quantile(ordered,.95),max:ordered.at(-1)};
  }
  return {...sample,frames:undefined,renderCounters:undefined,renderStats,endFrameDrawCalls:sample.drawCalls,endFrameTriangles:sample.triangles,drawCalls:renderStats.drawCalls.p50,drawCallsP95:renderStats.drawCalls.p95,triangles:renderStats.triangles.p50,trianglesP95:renderStats.triangles.p95,intervalCount:n,frameCount:clock.drawCount,fps:clock.drawCount/sample.wallSeconds,minOneSecondFps:minimumWindowFps(sample.frames,clock),p50Ms:quantile(sorted,.5),p95Ms:quantile(sorted,.95),p99Ms:quantile(sorted,.99),maxMs:Math.max(sorted[n-1],clock.firstDrawMs,clock.durationMs-clock.lastDrawMs),over33Ratio:sorted.filter(n=>n>1000/30+1).length/n,over50Ratio:sorted.filter(n=>n>50).length/n,over100Count:sorted.filter(n=>n>100).length+(clock.firstDrawMs>100?1:0)+(clock.durationMs-clock.lastDrawMs>100?1:0),mainThreadMsPerFrame:sample.mainThreadCpuSeconds*1000/clock.drawCount,cpu:cpuUsage(sample.processCpuSeconds,sample.wallSeconds,sample.logicalCores)};
}
function minimumWindowFps(frames,clock){
 const times=[clock?.firstDrawMs??0];for(const dt of frames)times.push(times.at(-1)+dt);
 const duration=clock?.durationMs??times.at(-1);
 if(duration<budget.fpsWindowMs)return null;
 let left=0,right=0,minimum=Infinity;
 // A window loses a frame when that frame passes its left edge. Checking only
 // arrival times misses the lower count immediately before the next draw.
 // Count (end-window, end] at every departure within the measured timeline.
 const inspect=end=>{
  while(left<times.length&&times[left]<=end-budget.fpsWindowMs+1e-7)left++;
  while(right<times.length&&times[right]<=end+1e-7)right++;
  minimum=Math.min(minimum,(right-left)*1000/budget.fpsWindowMs);
 };
 inspect(budget.fpsWindowMs);
 for(const t of times){const end=t+budget.fpsWindowMs;if(end>duration+1e-7)break;inspect(end);}
 // Include the final unrendered tail instead of truncating at the last draw.
 inspect(duration);
 return Number.isFinite(minimum)?minimum:null;
}
function validateSample(s, seconds,performanceGates=true) {
  const errors=[];
  for(const key of ['wallSeconds','simulationSeconds','frameCount','fps','p95Ms','p99Ms','maxMs','over33Ratio','mainThreadMsPerFrame','drawCalls','drawCallsP95','triangles','trianglesP95'])if(!Number.isFinite(s[key])||s[key]<0)errors.push(`invalid metric ${key}`);
  const render=s.renderStats;
  if(render?.schema!=='render-counter-series-v1'||render.samples!==s.intervalCount||s.intervalCount!==s.frameCount-1||!Number.isInteger(render.samples)||render.samples<1)errors.push('invalid per-frame rendering coverage');
  const clock=s.frameClock;
  if(clock?.schema!=='render-window-clock-v1'||![clock.durationMs,clock.firstDrawMs,clock.lastDrawMs].every(Number.isFinite)||clock.firstDrawMs<0||clock.lastDrawMs<clock.firstDrawMs||clock.lastDrawMs>clock.durationMs+1e-5||clock.drawCount!==s.frameCount||clock.durationMs<s.wallSeconds*950||clock.durationMs>s.wallSeconds*1050)errors.push('invalid rendered-window clock coverage');
  for(const key of ['drawCalls','triangles']){
    const r=render?.[key];
    if(!r||![r.min,r.p50,r.p95,r.max].every(value=>validRenderCounter(key,value))||r.min>r.p50||r.p50>r.p95||r.p95>r.max||r.p95<=0||r.p50!==s[key]||r.p95!==s[key+'P95'])errors.push(`invalid temporal ${key} statistics`);
  }
  if(!Number.isFinite(s.minOneSecondFps)||s.minOneSecondFps<0)errors.push('invalid metric minOneSecondFps');
  const c=s.cpu;
  if(!c||!Number.isInteger(c.logicalCores)||c.logicalCores<1||!Number.isFinite(c.normalizedPercent)||c.normalizedPercent<0||!Number.isFinite(c.corePercent)||c.corePercent<0||Math.abs(c.corePercent-c.normalizedPercent*c.logicalCores)>1e-6)errors.push('invalid CPU usage/core conversion');
  const m=s.processMemory;
  if(!m||!m.source||!Number.isInteger(m.samples)||m.samples<1||!Number.isFinite(m.peakBytes)||m.peakBytes<=0||!Number.isFinite(m.maxGapMs)||m.maxGapMs>budget.maximumMemorySampleGapMs)errors.push('invalid or incomplete process memory measurements');
  if(s.expectedArea&&s.area!==s.expectedArea)errors.push('scene changed during measurement');
  if(s.wallSeconds<seconds*.95)errors.push('measurement too short');
  if(s.frameRate!==60)errors.push('60 FPS setting changed');
  if(s.frameCount<2)errors.push('too few rendered frames to measure');
  if(s.simulationSeconds<s.wallSeconds*.85)errors.push('simulation paused, dead, or severely stalled');
  if(s.status!=='playing')errors.push('player died');
  if(s.mode.includes('combat')) {
    if((s.events.hit||0)+(s.events.skill_hit||0)<1)errors.push('no actual damage/hit events');
    if((s.events.action||0)+(s.events.skill_release||0)<1)errors.push('no attack/release events');
    if(s.skills!==false&&!(s.events.skill_release>0))errors.push('no skill release events');
    if(s.actionFrames<s.frameCount*.2)errors.push('insufficient attack coverage');
    if(s.family==='BOW'&&!(s.events.projectile>0||s.events.skill_release>0))errors.push('bow never released');
  }
  if(s.mode==='run'||s.mode==='move-combat') {
    if(s.movedMetres<seconds*.25)errors.push('pilot did not actually move');
    if(s.movingFrames<s.frameCount*.5)errors.push('insufficient movement coverage');
  }
  if(!performanceGates)return errors;
  if(s.frameCount<seconds*20)errors.push('too few rendered frames');
  if(s.fps<budget.minimumFps)errors.push('FPS below absolute floor 50');
  if(s.minOneSecondFps<budget.minimumFps)errors.push('1-second FPS below floor 50');
  if(m?.peakBytes>budget.maximumProcessMemoryBytes)errors.push('observed process memory exceeds 1000MB hard limit');
  if(s.p99Ms>80)errors.push('p99 exceeds 80ms');
  if(s.maxMs>250)errors.push('single rendered frame exceeds 250ms');
  if(s.mainThreadMsPerFrame>budget.maximumMainThreadMsPerFrame)errors.push('main-thread CPU exceeds frame budget');
  return errors;
}
function validateReference(report,caseIds,seconds,repeats,allowPerformanceFailure=false){
 const errors=[];
 if(!['passed','failed'].includes(report.status)||!Array.isArray(report.samples))return ['reference is not a completed measured run'];
 if(report.budgetHash!==fingerprint(budget))errors.push('reference resource budget mismatch');
 if(report.measurementHash!==measurementHash())errors.push('reference measurement harness mismatch');
 if(typeof report.workloadRulesHash!=='string'||!/^[a-f0-9]{64}$/.test(report.workloadRulesHash))errors.push('reference lacks a workload rules fingerprint');
 const memory=memoryBudget(report.memoryObservations),coverage=validateMemoryCoverage(report.memoryObservations,report.memoryMonitoring?.startedMs,report.memoryMonitoring?.finishedMs);
 errors.push(...coverage.map(e=>`reference memory telemetry: ${e}`));
 if(!allowPerformanceFailure)errors.push(...memory.errors.map(e=>`reference memory budget: ${e}`));
 if(report.environment?.backend==='android-emulator'&&(report.nativeGraphicsChecked!==true||!Array.isArray(report.nativeGraphicsErrors)||report.nativeGraphicsErrors.length))errors.push('Android reference lacks a clean native graphics log check');
 if(report.environment?.backend==='android-emulator'&&report.nativeUiChecked!==true)errors.push('Android reference lacks an unobstructed native UI check');
 if(!allowPerformanceFailure&&(report.status!=='passed'||report.renderSettings?.usesCustomPipeline!==false))errors.push('approved baseline must pass gates and the legacy rendering policy');
 if(!allowPerformanceFailure&&(report.profileCpu||report.trace||report.diagnostic))errors.push('approved baseline must not contain diagnostic profiler/tracing/host-experiment runs');
 if(report.seconds!==seconds||report.repeats!==repeats||report.samples.length!==caseIds.length*repeats)errors.push('reference has incomplete duration/case/repetition coverage');
 const seen=new Set(),allowedFailures=new Set();
 for(const s of report.samples){
  const key=`${s.round+1}-${s.id}`;
  if(!caseIds.includes(s.id)||!Number.isInteger(s.round)||s.round<0||s.round>=repeats||seen.has(key))errors.push(`${key}: unexpected or duplicated reference window`);
  seen.add(key);
  errors.push(...validateSample(s,seconds,!allowPerformanceFailure).map(e=>`${key}: ${e}`));
  for(const error of validateSample(s,seconds))allowedFailures.add(`${key}: ${error}`);
 }
 for(const error of memory.errors)if(error.includes('hard limit'))allowedFailures.add(`Resource budget: ${error}`);
 for(const error of report.errors||[])if(!allowPerformanceFailure||!allowedFailures.has(error))errors.push(`reference runtime/integrity error: ${error}`);
 return errors;
}
function aggregate(samples) {
  const groups={};
  for(const s of samples)(groups[s.id]??=[]).push(s);
  return Object.fromEntries(Object.entries(groups).map(([id,rows])=>[id,{windows:rows.length,...Object.fromEntries(['fps','p95Ms','p99Ms','over33Ratio','mainThreadMsPerFrame','processCpuSeconds','drawCalls','drawCallsP95','triangles','trianglesP95'].map(k=>[k,median(rows.map(s=>s[k]))])),minOneSecondFps:Math.min(...rows.map(s=>s.minOneSecondFps)),peakProcessMemoryBytes:Math.max(...rows.map(s=>s.processMemory?.peakBytes??0)),normalizedCpuPercent:median(rows.map(s=>s.cpu.normalizedPercent)),corePercent:median(rows.map(s=>s.cpu.corePercent)),coreEquivalents:median(rows.map(s=>s.cpu.corePercent))/100,maxMs:Math.max(...rows.map(s=>s.maxMs)),over100Count:rows.reduce((n,s)=>n+(s.over100Count||0),0),hits:rows.reduce((n,s)=>n+(s.events.hit||0),0)}]));
}
function compare(candidate, baseline) {
  const errors=[];
  if(candidate.protocol!==baseline.protocol)return ['baseline environment/protocol mismatch'];
  if(candidate.workloadRulesHash!==baseline.workloadRulesHash)return ['baseline workload rules mismatch'];
  if(candidate.fingerprint!==baseline.fingerprint)return ['baseline environment/protocol mismatch'];
  if(candidate.budgetHash!==baseline.budgetHash)return ['baseline resource budget mismatch'];
  if(candidate.measurementHash!==baseline.measurementHash)return ['baseline measurement harness mismatch'];
  if((candidate.emulation||'desktop')!==(baseline.emulation||'desktop'))return ['baseline device-emulation mismatch'];
  if(!!candidate.profileCpu!==!!baseline.profileCpu)return ['baseline profiler instrumentation mismatch'];
  if(!!candidate.trace!==!!baseline.trace)return ['baseline trace instrumentation mismatch'];
  if(!!candidate.diagnostic!==!!baseline.diagnostic)return ['baseline diagnostic mode mismatch'];
  if(candidate.profile!==baseline.profile||candidate.seconds!==baseline.seconds||candidate.repeats!==baseline.repeats)return ['baseline duration/repetition/profile mismatch'];
  const current=aggregate(candidate.samples),prior=aggregate(baseline.samples);
  for(const [id,b] of Object.entries(prior)) {
    const a=current[id];if(!a){errors.push(`${id}: missing case`);continue;}
    if(a.windows!==b.windows)errors.push(`${id}: window count changed`);
    for(const [metric,ratio,noise] of [['mainThreadMsPerFrame',budget.cpuRegressionRatio,budget.cpuFrameNoiseMs],['corePercent',budget.cpuRegressionRatio,budget.cpuCoreNoisePercent],['peakProcessMemoryBytes',budget.memoryRegressionRatio,budget.memoryRegressionNoiseBytes],['p99Ms',1.2,2],['drawCalls',1.1,5],['drawCallsP95',1.1,5],['triangles',1.1,1000],['trianglesP95',1.1,1000]])if(a[metric]>b[metric]*ratio+noise)errors.push(`${id}: ${metric} regression ${b[metric].toFixed(2)} -> ${a[metric].toFixed(2)}`);
    if(a.over33Ratio>b.over33Ratio+.03)errors.push(`${id}: long-frame ratio +3pp`);
    if(a.over100Count>b.over100Count+1)errors.push(`${id}: repeated >100ms stalls increased`);
    if(a.fps<b.fps*.9)errors.push(`${id}: FPS decreased >10%`);
  }
  for(const id of Object.keys(current))if(!prior[id])errors.push(`${id}: missing baseline`);
  return errors;
}
// PowerShell maps may serialize identical settings in a different key order.
// Preserve array order and every value while canonicalizing object keys.
const fingerprint = value => crypto.createHash('sha256').update(JSON.stringify(value,(_key,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.keys(item).sort().map(key=>[key,item[key]])):item)).digest('hex');
const measurementHash=()=>fingerprint(Object.fromEntries(['run.cjs','metrics.cjs','resources.cjs','android.cjs','cases.json','budget.json','page-driver.cjs','Set-AndroidHostAffinity.ps1','Set-AndroidTimerPolicy.ps1'].map(file=>[file,fingerprint(fs.readFileSync(path.join(__dirname,file),'utf8'))])));
module.exports={cpuUsage,processCpuDelta,summarize,minimumWindowFps,validateSample,validateReference,aggregate,compare,fingerprint,median,measurementHash};
