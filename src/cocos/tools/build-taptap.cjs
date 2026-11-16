#!/usr/bin/env node
// Shared macOS/Windows pipeline. Use installed tools and the official converter only.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {spawn,spawnSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const configTool=require('./taptap-config.cjs');
const project=path.resolve(__dirname,'..'),root=path.resolve(project,'../..'),outRoot=path.join(root,'src/out');
const args=process.argv.slice(2),options={mode:'test'};
const values=new Set(['--mode','--profile','--editor','--python','--app-id','--previous-version','--editor-user-data','--output-name']);
try{
 for(let i=0;i<args.length;i++){
  const key=args[i];
  if(['--guest','--check','--help'].includes(key))options[key.slice(2)]=true;
  else if(values.has(key)&&args[i+1]&&!args[i+1].startsWith('--'))options[key.slice(2)]=args[++i];
  else throw new Error('Unknown or incomplete option: '+key+'; use --help.');
 }
 if(options.help){console.log(`Usage: npm run pack:taptap [-- --editor <Creator> --python <Python>]
Output: src/out/<version>/SwordAndFire_<version>.zip (version automatically increments once)
Options: --mode dev|test|release|audit|preview, --profile dev|test|release,
         --guest (test only), --check (preflight only),
         --editor, --python, --app-id, --previous-version, --editor-user-data.
The pipeline validates installed tools/configuration, runs existing type checks/tests,
prepares resources, exports Cocos, converts with the official TapTap converter,
and checks version/AppID/subpackages/budgets/ZIP CRC/SHA-256. It never uploads.`);process.exit(0);}
 if(!['dev','test','release','audit','preview'].includes(options.mode))throw new Error('Invalid --mode.');
 options.profile=options.profile||(['dev','test','release'].includes(options.mode)?options.mode:'test');
 require('./build-profile.cjs').profileFor(options.profile);
 if(['dev','test','release'].includes(options.mode)&&options.profile!==options.mode)throw new Error('Build mode and gameplay profile must agree.');
 if(options.mode==='audit'&&options.profile!=='test'||options.mode==='preview'&&options.profile==='release')throw new Error('Audit uses test gameplay; a Web preview cannot be release.');
 if(options.guest&&options.mode!=='test')throw new Error('--guest requires --mode test.');
 if(options.mode==='audit'&&options['app-id'])throw new Error('Audit builds cannot bind an AppID.');
 if(options['output-name']&&!/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(options['output-name']))throw new Error('Invalid intermediate output name.');
}catch(error){console.error(error.message);process.exit(1);}

