const fs=require('node:fs'),path=require('node:path'),{createHash}=require('node:crypto');

// Observe Creator CLI logs without polling processes inside a timed window.
// This does not stop or change another task, its priority or the power plan.
function monitorBuilds(directory){
 const writes=new Map(),errors=[],observed=new Map();let stopped=false;
 const matches=name=>/^(?:build-|.*-build-).+-(?:out|err)\.log(?:\..*)?$/.test(name);
 const snapshot=name=>{
  try{const file=path.join(directory,name),stat=fs.statSync(file),prior=observed.get(name);
   if(prior&&prior.size===stat.size&&prior.mtimeMs===stat.mtimeMs)return prior;
   return {size:stat.size,mtimeMs:stat.mtimeMs,sha256:createHash('sha256').update(fs.readFileSync(file)).digest('hex')};
  }catch(error){if(error.code==='ENOENT')return null;throw error;}
 };
 for(const name of fs.readdirSync(directory).filter(matches))observed.set(name,snapshot(name));
 const inspect=name=>{
  if(!matches(name))return;
  let next;try{next=snapshot(name);}catch(error){errors.push(error.message);return;}
  const prior=observed.get(name);observed.set(name,next);
  // Windows also notifies about last-access metadata after reading a log.
  // Only changed file contents qualify as competing build activity.
  if((prior?.sha256??null)===(next?.sha256??null))return;
  const now=new Date().toISOString(),entry=writes.get(name);
  if(entry){entry.last=now;entry.events++;entry.after=next;}else writes.set(name,{name,first:now,last:now,events:1,before:prior??null,after:next});
 };
 const watcher=fs.watch(directory,(_event,file)=>inspect(String(file||'')));
 watcher.on('error',error=>errors.push(error.message));
 return {stop(){if(!stopped){watcher.close();stopped=true;for(const name of new Set([...observed.keys(),...fs.readdirSync(directory).filter(matches)]))inspect(name);}return {scope:'Creator CLI build-log content changes observed during the run; last-access metadata ignored; other host applications are not measured',writes:[...writes.values()],errors};}};
}
module.exports={monitorBuilds};
