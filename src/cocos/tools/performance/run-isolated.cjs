// Keep run.cjs's pinned sampling protocol; reject competing Creator builds.
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const {fingerprint}=require('./metrics.cjs');
const {monitorBuilds}=require('./host-build.cjs');
const args=process.argv.slice(2),index=args.indexOf('--out');
if(args.includes('--help')){console.log('Same options as run.cjs; additionally watches Creator CLI logs and rejects runs/references with build interference.');process.exit(0);}
if(index<0||!args[index+1])throw Error('run-isolated requires an explicit unique --out directory');
const reportFile=path.resolve(args[index+1],'report.json');
if(fs.existsSync(reportFile))throw Error('Refusing to overwrite an existing performance report');
const enclosureHash=fingerprint(['run-isolated.cjs','host-build.cjs'].map(p=>fs.readFileSync(path.join(__dirname,p),'utf8')));
for(const flag of ['--before','--baseline']){
 const i=args.indexOf(flag);if(i<0)continue;
 const prior=JSON.parse(fs.readFileSync(args[i+1],'utf8'));
 if(prior.hostEnclosureHash!==enclosureHash||!prior.hostWorkload||prior.hostWorkload.writes.length||prior.hostWorkload.errors.length)throw Error('Reference lacks the matching clean host-build guard; collect a new isolated reference');
}
const guard=monitorBuilds(path.resolve(__dirname,'../../temp'));
const child=spawn(process.execPath,[path.join(__dirname,'run.cjs'),...args],{stdio:['ignore','pipe','inherit']});
let pending='';child.stdout.on('data',chunk=>{pending+=chunk.toString();const lines=pending.split(/\r?\n/);pending=lines.pop();for(const line of lines)if(!/^(?:passed|failed):/.test(line))process.stdout.write(line+'\n');});
child.on('error',error=>{guard.stop();console.error(error);process.exitCode=1;});
child.on('close',code=>{
 const host=guard.stop();
 if(!fs.existsSync(reportFile)){console.error('Benchmark exited without a report');process.exitCode=1;return;}
 const report=JSON.parse(fs.readFileSync(reportFile,'utf8'));
 report.hostEnclosureHash=enclosureHash;report.hostWorkload=host;
 report.errors.push(...host.errors);
 if(host.writes.length)report.errors.push('Host workload: concurrent Creator build logs changed; run is ineligible');
 if(report.status==='running'||code===null)report.errors.push('Benchmark exited before completion');
 if(report.errors.length)report.status='failed';
 fs.writeFileSync(reportFile,JSON.stringify(report,null,2));
 console.log(report.status+': '+reportFile);
 if(code!==0||report.status!=='passed')process.exitCode=1;
});
