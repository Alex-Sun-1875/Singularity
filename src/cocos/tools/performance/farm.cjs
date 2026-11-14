const fs=require('node:fs'),path=require('node:path'),{performance}=require('node:perf_hooks');
const {openAndroid}=require('./android.cjs');
const {chromium,devices}=require('playwright'),os=require('node:os');
const {monitorMemory,memoryBudget,validateMemoryCoverage,windowMemory,createWindowsChromeMemoryReader}=require('./resources.cjs');
const {summarize,validateSample,validateReference,aggregate,compare,fingerprint,measurementHash,processCpuDelta,cpuUsage,median}=require('./metrics.cjs');
const {monitorBuilds}=require('./host-build.cjs');
const {validateFarmSample}=require('./farm-metrics.cjs');
const budget=require('./budget.json');
const args=process.argv.slice(2),arg=(key,fallback)=>{const i=args.indexOf('--'+key);return i<0?fallback:args[i+1];};
if(args.includes('--help')){console.log('node tools/performance/farm.cjs --url URL --profile routine|smoke|regression|soak --control move|auto --family WAR|BOW|FIR|THU --area H12 --out DIRECTORY [--before REPORT] [--backend desktop|android]. Desktop uses fixed mobile rendering at1608x768/DPR1. Default:5min continuously moving combat. soak20min is explicit large-change validation.');process.exit(0);}
const backend=arg('backend','android');if(!['desktop','android'].includes(backend))throw Error('Invalid backend');
const profile=arg('profile','routine'),plans={smoke:{seconds:60,repeats:1},routine:{seconds:300,repeats:1},regression:{seconds:300,repeats:1},soak:{seconds:1200,repeats:1}},plan=plans[profile];
const spec={area:arg('area','H12'),family:arg('family','BOW'),level:17,control:arg('control','move')};
if(!plan||!['move','auto'].includes(spec.control)||!['WAR','BOW','FIR','THU'].includes(spec.family)||!['H12','H13'].includes(spec.area))throw Error('Invalid native hunting scenario');
const out=path.resolve(arg('out',path.join(__dirname,'../../test-results/performance',Date.now()+'-farm')));
if(fs.existsSync(path.join(out,'report.json')))throw Error('Refusing to overwrite a native hunting run');fs.mkdirSync(out,{recursive:true});
const url=new URL(arg('url','http://127.0.0.1:7514/'));url.searchParams.set('view','2d');url.searchParams.set('player','3d');url.searchParams.set('progression','natural');
const farmHash=fingerprint(Object.fromEntries(['farm.cjs','farm-driver.cjs','farm-metrics.cjs','host-build.cjs'].map(p=>[p,fs.readFileSync(path.join(__dirname,p),'utf8')])));
const report={protocol:'moving-combat-v6',scenario:spec.control==='move'?'moving-hunt-v1':'native-auto-hunt-v1',profile:'farm-'+profile,seconds:plan.seconds,repeats:plan.repeats,url:url.href,fixture:spec,farmHarnessHash:farmHash,measurementHash:measurementHash(),budget,budgetHash:fingerprint(budget),started:new Date().toISOString(),status:'running',samples:[],heartbeats:[],errors:[],warnings:[],memory:[]};
const persist=()=>fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let session,browser,browserCdp,desktopMemory,monitor,builds;
const logicalCores=()=>session?.logicalCores??os.cpus().length;
const processes=async()=>session?session.processes():new Map((await browserCdp.send('SystemInfo.getProcessInfo')).processInfo.map(p=>[p.id,p.cpuTime]));
const readMemory=async()=>session?{...await session.memory(),source:'Android Chrome process-family PSS (/proc/smaps_rollup)'}:desktopMemory.read();
async function main(){
 builds=monitorBuilds(path.resolve(__dirname,'../../temp'));
 let context;
 if(backend==='android'){session=await openAndroid(arg('serial','emulator-5556'),url);context=session.context;}
 else{browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:!args.includes('--headed')});browserCdp=await browser.newBrowserCDPSession();desktopMemory=createWindowsChromeMemoryReader(browserCdp);context=await browser.newContext({viewport:{width:1608,height:768},screen:{width:1608,height:768},deviceScaleFactor:1,isMobile:true,hasTouch:true,userAgent:devices['Pixel 7'].userAgent});}
 const page=await context.newPage();
 for(const other of context.pages().filter(p=>p!==page))await other.close();
 page.on('pageerror',e=>report.errors.push(e.stack||e.message));page.on('console',m=>{if(m.type()==='error')report.errors.push('console: '+m.text());});
 report.phase='loading';monitor=monitorMemory(async()=>{const m=await readMemory();return {...m,processMemoryBytes:session?m.chromeProcessPssBytes:m.processMemoryBytes,phase:report.phase};});report.memoryObservations=monitor.samples;await monitor.start();
 await page.goto(url.href,{waitUntil:'domcontentloaded',timeout:60000});const cdp=await context.newCDPSession(page);
 if(session){const fullscreen=await cdp.send('Runtime.evaluate',{expression:'document.documentElement.requestFullscreen()',userGesture:true,awaitPromise:true});if(fullscreen.exceptionDetails)throw Error('Native fullscreen failed');}
 await page.waitForFunction(()=>!!globalThis.System,null,{timeout:60000});
 await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.__performanceApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>!!__performanceApp()?.actors&&!__performanceApp().loading&&!__performanceApp().failure,null,{timeout:120000});
 if(session){await session.nativeUi(true);report.nativeUiChecked=true;}
 const {workloadRules,...rendering}=await page.evaluate(require('./page-driver.cjs'));
 report.workloadRulesHash=fingerprint({workloadRules,scenario:report.scenario,spec});report.expectedPipeline='legacy';report.emulation=session?'android-native':'desktop-mobile';
 report.renderSettings=await page.evaluate(()=>({engineMobile:__perf.cc.sys.isMobile,csmLevel:__perf.app.keyLight.csmLevel,usesCustomPipeline:__perf.cc.director.root.usesCustomPipeline}));
 if(!report.renderSettings.engineMobile||report.renderSettings.csmLevel!==1||report.renderSettings.usesCustomPipeline||rendering.frameRate!==60)throw Error('Native mobile quality/pipeline/60FPS policy changed');
 report.environment={userAgent:await page.evaluate(()=>navigator.userAgent),...(session?session.environment:{backend:'desktop-chrome',os:os.platform(),cpu:os.cpus()[0].model,logicalCores:logicalCores(),headless:!args.includes('--headed')}),browser:(await cdp.send('Browser.getVersion')).product,...rendering,nativeViewport:await page.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio})),renderer:await page.evaluate(()=>__perf.cc.director.root.device.renderer)};
 if(!session&&/swiftshader|llvmpipe|software/i.test(report.environment.renderer))throw Error('Desktop baseline requires hardware graphics');
 if(session){report.hostControl=session.hostControl;report.hostTimerPolicy=session.hostTimerPolicy;}
 report.fingerprint=fingerprint({environment:report.environment,measurement:report.measurementHash,farm:farmHash,workload:report.workloadRulesHash,budget:report.budgetHash});
 report.buildHashes={};for(const script of await page.evaluate(()=>performance.getEntriesByType('resource').map(x=>x.name).filter(x=>/\/assets\/main\/index[^/]*\.js/.test(x))))report.buildHashes[script]=fingerprint(await (await fetch(script)).text());
 await cdp.send('Performance.enable',{timeDomain:'threadTicks'});const metrics=async()=>Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m=>[m.name,m.value]));
 const retained=async label=>{await cdp.send('HeapProfiler.collectGarbage');const heap=await cdp.send('Runtime.getHeapUsage'),gfx=await page.evaluate(()=>({...__perf.cc.director.root.device.memoryStatus}));const m=await readMemory();const row={label,...heap,gfxBytes:gfx,...m};report.memory.push(row);persist();return row;};
 if(!session){report.phase='warmup';persist();await page.evaluate(require('./farm-driver.cjs'),spec);await sleep(60000);}
 const id=spec.area+'-'+spec.control+'-hunt-'+spec.family;
 for(let round=0;round<plan.repeats;round++){
  report.phase='setup';const fixture=await page.evaluate(require('./farm-driver.cjs'),spec);report.actualFixture=fixture;await sleep(5000);const warm=await retained('warm-'+round);
  const before=await metrics(),p0=await processes(),started=performance.now();let previousCpu=p0,previousMetrics=before,previousWall=0,previousFrames=0;
  report.phase=(round+1)+'-'+id;report.measurementStarted=new Date().toISOString();await page.evaluate(()=>__perf.begin());
  for(let elapsed=0;elapsed<plan.seconds;elapsed+=60){
   await sleep(Math.min(60,plan.seconds-elapsed)*1000);
   const state=await page.evaluate(()=>({wallSeconds:(performance.now()-__perf.measurementStartMs)/1000,draws:__perf.frames.length+1,simulationTime:__perf.app.session.state.time,status:__perf.app.session.state.status,hp:__perf.app.session.state.player.hp,automation:__perf.app.automation.mode,active:__perf.app.automation.active,area:__perf.app.session.state.area,kills:__perf.events.defeat||0,hits:(__perf.events.hit||0)+(__perf.events.skill_hit||0),respawns:__perf.events.enemy_respawn||0,groundLoot:__perf.app.session.state.groundLoot.length,movedMetres:__perf.app.session.state.movedDistance-__perf.startDistance,actualMovingFrames:__perf.farmMotion.movingFrames,route:__perf.farmRoute}));
   const cpu=await processes(),m=await metrics(),row={round:round+1,at:new Date().toISOString(),...state,cpu:cpuUsage(processCpuDelta(previousCpu,cpu),state.wallSeconds-previousWall,logicalCores()),mainThreadMsPerFrame:(m.TaskDuration-previousMetrics.TaskDuration)*1000/Math.max(1,state.draws-previousFrames)};
   report.heartbeats.push(row);previousCpu=cpu;previousMetrics=m;previousWall=state.wallSeconds;previousFrames=state.draws;persist();console.log(JSON.stringify({minute:Math.round(state.wallSeconds/60),round:round+1,corePercent:row.cpu.corePercent,mainThreadMs:row.mainThreadMsPerFrame,hp:state.hp,kills:state.kills,respawns:state.respawns,groundLoot:state.groundLoot,movedMetres:state.movedMetres}));
  }
  const data=await page.evaluate(()=>({...__perf.end(),nativeHunt:{...__perf.farmMotion}})),ended=performance.now(),p1=await processes(),after=await metrics();
  fs.writeFileSync(path.join(out,(round+1)+'-frames.json'),JSON.stringify(data.frames));fs.writeFileSync(path.join(out,(round+1)+'-frame-clock.json'),JSON.stringify(data.frameClock));fs.writeFileSync(path.join(out,(round+1)+'-render-counters.json'),JSON.stringify(data.renderCounters));
  const sample=summarize({...spec,...data,id,round,expectedArea:spec.area,mode:spec.control==='move'?'move-combat':'auto-hunt',frameRate:fixture.frameRate,wallSeconds:data.frameClock.durationMs/1000,logicalCores:logicalCores(),processCpuSeconds:processCpuDelta(p0,p1),mainThreadCpuSeconds:after.TaskDuration-before.TaskDuration,processMemory:windowMemory(monitor.samples,started,ended),...(session?{androidCpu:{before:p0.counters,after:p1.counters,processesBefore:[...p0],processesAfter:[...p1]}}:{})});
  sample.validation=validateFarmSample(sample,plan.seconds);
  const heartbeats=report.heartbeats.filter(x=>x.round===round+1);if(heartbeats.some(x=>(spec.control==='auto'?(x.automation!=='idle'||!x.active):(x.automation!=='manual'||x.active))||x.status!=='playing'||x.area!==spec.area))sample.validation.push('hunting controller changed, died or left the area');
  if(spec.control==='move'){let metres=0,kills=0,hits=0,moving=0,draws=0;for(const h of heartbeats){if(h.movedMetres-metres<30||h.actualMovingFrames-moving<(h.draws-draws)*.5)sample.validation.push('continuous movement missing in a minute');if(h.kills<=kills||h.hits<=hits)sample.validation.push('continued combat missing in a minute');metres=h.movedMetres;kills=h.kills;hits=h.hits;moving=h.actualMovingFrames;draws=h.draws;}}
  if(profile==='soak'){
   if(heartbeats.at(-1).kills<=heartbeats.at(-6).kills||heartbeats.at(-1).respawns<=heartbeats.at(-6).respawns)sample.validation.push('no sustained hunting in final5minutes');
   if(median(heartbeats.slice(-3).map(x=>x.mainThreadMsPerFrame))>median(heartbeats.slice(0,3).map(x=>x.mainThreadMsPerFrame))*1.2+.3)sample.validation.push('late CPU degradation >20% +0.3ms');
  }
  report.samples.push(sample);report.errors.push(...sample.validation.map(x=>(round+1)+'-'+id+': '+x));persist();
  await page.screenshot({path:path.join(out,(round+1)+'-farm.png')});const end=await retained('end-'+round);
  if(profile==='soak'){if(end.usedSize-warm.usedSize>12*1048576)report.errors.push('retained heap grew >12MiB');if(end.gfxBytes.bufferSize+end.gfxBytes.textureSize-warm.gfxBytes.bufferSize-warm.gfxBytes.textureSize>8*1048576)report.errors.push('graphics allocation grew >8MiB');if(session&&end.chromeProcessPssBytes-warm.chromeProcessPssBytes>64*1048576)report.errors.push('Chrome-family PSS grew >64MiB');}
 }
 report.summary=aggregate(report.samples);
 if(arg('before')){const prior=JSON.parse(fs.readFileSync(arg('before'),'utf8'));if(prior.farmHarnessHash!==farmHash)report.errors.push('Native hunting harness mismatch');const errors=validateReference(prior,[id],plan.seconds,plan.repeats,true);for(const sample of prior.samples||[])errors.push(...validateFarmSample(sample,plan.seconds,false));report.errors.push(...errors);if(!errors.length)report.errors.push(...compare(report,prior));report.reference={kind:'optimization-before',file:path.resolve(arg('before'))};}
 if(session){await session.nativeUi();report.nativeUiEndChecked=true;}
}
main().catch(error=>{report.errors.push(error.stack||String(error));console.error(error);}).finally(async()=>{
 if(monitor)try{const m=await monitor.stop();report.memoryMonitoring={startedMs:m.startedMs,finishedMs:m.finishedMs,intervalMs:budget.memorySampleIntervalMs,errors:m.errors};report.resources=memoryBudget(m.samples);report.errors.push(...m.errors,...validateMemoryCoverage(m.samples,m.startedMs,m.finishedMs),...report.resources.errors);report.warnings.push(...report.resources.warnings);}catch(e){report.errors.push('Memory monitor: '+e.message);}
 if(session)try{const g=await session.graphicsLog();report.nativeGraphicsChecked=true;report.nativeGraphicsErrors=g.errors;fs.writeFileSync(path.join(out,'android-chromium.log'),g.log);report.errors.push(...g.errors);}catch(e){report.errors.push('Native graphics: '+e.message);}
 if(builds){report.hostWorkload=builds.stop();report.errors.push(...report.hostWorkload.errors);if(report.hostWorkload.writes.length)report.errors.push('Host workload: concurrent Creator build logs changed; run is ineligible');}
 report.status=report.errors.length?'failed':'passed';report.finished=new Date().toISOString();report.scope=(session?'Android emulator Chrome, ':'Desktop hardware Chrome fixed1608x768/DPR1 mobile branch, ')+(spec.control==='move'?'continuousmoving normalinput combat; gameAutomation disabled, inputpilot follows native navigation with atmost1pathquery/sec':'native idle-hunting without injected inputpilot')+', real damage, finite consumables, loot and naturalrespawn; no browser CPUprofiler, HP restoration or replenished stock. Not physical TapTap energy/temperature acceptance.';persist();await desktopMemory?.close();await session?.close();await browser?.close();console.log(report.status+': '+path.join(out,'report.json'));if(report.status!=='passed')process.exitCode=1;
});
