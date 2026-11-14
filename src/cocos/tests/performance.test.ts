import {test} from 'node:test';
import assert from 'node:assert/strict';
const {cpuUsage,processCpuDelta,summarize,minimumWindowFps,validateSample,validateReference,compare,fingerprint,measurementHash}=require('../tools/performance/metrics.cjs');
const {memoryBudget,validateMemoryCoverage,windowMemory,monitorMemory}=require('../tools/performance/resources.cjs');
const budget=require('../tools/performance/budget.json');
const processMemory={source:'synthetic-test-only PSS',samples:10,peakBytes:700000000,maxGapMs:1000};
const renderCounters=(n:number)=>({drawCalls:Array(n).fill(100),triangles:Array(n).fill(1000)});
const frameClock=(frames:number[],durationMs:number)=>({schema:'render-window-clock-v1',durationMs,firstDrawMs:0,lastDrawMs:frames.reduce((n,dt)=>n+dt,0),drawCount:frames.length+1});
const memoryObservations=Array.from({length:11},(_,i)=>({source:'synthetic-test-only PSS',processMemoryBytes:700000000,startedMs:i*1000,finishedMs:i*1000+1}));
const {evaluateDeviceReport}=require('../tools/performance/device-gate.cjs');
const {parseProcStat,parseGraphicsLog,inspectNativeUi,parsePssSnapshot}=require('../tools/performance/android.cjs');
const {assertSourcePolicy,assertBuildPolicy,assertEnginePolicy,assertMinigameEntryPolicy}=require('../tools/render-policy.cjs');
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {useBakedAnimation} from '../assets/scripts/features/actors/common/AnimationMode';
test('moving ranged attacks retain one evaluator through ready combat gaps and release it for exploration',()=>{
 const mode={realtime:false};
 assert.equal(useBakedAnimation(mode,false,false),true);
 assert.equal(useBakedAnimation(mode,true,true),false);
 for(let i=0;i<10;i++)assert.equal(useBakedAnimation(mode,i%2===0,true),false);
 assert.equal(useBakedAnimation(mode,false,false),true);
 assert.equal(useBakedAnimation(mode,true,false),false,'authored melee always uses real-time evaluation');
});
test('active and migrated engine settings and generated builds cannot silently restore CRP',()=>{
 const settings=JSON.parse(fs.readFileSync(path.join(__dirname,'../settings/v2/packages/engine.json'),'utf8'));
 assert.doesNotThrow(()=>assertSourcePolicy(settings));
 const reverted=structuredClone(settings);reverted.modules.configs[reverted.modules.globalConfigKey].cache['render-pipeline']._option='custom-pipeline';assert.throws(()=>assertSourcePolicy(reverted));
 assert.doesNotThrow(()=>assertBuildPolicy({CocosEngine:'3.8.8',rendering:{customPipeline:false}}));assert.throws(()=>assertBuildPolicy({CocosEngine:'3.8.8',rendering:{customPipeline:true}}));
 const stripped='System.register([], (function (publish) {return {execute:function(){if(cc.WebGL2Device)use(cc.WebGL2Device);}}}));';
 assert.throws(()=>assertEnginePolicy(stripped),/missing the WebGL 2 backend/,'DeviceManager references alone cannot prove a renderer exists');
 const webgl2='System.register([], (function (publish) {return {execute:function(){publish("WebGL2Device",function Device(){});}}}));';
 assert.doesNotThrow(()=>assertEnginePolicy(webgl2));
 assert.throws(()=>assertEnginePolicy(webgl2.replace('publish("WebGL2Device",','publish("WebGLDevice",')),/missing the WebGL 2 backend/);
 assert.doesNotThrow(()=>assertMinigameEntryPolicy("firstScreen.start('default','default','true').then(start)"));
 assert.throws(()=>assertMinigameEntryPolicy("firstScreen.start('default','default','false').then(start)"),/WebGL 2 context/);
});
test('CPU normalizes across all cores and restores core-equivalent load exactly once',()=>{
 const cpu=cpuUsage(12,10,8);assert.equal(cpu.normalizedPercent,15);assert.equal(cpu.corePercent,120);assert.equal(cpu.coreEquivalents,1.2);
 assert.throws(()=>cpuUsage(1,0,8));assert.throws(()=>cpuUsage(1,10,0));
});
test('Android process CPU reads utime and stime once and handles spaces in proc names',()=>{
 const fields=Array(22).fill('0');fields[0]='S';fields[11]='25';fields[12]='15';fields[13]='999';fields[14]='999';fields[19]='12345';
 const stat=parseProcStat(`42 (chrome renderer) ${fields.join(' ')}`,100);
 assert.equal(stat.key,'42:12345');assert.equal(stat.cpuSeconds,.4);assert.equal(stat.ticks,40);
 assert.throws(()=>parseProcStat('not a proc record',100));
});
test('CPU includes Android processes born within the window and rejects missing or untraceable counters',()=>{
 const before:any=new Map([['42:10',2]]);before.counters={snapshotStartTicks:100};
 assert.equal(processCpuDelta(before,new Map([['42:10',3],['43:105',.5]])),1.5);
 assert.throws(()=>processCpuDelta(before,new Map([['42:10',3],['43:99',.5]])),/unknown pre-window/);
 assert.throws(()=>processCpuDelta(before,new Map([['42:101',.5]])),/exited/,'PID reuse cannot conceal the exited process CPU');
 assert.throws(()=>processCpuDelta(before,new Map([['42:10',1]])),/Invalid CPU counter/);
 assert.throws(()=>processCpuDelta(new Map([['42',2]]),new Map([['42',3],['43',.5]])),/unknown pre-window/,'desktop process birth without a timestamp stays invalid');
});
test('Android native graphics errors and GPU restarts cannot be hidden by an empty page console',()=>{
 const marker='performance-start-fixture',log=`old GL ERROR\nI/SingularityPerf: ${marker}\nI/chromium: normal startup\nE/chromium: GL ERROR :GL_INVALID_OPERATION : glDrawElements out of range\nE/chromium: GPU process exited unexpectedly: exit_code=0\nW/chromium: The GPU process has crashed 1 time(s)`;
 assert.equal(parseGraphicsLog(log,marker).errors.length,3);
 assert.deepEqual(parseGraphicsLog(`I/SingularityPerf: ${marker}\nI/chromium: normal startup`,marker).errors,[]);
 assert.throws(()=>parseGraphicsLog(log,'missing-marker'),/marker/);
});
test('native full-screen guidance is acknowledged only by its known system button and other overlays fail',()=>{
 assert.equal(inspectNativeUi('<node package="com.android.chrome" class="android.view.View" />').clean,true);
 assert.deepEqual(inspectNativeUi('<node resource-id="android:id/immersive_cling_title" package="android" /><node resource-id="android:id/ok" package="android" clickable="true" enabled="true" bounds="[1392,530][1656,674]" />').tap,[1524,602]);
 const other=inspectNativeUi('<node resource-id="android:id/ok" package="android" class="android.widget.Button" text="Erase" />');assert.equal(other.clean,false);assert.equal(other.immersiveHelp,false);assert.equal(other.tap,undefined);
 assert.throws(()=>inspectNativeUi('<hierarchy />'),/empty/);
});
test('static mesh caches with stale vertex and index offsets are rebuilt without changing native geometry',()=>{
 const root=path.resolve(__dirname,'../temp'),dir=fs.mkdtempSync(path.join(root,'mesh-cache-rule-')),uid='fixture-mesh',library=path.join(dir,'library/fi'),cache=path.join(dir,`temp/asset-db/assets/fi/${uid}/build1.0.1`);
 try{
  fs.mkdirSync(library,{recursive:true});fs.mkdirSync(cache,{recursive:true});
  const structure={primitives:[{vertexBundelIndices:[0]}],vertexBundles:[{view:{offset:0,length:36,count:3,stride:12}}]};
  fs.writeFileSync(path.join(library,uid+'.json'),JSON.stringify({__type__:'cc.Mesh',_hash:7,_struct:structure}));const native=Buffer.alloc(36,3);fs.writeFileSync(path.join(library,uid+'.bin'),native);
  fs.writeFileSync(path.join(cache,'release.json'),JSON.stringify([[0,'.bin',6,[{...structure,vertexBundles:[{view:{offset:0,length:24,count:2,stride:12}}]}]]]));
  const report=JSON.parse(execFileSync('python',[path.resolve(__dirname,'../tools/refresh-morph-build-cache.py'),'--project',dir],{encoding:'utf8'}));
  assert.equal(report.checkedMeshCaches,1);assert.equal(report.checkedMorphCaches,0);assert.equal(report.invalidated.length,1);assert.equal(fs.existsSync(cache),false);
  assert.ok(fs.existsSync(path.join(dir,report.invalidated[0].backup,'release.json')));assert.deepEqual(fs.readFileSync(path.join(library,uid+'.bin')),native);
 }finally{assert.equal(path.dirname(path.resolve(dir)),root);fs.rmSync(dir,{recursive:true,force:true});}
});
test('performance gate catches long frames and stationary or unreleased fake combat',()=>{
 const sample=summarize({frames:[16,16,16,120],frameClock:frameClock([16,16,16,120],1000),renderCounters:renderCounters(4),wallSeconds:1,logicalCores:8,processCpuSeconds:1,mainThreadCpuSeconds:.08,frameRate:60,mode:'move-combat',family:'BOW',simulationSeconds:1,status:'playing',events:{},actionFrames:0,movingFrames:0,movedMetres:0,drawCalls:100,triangles:1000});
 assert.equal(sample.p99Ms,120);assert.equal(sample.over100Count,2,'120ms internal interval plus832ms silent tail');assert.equal(sample.cpu.corePercent,100);
 const errors=validateSample(sample,1);assert.ok(errors.includes('no actual damage/hit events'));assert.ok(errors.includes('bow never released'));assert.ok(errors.includes('pilot did not actually move'));assert.ok(errors.includes('p99 exceeds 80ms'));
});
test('invalid counters, missing metrics and unexpected scene travel cannot produce green performance samples',()=>{
 assert.throws(()=>summarize({frames:[16,NaN],mainThreadCpuSeconds:1}));
 assert.throws(()=>summarize({frames:[16],mainThreadCpuSeconds:undefined}));
 const errors=validateSample({mode:'idle',status:'playing',area:'S01',expectedArea:'U1-06',frameRate:60},20);
 assert.ok(errors.includes('scene changed during measurement'));assert.ok(errors.includes('invalid metric p99Ms'));assert.ok(errors.includes('invalid metric mainThreadMsPerFrame'));
});
test('optimization before-data may expose a real performance failure but cannot hide invalid or incomplete measurements',()=>{
 const s=summarize({id:'battle',round:0,frames:Array(300).fill(33.3),frameClock:frameClock(Array(300).fill(33.3),10000),renderCounters:renderCounters(300),wallSeconds:10,logicalCores:4,processCpuSeconds:10,mainThreadCpuSeconds:2,frameRate:60,mode:'move-combat',family:'BOW',simulationSeconds:10,status:'playing',events:{hit:4,action:5,skill_release:3,projectile:5},actionFrames:250,movingFrames:300,movedMetres:20,drawCalls:100,triangles:1000,processMemory});
 const before={status:'failed',budgetHash:fingerprint(budget),measurementHash:measurementHash(),workloadRulesHash:'0'.repeat(64),memoryObservations,memoryMonitoring:{startedMs:0,finishedMs:10001},seconds:10,repeats:1,samples:[s],errors:['1-battle: FPS below absolute floor 50'],renderSettings:{usesCustomPipeline:true}};
 assert.deepEqual(validateReference(before,['battle'],10,1,true),[]);
 assert.ok(validateReference(before,['battle'],10,1,false).length>0);
 assert.ok(validateReference({...before,status:'passed',errors:[],renderSettings:{usesCustomPipeline:false}},['battle'],10,1,false).some((e:string)=>e.includes('FPS below absolute floor')),'a passed label cannot conceal failing measurements');
 assert.ok(validateReference({...before,status:'passed',profileCpu:true,errors:[],renderSettings:{usesCustomPipeline:false}},['battle'],10,1,false).some((e:string)=>e.includes('diagnostic profiler')));
 assert.ok(validateReference({...before,status:'passed',diagnostic:true,errors:[],renderSettings:{usesCustomPipeline:false}},['battle'],10,1,false).some((e:string)=>e.includes('host-experiment')));
 assert.ok(validateReference({...before,environment:{backend:'android-emulator'}},['battle'],10,1,true).some((e:string)=>e.includes('native graphics')));
 assert.ok(validateReference({...before,samples:[{...s,events:{}}]},['battle'],10,1,true).some((e:string)=>e.includes('no actual damage')));
 assert.ok(validateReference({...before,errors:['unknown runtime crash']},['battle'],10,1,true).some((e:string)=>e.includes('runtime/integrity')));
 assert.ok(validateReference({...before,samples:[]},['battle'],10,1,true).some((e:string)=>e.includes('coverage')));
});
test('regression gate rejects incomparable environments, missing cases and CPU regressions',()=>{
 assert.equal(fingerprint({gpu:{name:'pipe',steps:[4096,800]},cores:4}),fingerprint({cores:4,gpu:{steps:[4096,800],name:'pipe'}}));
 assert.notEqual(fingerprint({steps:[4096,800]}),fingerprint({steps:[800,4096]}));
 assert.notEqual(fingerprint({cores:4}),fingerprint({cores:8}));
 const row={id:'battle',fps:60,p95Ms:17,p99Ms:18,over33Ratio:0,mainThreadMsPerFrame:4,processCpuSeconds:1,cpu:{corePercent:80},drawCalls:100,drawCallsP95:100,triangles:10000,trianglesP95:10000,maxMs:20,events:{hit:1}};
 const baseline={protocol:'v1',fingerprint:'same',profile:'regression',seconds:20,repeats:3,samples:[row]};
 assert.deepEqual(compare(baseline,baseline),[]);
 assert.match(compare({...baseline,fingerprint:'other'},baseline)[0],/mismatch/);
 assert.match(compare({...baseline,profileCpu:true},baseline)[0],/instrumentation mismatch/);
 assert.match(compare({...baseline,trace:true},baseline)[0],/trace instrumentation mismatch/);
 assert.match(compare({...baseline,diagnostic:true},baseline)[0],/diagnostic mode mismatch/);
 assert.match(compare({...baseline,emulation:'iphone14'},baseline)[0],/device-emulation mismatch/);
 assert.match(compare({...baseline,samples:[]},baseline)[0],/missing case/);
 assert.ok(compare({...baseline,samples:[{...row,mainThreadMsPerFrame:7}]},baseline).some((e:string)=>e.includes('mainThreadMsPerFrame regression')));
 assert.ok(compare({...baseline,samples:[{...row,over100Count:2}]},baseline).some((e:string)=>e.includes('repeated >100ms stalls')));
 assert.ok(compare({...baseline,samples:[{...row,processMemory:{peakBytes:850000000}}]},{...baseline,samples:[{...row,processMemory:{peakBytes:700000000}}]}).some((e:string)=>e.includes('peakProcessMemoryBytes regression')));
 assert.ok(compare({...baseline,measurementHash:'changed-sampler'},baseline).some((e:string)=>e.includes('harness mismatch')));
 assert.ok(compare({...baseline,workloadRulesHash:'pursuing-elite'},{...baseline,workloadRulesHash:'stationary-elite'}).some((e:string)=>e.includes('workload rules mismatch')));
});
test('device energy gate rejects OS app-share and incomplete or short physical runs',()=>{
 const result=evaluateDeviceReport({platform:'Chrome',energySource:'os-app-share',runs:[{mode:'move-combat',durationSeconds:60,energy:31}]});
 assert.equal(result.status,'failed');assert.ok(result.errors.some((e:string)=>e.includes('OS app-share')));assert.ok(result.errors.some((e:string)=>e.includes('15 minutes')));assert.ok(result.errors.some((e:string)=>e.includes('ABBA')));
});
test('physical-device gate accepts controlled ABBA data and converts normalized CPU by core count',()=>{
 const runs:any[]=[];
 for(const mode of ['idle','run','combat','move-combat'])for(const family of mode.includes('combat')?['WAR','BOW','FIR','THU']:[''])for(const build of ['baseline','candidate','candidate','baseline'])runs.push({build,buildHash:build,mode,family,durationSeconds:900,targetFps:60,charging:false,brightnessPercent:50,ambientCelsius:22,startBatteryPercent:80,endBatteryPercent:build==='baseline'?75:75.5,quality:'default',route:'synthetic-unit-fixture',fps:60,minOneSecondFps:55,peakProcessMemoryBytes:700000000,memorySource:'synthetic-unit-fixture',memorySampleIntervalMs:1000,p99Ms:20,over33Ratio:0,energy:build==='baseline'?5:4.5,cpuNormalizedPercent:15,logicalCores:8,temperatureStartCelsius:25,temperatureEndCelsius:build==='baseline'?39:37,rawEvidencePaths:['synthetic-unit-fixture-only']});
 const report={platform:'TapTap',device:'synthetic-device',os:'fixture',appId:'fixture',telemetrySource:'synthetic-unit-test',energySource:'device-battery-delta',runs};
 assert.equal(evaluateDeviceReport(report).status,'passed');assert.equal(runs[0].cpu.corePercent,120);
 const wrongOrder={...report,runs:[...runs].sort((a,b)=>a.build.localeCompare(b.build))};
 assert.ok(evaluateDeviceReport(wrongOrder).errors.some((e:string)=>e.includes('chronological ABBA')));
 const overloaded=structuredClone(report);overloaded.runs.find(r=>r.build==='candidate')!.peakProcessMemoryBytes=1000000001;assert.ok(evaluateDeviceReport(overloaded).errors.some((e:string)=>e.includes('1000MB hard limit')));
 const slow=structuredClone(report);slow.runs.find(r=>r.build==='candidate')!.minOneSecondFps=49;assert.ok(evaluateDeviceReport(slow).errors.some((e:string)=>e.includes('FPS below floor 50')));
 const noCpu=structuredClone(report);delete noCpu.runs[0].cpuNormalizedPercent;assert.ok(evaluateDeviceReport(noCpu).errors.some((e:string)=>e.includes('normalized CPU usage')));
});
test('memory budget uses observed process peak, 1000MB hard ceiling and 800MB soft target',()=>{
 const row=(bytes:number)=>({...memoryObservations[0],processMemoryBytes:bytes});
 assert.deepEqual(memoryBudget([row(800000000)]).warnings,[]);
 assert.equal(memoryBudget([row(800000001),row(700000000)]).warnings.length,1);
 assert.deepEqual(memoryBudget([row(1000000000)]).errors,[]);
 assert.ok(memoryBudget([row(1000000001),row(700000000)]).errors.some((e:string)=>e.includes('1000MB hard limit')));
 for(const bytes of [NaN,0,-1])assert.ok(memoryBudget([row(bytes)]).errors.length);
 assert.ok(memoryBudget([]).errors.length);
});
test('resource measurements must cover the run and window instead of relying on post-GC samples',()=>{
 assert.deepEqual(validateMemoryCoverage(memoryObservations,0,10001),[]);
 assert.ok(validateMemoryCoverage([memoryObservations[0],memoryObservations[10]],0,10001).some((e:string)=>e.includes('sampling gap')));
 assert.ok(validateMemoryCoverage([...memoryObservations].reverse(),0,10001).some((e:string)=>e.includes('chronological')));
 assert.equal(windowMemory(memoryObservations,1000,3000).samples,3);
 assert.ok(!Number.isFinite(windowMemory([],0,3000).maxGapMs));
});
test('50FPS floor includes worst sliding one-second interval even when overall FPS passes',()=>{
 assert.equal(minimumWindowFps([500,600]),1,'count the lower window between two arrivals');
 assert.equal(minimumWindowFps([1200]),0,'a gap longer than one second contains an empty window');
 assert.equal(minimumWindowFps(Array(60).fill(1000/60),{firstDrawMs:0,durationMs:2200}),0,'the final silent tail remains part of the measurement');
 assert.equal(minimumWindowFps(Array(60).fill(1000/60),{firstDrawMs:1100,durationMs:2100}),0,'the leading gap before the first draw remains part of the measurement');
 for(const fps of [49,50,60])assert.equal(minimumWindowFps(Array(fps*3).fill(1000/fps)),fps);
 const frames=[...Array(60).fill(1000/60),200,...Array(60).fill(1000/60)],seconds=frames.reduce((n,dt)=>n+dt,0)/1000;
 const row=summarize({frames,frameClock:frameClock(frames,seconds*1000),renderCounters:renderCounters(frames.length),wallSeconds:seconds,logicalCores:4,processCpuSeconds:1,mainThreadCpuSeconds:.1,frameRate:60,mode:'idle',simulationSeconds:seconds,status:'playing',events:{},drawCalls:100,triangles:1000,processMemory});
 assert.ok(row.fps>50);assert.ok(row.minOneSecondFps<50);assert.ok(validateSample(row,seconds).includes('1-second FPS below floor 50'));
 const steady=summarize({...row,frames:Array(150).fill(20),frameClock:frameClock(Array(150).fill(20),3000),renderCounters:renderCounters(150),wallSeconds:3,simulationSeconds:3});assert.deepEqual(validateSample(steady,3),[]);
 assert.ok(validateSample({...steady,frameClock:{...steady.frameClock,durationMs:2900}},3).includes('invalid rendered-window clock coverage'));
 assert.ok(validateSample({...steady,processMemory:{...processMemory,peakBytes:1000000001}},3).some((e:string)=>e.includes('1000MB')));
 assert.ok(validateSample({...steady,cpu:{...steady.cpu,corePercent:steady.cpu.corePercent*4}},3).includes('invalid CPU usage/core conversion'));
});
test('temporal GPU counters ignore end-phase snapshots but reject sustained burst growth and incomplete series',()=>{
 const frames=Array(120).fill(1000/60),common={id:'battle',round:0,frames,frameClock:frameClock(frames,2000),wallSeconds:2,logicalCores:4,processCpuSeconds:1,mainThreadCpuSeconds:.1,frameRate:60,mode:'idle',simulationSeconds:2,status:'playing',events:{},processMemory,drawCalls:300,triangles:1000};
 const measure=(values:number[])=>summarize({...common,renderCounters:{drawCalls:values,triangles:Array(120).fill(1000)}});
 const a=measure([...Array(119).fill(100),300]),b=measure([300,...Array(119).fill(100)]);
 assert.equal(a.endFrameDrawCalls,300);assert.equal(a.drawCalls,100);assert.equal(a.drawCallsP95,100);assert.deepEqual(validateSample(a,2),[]);
 const report=(sample:any)=>({protocol:'moving-combat-v6',fingerprint:'synthetic-only',profile:'regression',seconds:2,repeats:1,samples:[sample]});
 assert.deepEqual(compare(report(a),report(b)),[]);
 const burst=measure([...Array(90).fill(100),...Array(30).fill(140)]);assert.equal(burst.drawCalls,100);assert.equal(burst.drawCallsP95,140);
 assert.ok(compare(report(burst),report(a)).some((e:string)=>e.includes('drawCallsP95 regression')));
 assert.throws(()=>measure(Array(119).fill(100)),/incomplete per-frame/);
 assert.throws(()=>measure([...Array(119).fill(100),NaN]),/Invalid/);
 assert.throws(()=>measure([...Array(119).fill(100),100+1/3]),/Invalid/,'draw calls remain integer counts');
 const nativeTriangles=198780+1/3;
 const fractional=summarize({...common,renderCounters:{drawCalls:Array(120).fill(100),triangles:Array(120).fill(nativeTriangles)}});
 assert.equal(fractional.triangles,nativeTriangles,'preserve the native Cocos indexCount/3 estimate without rounding');
 assert.deepEqual(validateSample(fractional,2),[]);
 for(const value of [NaN,Infinity,-1,Number.MAX_SAFE_INTEGER*2])assert.throws(()=>summarize({...common,renderCounters:{drawCalls:Array(120).fill(100),triangles:Array(120).fill(value)}}),/Invalid/);
 assert.throws(()=>summarize(common),/incomplete per-frame/);
 assert.ok(validateSample({...a,renderStats:{...a.renderStats,samples:119}},2).includes('invalid per-frame rendering coverage'));
});
test('memory monitor shuts down without a dangling timer and retains read failures',async()=>{
 let reads=0;const monitor=monitorMemory(async()=>({processMemoryBytes:700000000+reads++,source:'synthetic-only'}));await monitor.start();const stopped=await monitor.stop();assert.equal(stopped.samples.length,2);assert.equal(await monitor.stop(),stopped);assert.deepEqual(stopped.errors,[]);
 const broken=monitorMemory(async()=>{throw Error('counter unavailable');});await assert.rejects(broken.start(),/counter unavailable/);
});
test('batched Android PSS preserves every Chrome process and rejects missing or duplicated counters',()=>{
 const row=parsePssSnapshot('PID 42\nPss: 1200 kB\nPID 43\nPss: 800 kB\n');assert.equal(row.chromeProcessPssBytes,2000*1024);assert.equal(row.perProcess.length,2);
 assert.throws(()=>parsePssSnapshot('PID 42\nPss: 1200 kB\nPID 43\ncat: unavailable\n'),/Cannot read/);
 assert.throws(()=>parsePssSnapshot('PID 42\nPss: 1 kB\nPID 42\nPss: 1 kB\n'),/Incomplete/);assert.throws(()=>parsePssSnapshot(''),/Incomplete/);
});
