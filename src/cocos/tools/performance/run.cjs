const {chromium,devices}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {performance}=require('node:perf_hooks');
const {execFileSync}=require('node:child_process');
const {summarize,validateSample,validateReference,aggregate,compare,fingerprint,median,processCpuDelta,measurementHash}=require('./metrics.cjs');
const {memoryBudget,validateMemoryCoverage,windowMemory,monitorMemory,windowsChromeMemory}=require('./resources.cjs');
const budget=require('./budget.json');
const config=require('./cases.json');
const args=process.argv.slice(2),arg=(key,fallback)=>{const i=args.indexOf(`--${key}`);return i<0?fallback:args[i+1];};
if(args.includes('--help')){console.log('node tools/performance/run.cjs --url http://127.0.0.1:7495/ --profile smoke|regression|soak --out test-results/performance/run-id [--backend desktop|android] [--serial emulator-5556] [--baseline approved/report.json | --before original/report.json] [--profile-cpu] [--trace] [--diagnostic --diagnostic-reason label] [--device iphone14|desktop] [--expected-pipeline legacy|crp]');process.exit(0);}
const emulation=arg('device','desktop');if(!['desktop','iphone14'].includes(emulation))throw Error(`Unknown emulation ${emulation}`);
const backend=arg('backend','desktop');if(!['desktop','android'].includes(backend))throw Error(`Unknown backend ${backend}`);
const expectedPipeline=arg('expected-pipeline','legacy');if(!['legacy','crp'].includes(expectedPipeline))throw Error(`Unknown pipeline ${expectedPipeline}`);
if(arg('before')&&arg('baseline'))throw Error('Choose --before for optimization evidence or --baseline for approved regression gating');
const profile=arg('profile','regression'),plan=config.profiles[profile];
if(!plan)throw Error(`Unknown profile ${profile}`);
const output=path.resolve(arg('out',path.join(__dirname,'../../test-results/performance',new Date().toISOString().replace(/[:.]/g,'-'))));
if(fs.existsSync(path.join(output,'report.json')))throw Error(`Refusing to overwrite an existing performance run: ${output}`);
fs.mkdirSync(output,{recursive:true});
const url=new URL(arg('url',process.env.CHAPTER_URL||'http://127.0.0.1:7495/'));url.searchParams.set('view','2d');url.searchParams.set('player','3d');url.searchParams.set('progression','natural');
const report={protocol:config.protocol,budget,budgetHash:fingerprint(budget),profile,profileCpu:args.includes('--profile-cpu'),seconds:plan.seconds,repeats:plan.repeats,started:new Date().toISOString(),url:url.href,status:'running',samples:[],errors:[],warnings:[],memory:[],memoryObservations:[]};
report.emulation=emulation;
report.measurementHash=measurementHash();
report.expectedPipeline=expectedPipeline;
report.trace=args.includes('--trace');
report.diagnostic=args.includes('--diagnostic');report.diagnosticReason=arg('diagnostic-reason','');
const persist=()=>fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));
const timeout=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let browser,androidSession,resourceMonitor;
async function main(){
  report.git=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
  report.driverHash=fingerprint(fs.readFileSync(path.join(__dirname,'page-driver.cjs'),'utf8'));
  let context;
  if(backend==='android'){androidSession=await require('./android.cjs').openAndroid(arg('serial','emulator-5556'),url);context=androidSession.context;report.emulation='android-native';report.hostControl=androidSession.hostControl;report.hostTimerPolicy=androidSession.hostTimerPolicy;}
  else {browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:!args.includes('--headed')});context=await browser.newContext({viewport:{width:844,height:390},deviceScaleFactor:3,isMobile:true,hasTouch:true,...(emulation==='iphone14'?{userAgent:devices['iPhone 14'].userAgent,screen:{width:844,height:390}}:{})});}
  const page=await context.newPage();page.on('pageerror',e=>report.errors.push(`pageerror: ${e.stack||e}`));
  if(androidSession){const extra=context.pages().filter(p=>p!==page);for(const stale of extra)await stale.close();report.closedStartupTabs=extra.length;}
  page.on('console',m=>{if(m.type()==='error')report.errors.push(`console: ${m.text()}`);});
  const browserCdp=browser?await browser.newBrowserCDPSession():null;
  const readMemory=androidSession?async()=>{const data=await androidSession.memory();return {...data,processMemoryBytes:data.chromeProcessPssBytes,source:'Android Chrome process-family PSS (/proc/smaps_rollup)'};}:async()=>{if(process.platform!=='win32')throw Error('Desktop process memory backend requires Windows; use Android backend on this host');return windowsChromeMemory(browserCdp);};
  report.phase='loading';resourceMonitor=monitorMemory(async()=>({...await readMemory(),phase:report.phase}));report.memoryObservations=resourceMonitor.samples;await resourceMonitor.start();
  await page.goto(url.href,{waitUntil:'domcontentloaded',timeout:60000});
  if(androidSession){const fullscreen=await context.newCDPSession(page);const result=await fullscreen.send('Runtime.evaluate',{expression:'document.documentElement.requestFullscreen()',userGesture:true,awaitPromise:true});if(result.exceptionDetails)throw Error('Android browser fullscreen failed');await fullscreen.detach();}
  await page.waitForFunction(()=>!!globalThis.System,null,{timeout:60000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.__performanceApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>!!__performanceApp()?.actors&&!__performanceApp().loading&&!__performanceApp().failure,null,{timeout:120000});
  if(androidSession){const ui=await androidSession.nativeUi(true);fs.writeFileSync(path.join(output,'android-start-ui.xml'),ui.xml);fs.writeFileSync(path.join(output,'android-start-device.png'),await androidSession.device.screenshot());report.nativeUiChecked=true;report.dismissedImmersiveHelp=ui.dismissed;await timeout(500);}
  const {workloadRules,...rendering}=await page.evaluate(require('./page-driver.cjs'));report.workloadRulesHash=fingerprint(workloadRules);
  report.renderSettings=await page.evaluate(()=>{const {cc,app}=__perf;return {userAgent:navigator.userAgent,engineMobile:cc.sys.isMobile,engineOS:cc.sys.os,csmLevel:app.keyLight.csmLevel,shadowMapSize:cc.director.getScene().globals.shadows.shadowMapSize,usesCustomPipeline:cc.director.root.usesCustomPipeline};});
  if(report.renderSettings.usesCustomPipeline!==(expectedPipeline==='crp'))throw Error(`Runtime rendering pipeline does not match ${expectedPipeline}`);
  if((emulation==='iphone14'||backend==='android')&&(!report.renderSettings.engineMobile||report.renderSettings.csmLevel!==1))throw Error('Mobile test did not enter the actual mobile render branch');
  const pageCdp=await context.newCDPSession(page);
  await pageCdp.send('Performance.enable',{timeDomain:'threadTicks'});
  const logicalCores=androidSession?.logicalCores??os.cpus().length;
  report.environment=androidSession?{...androidSession.environment,nativeUi:'unobstructed-fullscreen',nativeViewport:await page.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,screen:[screen.width,screen.height]})),host:{os:os.platform(),cpu:os.cpus()[0].model,logicalCores:os.cpus().length},browser:(await pageCdp.send('Browser.getVersion')).product,...rendering}:{os:os.platform(),cpu:os.cpus()[0].model,logicalCores,browser:browser.version(),headless:!args.includes('--headed'),viewport:[844,390],requestedDpr:3,...rendering};
  report.buildScripts=await page.evaluate(()=>performance.getEntriesByType('resource').map(r=>r.name).filter(url=>/\/assets\/main\/index[^/]*\.js/.test(url)));
  report.buildHashes={};for(const script of report.buildScripts){const response=await fetch(script);if(!response.ok)throw Error(`Cannot fingerprint build script ${script}`);report.buildHashes[script]=fingerprint(await response.text());}
  report.assetManifestHashes={};for(const file of await page.evaluate(()=>performance.getEntriesByType('resource').map(r=>r.name).filter(url=>/\/assets\/[^/]+\/config\.[^/]+\.json/.test(url)))){const response=await fetch(file);if(!response.ok)throw Error(`Cannot fingerprint asset manifest ${file}`);report.assetManifestHashes[file]=fingerprint(await response.text());}
  report.fingerprint=fingerprint({...report.environment,driver:report.driverHash,budget:report.budgetHash,measurement:report.measurementHash,workload:report.workloadRulesHash});
  const metrics=async()=>Object.fromEntries((await pageCdp.send('Performance.getMetrics')).metrics.map(m=>[m.name,m.value]));
  const processes=androidSession?androidSession.processes:async()=>new Map((await browserCdp.send('SystemInfo.getProcessInfo')).processInfo.map(p=>[p.id,p.cpuTime]));
  const collectMemory=async(label)=>{await pageCdp.send('HeapProfiler.collectGarbage');const heap=await pageCdp.send('Runtime.getHeapUsage');const data=await page.evaluate(()=>{const d=__perf.cc.director.root.device;return {gfxBytes:{...d.memoryStatus},models:__perf.cc.director.getScene().renderScene.models.length};});report.memory.push({label,...heap,...data,...(androidSession?await androidSession.memory():{})});persist();};
  const cases=plan.cases?config.cases.filter(c=>plan.cases.includes(c.id)):config.cases;
  // Warm every participating asset/action before retained-memory and timing gates.
  report.phase='warmup';for(const spec of cases){await page.evaluate(s=>__perf.setup(s),spec);await timeout(3000);}
  await collectMemory('warm');
  for(let round=0;round<plan.repeats;round++){
    for(const spec of round%2?[...cases].reverse():cases){
      const label=`${round+1}-${spec.id}`;
      report.phase=`${label}:setup`;const fixture=await page.evaluate(s=>__perf.setup(s),spec);await timeout(1000);
      if(args.includes('--profile-cpu')){await pageCdp.send('Profiler.enable');await pageCdp.send('Profiler.start');}
      if(report.trace)await pageCdp.send('Tracing.start',{categories:'devtools.timeline,toplevel,cc,gpu,viz,v8,blink.user_timing,disabled-by-default-v8.gc',transferMode:'ReturnAsStream'});
      const before=await metrics(),p0=await processes(),start=performance.now();
      report.phase=label;
      if(report.trace)await page.evaluate(()=>{globalThis.__perfTraceClock={startMs:performance.now(),firstDrawMs:0};console.timeStamp('performance-window-start');__perf.cc.director.once(__perf.cc.Director.EVENT_AFTER_DRAW,()=>__perfTraceClock.firstDrawMs=performance.now());__perf.begin();});
      else await page.evaluate(()=>__perf.begin());
      // Host waits leave the game running. Heartbeat permits observing long jobs.
      let remaining=plan.seconds;while(remaining>0){const step=Math.min(10,remaining);await timeout(step*1000);remaining-=step;if(remaining>0)console.log(`${label}: ${plan.seconds-remaining}/${plan.seconds}s`);}
      const data=report.trace?await page.evaluate(()=>{const data=__perf.end();console.timeStamp('performance-window-end');return {...data,profileClock:{...__perfTraceClock,endMs:performance.now()}};}):await page.evaluate(()=>__perf.end()),end=performance.now(),wallSeconds=(end-start)/1000,p1=await processes(),after=await metrics();report.phase=`${label}:after`;
      if(report.trace)data.profileClock.navigationStartSeconds=before.NavigationStart;
      if(args.includes('--profile-cpu')){const {profile}=await pageCdp.send('Profiler.stop');fs.writeFileSync(path.join(output,`${label}.cpuprofile`),JSON.stringify(profile));}
      if(report.trace){
        const complete=new Promise(resolve=>pageCdp.once('Tracing.tracingComplete',resolve));await pageCdp.send('Tracing.end');const outcome=await complete,stream=outcome.stream;let trace='';
        for(;;){const chunk=await pageCdp.send('IO.read',{handle:stream});trace+=chunk.base64Encoded?Buffer.from(chunk.data,'base64').toString():chunk.data;if(chunk.eof)break;}
        await pageCdp.send('IO.close',{handle:stream});fs.writeFileSync(path.join(output,`${label}.trace.json`),trace);data.traceDataLoss=outcome.dataLossOccurred??null;data.traceMarkersComplete=trace.includes('performance-window-start')&&trace.includes('performance-window-end');
        if(data.traceDataLoss||!data.traceMarkersComplete)report.errors.push(`${label}: diagnostic trace lost events or window markers`);
      }
      fs.writeFileSync(path.join(output,`${label}-frames.json`),JSON.stringify(data.frames));
      fs.writeFileSync(path.join(output,`${label}-frame-clock.json`),JSON.stringify(data.frameClock));
      fs.writeFileSync(path.join(output,`${label}-render-counters.json`),JSON.stringify({schema:'render-counter-series-v1',...data.renderCounters}));
      const processCpuSeconds=processCpuDelta(p0,p1);
      const sample=summarize({...spec,...data,expectedArea:spec.area,round,frameRate:fixture.frameRate,wallSeconds,logicalCores,processCpuSeconds,mainThreadCpuSeconds:after.TaskDuration-before.TaskDuration,processMemory:windowMemory(resourceMonitor.samples,start,end),...(androidSession?{androidCpu:{before:p0.counters,after:p1.counters,processesBefore:Array.from(p0),processesAfter:Array.from(p1)}}:{})});
      sample.validation=validateSample(sample,plan.seconds);report.errors.push(...sample.validation.map(e=>`${label}: ${e}`));report.samples.push(sample);persist();
      console.log(JSON.stringify({case:label,fps:sample.fps,minOneSecondFps:sample.minOneSecondFps,p99Ms:sample.p99Ms,memoryPeakMB:sample.processMemory.peakMB,cpuNormalizedPercent:sample.cpu.normalizedPercent,cpuCorePercent:sample.cpu.corePercent,coreEquivalents:sample.cpu.coreEquivalents,mainThreadMs:sample.mainThreadMsPerFrame,hits:sample.events.hit||0,validation:sample.validation}));
      if(round===0){await page.screenshot({path:path.join(output,`${spec.id}.png`)});if(androidSession)fs.writeFileSync(path.join(output,`${spec.id}-device.png`),await androidSession.device.screenshot());}
    }
    await collectMemory(`round-${round+1}`);
    if(androidSession){const ui=await androidSession.nativeUi();fs.writeFileSync(path.join(output,`android-round-${round+1}-ui.xml`),ui.xml);}
  }
  if(profile==='soak'){
    const initial=report.memory[0],tail=report.memory.slice(-3),used=median(tail.map(m=>m.usedSize)),gfx=m=>m.gfxBytes.bufferSize+m.gfxBytes.textureSize;
    if(used-initial.usedSize>12*1048576)report.errors.push('retained heap grew >12MiB after warmup');
    if(median(tail.map(gfx))-gfx(initial)>8*1048576)report.errors.push('graphics allocation grew >8MiB after warmup');
    if(androidSession&&median(tail.map(m=>m.chromeProcessPssBytes))-initial.chromeProcessPssBytes>64*1048576)report.errors.push('Android Chrome process-family PSS grew >64MiB after warmup');
    for(const spec of cases){const rows=report.samples.filter(s=>s.id===spec.id);if(median(rows.slice(-3).map(s=>s.mainThreadMsPerFrame))>median(rows.slice(0,3).map(s=>s.mainThreadMsPerFrame))*1.2+.3)report.errors.push(`${spec.id}: late CPU degradation >20% +0.3ms`);}
  }
  report.summary=aggregate(report.samples);
  const baseline=arg('baseline')||arg('before');if(baseline){report.reference={file:path.resolve(baseline),kind:arg('before')?'optimization-before':'approved-baseline'};const prior=JSON.parse(fs.readFileSync(baseline,'utf8')),invalid=validateReference(prior,cases.map(c=>c.id),plan.seconds,plan.repeats,!!arg('before'));report.errors.push(...invalid);if(!invalid.length){report.errors.push(...compare(report,prior));const a=report.summary,b=aggregate(prior.samples);report.comparison=Object.fromEntries(Object.keys(a).map(id=>[id,{before:b[id],after:a[id],fpsChangePercent:(a[id].fps/b[id].fps-1)*100,mainThreadChangePercent:(a[id].mainThreadMsPerFrame/b[id].mainThreadMsPerFrame-1)*100,coreLoadChangePercent:(a[id].corePercent/b[id].corePercent-1)*100}]));}}
  report.status=report.errors.length?'failed':'passed';
  report.scope=(report.trace||report.profileCpu||report.diagnostic?'Diagnostic instrumentation or host experiment; this is not an approved baseline. ':'')+(androidSession?'Android emulator Chrome with real Cocos/Bullet; CPU is measured inside Android across Chrome processes. ':'Desktop Chrome with real Cocos/Bullet. ')+'Not physical-device TapTap energy or thermal acceptance. Forced GC occurs only outside measured windows. Repeated fresh encounters include normal health/damage and do not emulate one continuous save.';
}
main().catch(e=>{report.status='failed';report.errors.push(e.stack||String(e));console.error(e);}).finally(async()=>{
 if(resourceMonitor)try{const monitored=await resourceMonitor.stop();report.memoryMonitoring={startedMs:monitored.startedMs,finishedMs:monitored.finishedMs,intervalMs:budget.memorySampleIntervalMs,errors:monitored.errors};report.resources=memoryBudget(monitored.samples);report.errors.push(...monitored.errors,...validateMemoryCoverage(monitored.samples,monitored.startedMs,monitored.finishedMs).map(e=>`Resource telemetry: ${e}`),...report.resources.errors.map(e=>`Resource budget: ${e}`));report.warnings.push(...report.resources.warnings);}catch(e){report.errors.push(`Process memory monitor unavailable: ${e.message}`);}
 if(androidSession)try{const native=await androidSession.graphicsLog();fs.writeFileSync(path.join(output,'android-chromium.log'),native.log);report.nativeGraphicsChecked=true;report.nativeGraphicsErrors=native.errors;report.errors.push(...native.errors.map(line=>`Android native graphics: ${line}`));}catch(e){report.errors.push(`Android native graphics log unavailable: ${e.message}`);}
 if(report.errors.length)report.status='failed';report.finished=new Date().toISOString();persist();await browser?.close();await androidSession?.close();console.log(`${report.status}: ${path.join(output,'report.json')}`);if(report.status!=='passed')process.exitCode=1;
});