const node=process.execPath,temp=path.join(project,'temp');
let locked=false,lockFd,logs,preparedProfile=false,environment={...process.env,npm_config_offline:'true'};
const lock=path.join(temp,'taptap-build.lock');
function acquire(){
 fs.mkdirSync(temp,{recursive:true});
 try{lockFd=fs.openSync(lock,'wx');}
 catch(error){
  if(error.code!=='EEXIST')throw error;
  const pid=Number(fs.readFileSync(lock,'utf8'));
  if(!Number.isSafeInteger(pid)||pid<=0)throw new Error('Inspect the existing build lock: '+lock);
  try{process.kill(pid,0);throw new Error('Another TapTap build is running (PID '+pid+').');}
  catch(state){if(state.code!=='ESRCH')throw state;}
  fs.unlinkSync(lock);lockFd=fs.openSync(lock,'wx');
 }
 fs.writeFileSync(lockFd,String(process.pid));locked=true;
}
function release(){if(locked){fs.closeSync(lockFd);fs.unlinkSync(lock);locked=false;}}
function tool(name){return path.join(__dirname,name);}
function probe(command,argv){const r=spawnSync(command,argv,{cwd:root,env:environment,encoding:'utf8',windowsHide:true});return r.status===0?r.stdout.trim():null;}
function pythonPath(){
 const candidates=options.python||process.env.TAPTAP_PYTHON?[options.python||process.env.TAPTAP_PYTHON]:[
  'python3','python',path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'),
 ];
 for(const candidate of candidates){const executable=probe(candidate,['-c','import sys, PIL; print(sys.executable)']);if(executable)return executable;}
 throw new Error('Python 3 with Pillow is required. Pass --python <installed executable>; no dependencies are downloaded.');
}
function editorPath(){
 const explicit=options.editor||process.env.COCOS_CREATOR;
 const candidates=explicit?[explicit]:[
  process.platform==='darwin'?'/Applications/Cocos/Creator/3.8.8/CocosCreator.app/Contents/MacOS/CocosCreator':undefined,
  process.platform==='win32'?'C:\\ProgramData\\cocos\\editors\\Creator\\3.8.8\\CocosCreator.exe':undefined,
 ].filter(Boolean);
 const editor=candidates.find(candidate=>fs.existsSync(candidate)&&fs.statSync(candidate).isFile());
 if(!editor)throw new Error('Cocos Creator 3.8.8 is required. Pass --editor <installed executable>.');
 return path.resolve(editor);
}
function snapshot(){
 const files={};
 function visit(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,entry.name);if(entry.isDirectory())visit(file);else if(entry.name.endsWith('.ts'))files[path.relative(root,file).split(path.sep).join('/')]=createHash('sha256').update(fs.readFileSync(file)).digest('hex');}}
 visit(path.join(project,'assets/scripts'));return files;
}
function save(file,value){fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n');}
function run(label,command,argv,{cwd=root,stdout,stderr,accepted=[0]}={}){
 console.log(label);
 const log=stdout||path.join(logs,'steps.log'),errors=stderr||log;
 const out=fs.openSync(log,stdout?'w':'a'),err=errors===log?out:fs.openSync(errors,'w');
 if(!stdout)fs.writeSync(out,'\n'+label+'\n');
 return new Promise((resolve,reject)=>{
  const child=spawn(command,argv,{cwd,env:environment,stdio:['ignore',out,err],windowsHide:true});
  child.on('error',reject);
  child.on('close',code=>{
   fs.closeSync(out);if(err!==out)fs.closeSync(err);
   if(accepted===null||accepted.includes(code))resolve(code);
   else{console.error(fs.readFileSync(errors,'utf8').split(/\r?\n/).slice(-25).join('\n'));reject(new Error(label+' failed (exit '+code+'); '+errors));}
  });
 });
}
async function main(){
 const preview=options.mode==='preview',editor=editorPath(),python=pythonPath();
 for(const name of ['typescript/bin/tsc','tsx/cli'])require.resolve(name,{paths:[project]});
 if(!preview)for(const name of ['terser','@babel/core','@babel/preset-env','esprima'])require.resolve(name,{paths:[path.join(project,'extensions/taptap-minigame-tools/converter')]});
 const oldVersion=JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8')).version;
 const parts=configTool.versionParts(oldVersion);if(!preview)parts[2]++;
 const next=parts.join('.'),candidate=configTool.loadConfig(next);
 if(!/^[A-Za-z][A-Za-z0-9_-]*$/.test(candidate.projectName))throw new Error('English projectName must use ASCII letters, digits, underscores or hyphens for package filenames.');
 if(options['app-id']&&options['app-id']!==candidate.miniAppId)throw new Error('AppID must match release/taptap-project.json.');
 if(options['previous-version']&&configTool.compareVersions(next,options['previous-version'])<=0)throw new Error('Version must exceed --previous-version.');
 const validation=probe(node,[tool('taptap-config.cjs'),'--json','--mode',options.mode,'--profile',options.profile]);
 if(!validation)throw new Error('Build configuration validation failed.');
 if(options.profile==='release'&&!probe(node,[tool('release-notes.cjs'),'--check-baseline']))throw new Error('Published release baseline is unavailable.');
 const delivery=path.join(outRoot,next);
 if(!preview&&fs.existsSync(delivery))throw new Error('Version directory already exists: '+delivery);
 const name=options['output-name']||(preview?'taptap-preview':'taptap');
 if(options.check){console.log(JSON.stringify({editor,python,mode:options.mode,profile:options.profile,nextVersion:next,output:preview?path.join(project,'build',name):path.join(delivery,candidate.projectName+'_'+next+'.zip'),uploads:false},null,2));return;}
 acquire();
 // Tests using the project's existing `python` command share the selected interpreter.
 const aliases=path.join(temp,'taptap-tools');fs.mkdirSync(aliases,{recursive:true});
 if(process.platform!=='win32'){const alias=path.join(aliases,'python');if(fs.readdirSync(aliases).includes('python'))fs.unlinkSync(alias);fs.symlinkSync(python,alias);}
 const pathKey=Object.keys(environment).find(key=>key.toLowerCase()==='path')||'PATH';
 environment[pathKey]=[aliases,path.dirname(python),environment[pathKey]||''].join(path.delimiter);
 logs=path.join(temp,'taptap-checks');fs.mkdirSync(logs,{recursive:true});
 await run('Check TypeScript',node,[require.resolve('typescript/bin/tsc',{paths:[project]}),'--noEmit'],{cwd:project,stdout:path.join(logs,'types.log')});
 await run('Check core TypeScript',node,[require.resolve('typescript/bin/tsc',{paths:[project]}),'-p','tsconfig.core.json','--noEmit'],{cwd:project,stdout:path.join(logs,'core.log')});
 const tests=fs.readdirSync(path.join(project,'tests')).filter(file=>file.endsWith('.test.ts')).sort().map(file=>path.join(project,'tests',file));
 await run('Run existing tests',node,[require.resolve('tsx/cli',{paths:[project]}),'--test',...tests],{cwd:project,stdout:path.join(logs,'tests.log')});
 const allocation=[tool('taptap-config.cjs'),'--prepare','--json','--mode',options.mode,'--profile',options.profile];
 if(!preview)allocation.push('--version','patch');
 if(options['app-id'])allocation.push('--app-id',options['app-id']);
 if(options['previous-version'])allocation.push('--previous-version',options['previous-version']);
 if(JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8')).version!==oldVersion)throw new Error('Version changed during checks; start again before allocating a package.');
 preparedProfile=true;
 const allocated=spawnSync(node,allocation,{cwd:root,env:environment,encoding:'utf8',windowsHide:true});
 if(allocated.status!==0)throw new Error(allocated.stderr||'Release configuration preparation failed.');
 const releaseInfo=JSON.parse(allocated.stdout);if(releaseInfo.version!==next)throw new Error('Version changed during preflight; inspect the allocated version.');
 if(!preview){
  fs.mkdirSync(outRoot,{recursive:true});fs.mkdirSync(delivery,{recursive:false});const previousLogs=logs;logs=path.join(delivery,'logs');fs.mkdirSync(logs);
  for(const file of ['types.log','core.log','tests.log'])fs.copyFileSync(path.join(previousLogs,file),path.join(logs,file));
 }
 const state={version:next,mode:options.guest?'guest-test':options.mode,profile:options.profile,status:'building',startedAt:new Date().toISOString(),uploaded:false,platformVerified:false};
 const stateFile=path.join(logs,'build.json');save(stateFile,state);save(path.join(logs,'release.json'),releaseInfo);
 const before=snapshot();save(path.join(logs,'source-before.json'),before);
 console.log('Version: '+next+'; output: '+(preview?path.join(project,'build',name):delivery));
 try{
  await run('Prepare navigation WASM',node,[tool('prepare-navigation-wasm.cjs'),'--prepare']);
  await run('Prepare resources',python,[tool('prepare-taptap.py'),'--platform',preview?'web-mobile':'wechatgame','--output-name',name,'--mode',options.mode,'--profile',options.profile]);
  await run('Verify mesh caches',python,[tool('refresh-morph-build-cache.py'),'--project',project]);
  const notesDirectory=path.join(temp,'release-notes-'+name);
  if(options.profile==='release')await run('Prepare release update log',node,[tool('release-notes.cjs'),'--prepare','--version',next,'--output',notesDirectory]);
  const creatorOut=path.join(logs,'creator.log'),creatorErr=path.join(logs,'creator-error.log'),creatorArgs=['--project',project,'--build','configPath='+path.join(temp,'build-'+name+'.json')];
  if(options['editor-user-data'])creatorArgs.unshift('--user-data-dir='+path.resolve(options['editor-user-data']));
  for(let attempt=1;attempt<=2;attempt++){
   const code=await run('Export Cocos (attempt '+attempt+')',editor,creatorArgs,{stdout:creatorOut,stderr:creatorErr,accepted:null});
   const stdout=fs.readFileSync(creatorOut,'utf8'),all=stdout+fs.readFileSync(creatorErr,'utf8');
   if([0,36].includes(code)&&stdout.includes('build Task ('+name+') Finished')){
    if(/Script .* attached to .* is missing or invalid|Missing class:/.test(all))throw new Error('Cocos exported a missing script component; inspect '+creatorErr);
    break;
   }
   if(attempt===1&&/UNKNOWN: unknown error, open.*[\\/]settings[\\/]v2[\\/]packages[\\/]engine\.json/.test(all)){
    fs.copyFileSync(creatorOut,creatorOut+'.attempt1');fs.copyFileSync(creatorErr,creatorErr+'.attempt1');continue;
   }
   throw new Error('Creator did not finish this build; inspect '+creatorOut);
  }
  const build=path.join(project,'build',name);
  await run('Check compiled gameplay profile',node,[tool('build-profile.cjs'),'--verify-build',build,'--profile',options.profile]);
  if(options.profile==='release'){
   await run('Check release source snapshot',node,[tool('release-notes.cjs'),'--verify-source',notesDirectory]);
   for(const file of ['RELEASE_NOTES.md','source-manifest.json','release-changes.json'])fs.copyFileSync(path.join(notesDirectory,file),path.join(build,file));
  }
  await run('Check renderer/startup',node,[tool('render-policy.cjs'),'--build',build]);
  await run('Check exported WASM',node,[tool('prepare-navigation-wasm.cjs'),'--build',build]);
  const notices=path.join(project,'build-templates/web-desktop/THIRD_PARTY_NOTICES.txt');if(fs.existsSync(notices))fs.copyFileSync(notices,path.join(build,'THIRD_PARTY_NOTICES.txt'));
  if(preview){
   const index=path.join(build,'index.html');fs.writeFileSync(index,fs.readFileSync(index,'utf8').replace('<head>','<head><script>globalThis.__SINGULARITY_BUNDLE_PREVIEW__=true;</script>'));
   await run('Copy preview branding',node,[tool('copy-branding.cjs'),build]);
  }else{
   const converted=path.join(project,'build',name+'-package'),conversion=[tool('convert-taptap.cjs'),'--source',build,'--target',converted,'--version',next,'--profile',options.profile];
   if(options.mode==='audit')conversion.push('--audit-only');else conversion.push('--app-id',releaseInfo.miniAppId);
   if(options.mode==='test')conversion.push('--test-package');if(options.guest)conversion.push('--guest-test');
   await run('Run official TapTap conversion',node,conversion);
   await run('Check ZIP, identity, subpackages and sizes',python,[tool('report-taptap.py'),converted,'--output',outRoot]);
  }
  await run('Check final release configuration',node,[tool('taptap-config.cjs'),'--check','--mode',options.mode,'--profile',options.profile]);
  const after=snapshot();save(path.join(logs,'source-after.json'),after);
  const changed=[...new Set([...Object.keys(before),...Object.keys(after)])].filter(file=>before[file]!==after[file]);
  if(changed.length)throw new Error('Source changed during export; do not deliver this build: '+changed.join(', '));
  state.status='complete';state.finishedAt=new Date().toISOString();state.sourceScripts=Object.keys(after).length;
  if(!preview){const settings=JSON.parse(fs.readFileSync(path.join(delivery,'upload-settings.json'),'utf8'));state.package=settings.packageFilename;state.sha256=settings.packageSha256;console.log('ZIP: '+state.package+'\nSize: '+(settings.uploadZipBytes/1e6).toFixed(2)+' MB\nSHA-256: '+state.sha256);}
  else console.log('Preview: '+build);
  save(stateFile,state);
 }catch(error){state.status='failed';state.error=error.message;save(stateFile,state);throw error;}
}
main().catch(error=>{console.error(error.message);process.exitCode=1;}).finally(()=>{
 try{
  if(preparedProfile&&options.profile!=='test'){
   const restored=spawnSync(node,[tool('taptap-config.cjs'),'--prepare','--json','--mode','preview','--profile','test'],{cwd:root,env:environment,encoding:'utf8',windowsHide:true});
   if(restored.status!==0){console.error('Could not restore normal test gameplay configuration: '+restored.stderr);process.exitCode=1;}
  }
 }finally{release();}
});
