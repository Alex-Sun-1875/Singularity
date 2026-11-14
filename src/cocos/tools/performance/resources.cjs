/* Process memory is separate from JS heap and graphics allocations: never add them. */
const {execFile,spawn}=require('node:child_process');
const {createInterface}=require('node:readline');
const {promisify}=require('node:util');
const exec=promisify(execFile),budget=require('./budget.json');
function memoryBudget(rows){
 const errors=[],warnings=[];
 if(!Array.isArray(rows)||!rows.length)return {errors:['process memory telemetry missing'],warnings,peakBytes:null};
 let peakBytes=0;
 for(const row of rows){
  if(!Number.isFinite(row.processMemoryBytes)||row.processMemoryBytes<=0||!Number.isFinite(row.startedMs)||!Number.isFinite(row.finishedMs)||row.finishedMs<row.startedMs||!row.source){errors.push('invalid process memory observation');continue;}
  peakBytes=Math.max(peakBytes,row.processMemoryBytes);
 }
 if(peakBytes>budget.maximumProcessMemoryBytes)errors.push('observed process memory exceeds 1000MB hard limit');
 if(peakBytes>budget.targetProcessMemoryBytes)warnings.push('observed process memory exceeds 800MB optimization target');
 return {errors,warnings,peakBytes,peakMB:peakBytes/1e6};
}
function validateMemoryCoverage(rows,startMs,endMs){
 const errors=memoryBudget(rows).errors.filter(e=>!e.includes('hard limit'));
 if(!Number.isFinite(startMs)||!Number.isFinite(endMs)||endMs<=startMs)return [...errors,'invalid memory monitoring interval'];
 if(!rows?.length)return errors;
 const times=rows.map(r=>r.startedMs);
 if(times.some((t,i)=>i&&t<times[i-1]))errors.push('process memory observations are not chronological');
 const gaps=[times[0]-startMs,endMs-times.at(-1),...times.slice(1).map((t,i)=>t-times[i])];
 if(Math.max(...gaps)>budget.maximumMemorySampleGapMs)errors.push('process memory sampling gap exceeds 3000ms');
 return errors;
}
function windowMemory(rows,startMs,endMs){
 const selected=rows.filter(r=>r.finishedMs>=startMs&&r.startedMs<=endMs),times=selected.map(r=>r.startedMs),peak=memoryBudget(selected);
 const maxGapMs=selected.length?Math.max(0,times[0]-startMs,endMs-times.at(-1),...times.slice(1).map((t,i)=>t-times[i])):Infinity;
 return {source:selected[0]?.source,samples:selected.length,peakBytes:peak.peakBytes,peakMB:peak.peakMB,maxGapMs};
}
function monitorMemory(read,onSample){
 let running=false,timer,inflight=Promise.resolve(),wake,startedMs,finishedMs,stopPromise;const samples=[],errors=[];
 const capture=async()=>{
  const start=performance.now();
  try{const data=await read(),row={...data,startedMs:start,finishedMs:performance.now()};samples.push(row);onSample?.(row);}
  catch(e){errors.push(`process memory read failed: ${e.message}`);}
 };
 const loop=async()=>{
  let next=startedMs+budget.memorySampleIntervalMs;
  while(running){await new Promise(resolve=>{wake=resolve;timer=setTimeout(resolve,Math.max(0,next-performance.now()));});wake=undefined;if(!running)break;await capture();next=Math.max(next+budget.memorySampleIntervalMs,performance.now());}
 };
 return {samples,errors,get startedMs(){return startedMs;},get finishedMs(){return finishedMs;},
  async start(){if(running)throw Error('Memory monitor already started');running=true;startedMs=performance.now();await capture();if(errors.length){running=false;throw Error(errors[0]);}inflight=loop();},
  stop(){return stopPromise??=(async()=>{running=false;clearTimeout(timer);wake?.();await inflight;await capture();finishedMs=performance.now();return {samples,errors,startedMs,finishedMs};})();}
 };
}
async function windowsChromeMemory(browserCdp){
 const pids=(await browserCdp.send('SystemInfo.getProcessInfo')).processInfo.map(p=>Number(p.id));
 if(!pids.length||pids.some(p=>!Number.isInteger(p)||p<=0))throw Error('Cannot identify Chrome process family');
 const command=`$ErrorActionPreference='Stop'; @(Get-Process -Id ${pids.join(',')} | ForEach-Object { @{pid=$_.Id;bytes=$_.WorkingSet64} }) | ConvertTo-Json -Compress`;
 const {stdout}=await exec('pwsh',['-NoProfile','-Command',command],{windowsHide:true,timeout:10000});
 const parsed=JSON.parse(stdout.replace(/^\uFEFF/,'')),rows=Array.isArray(parsed)?parsed:[parsed];
 if(rows.length!==pids.length||rows.some(r=>!pids.includes(r.pid)||!Number.isFinite(r.bytes)||r.bytes<=0))throw Error('Incomplete Chrome working-set counters');
 return {processMemoryBytes:rows.reduce((n,r)=>n+r.bytes,0),source:'Windows Chrome process-family RSS sum (shared pages may repeat)',perProcess:rows};
}
// Keep one counter reader alive: launching PowerShell every second perturbs
// desktop frame timing. A process that exits between CDP and the counter read
// causes a fresh complete snapshot, never a silently truncated RSS sum.
function createWindowsChromeMemoryReader(browserCdp){
 if(process.platform!=='win32')throw Error('Desktop process memory backend requires Windows');
 const command="$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); while($null -ne ($counterLine=[Console]::ReadLine())){try{$requestedPids=@(ConvertFrom-Json -InputObject $counterLine); $counterRows=@(Get-Process -Id $requestedPids | ForEach-Object { @{pid=$_.Id;bytes=$_.WorkingSet64} }); [Console]::WriteLine((ConvertTo-Json -Compress -Depth 4 -InputObject @{rows=$counterRows}))}catch{[Console]::WriteLine((ConvertTo-Json -Compress -InputObject @{error=$_.Exception.Message}))}}";
 const child=spawn('pwsh',['-NoProfile','-Command',command],{windowsHide:true,stdio:['pipe','pipe','pipe']}),pending=[];
 let stderr='',closed=false;child.stderr.on('data',data=>stderr=(stderr+data).slice(-2000));
 const fail=error=>{for(const row of pending.splice(0)){clearTimeout(row.timer);row.reject(error);}};
 child.on('error',fail);child.stdin.on('error',fail);child.on('exit',code=>{closed=true;fail(new Error('Memory reader exited '+code+': '+stderr));});
 createInterface({input:child.stdout}).on('line',line=>{const row=pending.shift();if(!row)return;clearTimeout(row.timer);try{row.resolve(JSON.parse(line.replace(/^\uFEFF/,'')));}catch(error){row.reject(error);}});
 const request=pids=>new Promise((resolve,reject)=>{if(closed)return reject(new Error('Memory reader is closed'));const timer=setTimeout(()=>{fail(new Error('Memory counter read timed out'));child.kill();},10000);pending.push({resolve,reject,timer});child.stdin.write(JSON.stringify(pids)+'\n');});
 return {async read(){
  let error;
  for(let attempt=0;attempt<3;attempt++){
   if(attempt)await new Promise(resolve=>setTimeout(resolve,100));
   const pids=(await browserCdp.send('SystemInfo.getProcessInfo')).processInfo.map(p=>Number(p.id));
   if(!pids.length||pids.some(pid=>!Number.isInteger(pid)||pid<=0))throw Error('Cannot identify Chrome process family');
   const result=await request(pids),rows=result.rows;
   if(!result.error&&Array.isArray(rows)&&rows.length===pids.length&&rows.every(r=>pids.includes(r.pid)&&Number.isFinite(r.bytes)&&r.bytes>0))return {processMemoryBytes:rows.reduce((n,r)=>n+r.bytes,0),source:'Windows Chrome process-family RSS sum (shared pages may repeat)',perProcess:rows,snapshotRetries:attempt};
   error=result.error||'Incomplete Chrome working-set counters';
  }
  throw Error(error);
 },async close(){if(closed)return;await new Promise(resolve=>{const timer=setTimeout(()=>child.kill(),2000);child.once('exit',()=>{clearTimeout(timer);resolve();});child.stdin.end();});}};
}
module.exports={memoryBudget,validateMemoryCoverage,windowMemory,monitorMemory,windowsChromeMemory,createWindowsChromeMemoryReader};
