// Root package.json is the version source. Platform identity lives in taptap-project.json.
const fs=require('node:fs'),path=require('node:path');
const {profileFor,runtimeSource}=require('./build-profile.cjs');
const project=path.resolve(__dirname,'..'),root=path.resolve(project,'../..');
const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));
function write(file,value){
 const text=typeof value==='string'?value:JSON.stringify(value,null,2)+'\n';
 if(fs.existsSync(file)&&fs.readFileSync(file,'utf8')===text)return;
 try{fs.writeFileSync(file,text);}catch(error){
  // Windows can reject the truncating open while an existing file permits r+.
  if(process.platform!=='win32'||error.code!=='UNKNOWN'||!fs.existsSync(file))throw error;
  const fd=fs.openSync(file,'r+');
  try{fs.writeFileSync(fd,text);fs.ftruncateSync(fd,Buffer.byteLength(text));}finally{fs.closeSync(fd);}
 }
}
function versionParts(value){if(typeof value!=='string'||!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(value))throw new Error('TapTap version must be three non-negative integers (x.y.z), without v, prerelease or build suffix.');const parts=value.split('.').map(Number);if(parts.some(x=>!Number.isSafeInteger(x)))throw new Error('Version component is too large.');return parts;}
function compareVersions(a,b){const x=versionParts(a),y=versionParts(b);for(let i=0;i<3;i++)if(x[i]!==y[i])return x[i]>y[i]?1:-1;return 0;}
function loadConfig(versionOverride){
 require('./render-policy.cjs').check(project);
 const pkg=read(path.join(root,'package.json')),identity=read(path.join(project,'release/taptap-project.json')),profile=read(path.join(project,'release/taptap.json')),auth=read(path.join(project,'release/taptap-auth.json'));
 if(versionOverride)pkg.version=versionOverride;
 if(Object.keys(identity).some(k=>/secret|password|privatekey|token/i.test(k)))throw new Error('Platform identity configuration must contain public values only.');
 if('version' in identity)throw new Error('Keep the game version only in root package.json.');
 versionParts(pkg.version);
 if(!/^tap[a-z0-9]+$/i.test(identity.miniAppId)||!/^\d+$/.test(identity.gameId)||!identity.title?.trim()||!identity.projectName?.trim())throw new Error('Missing real MiniApp ID, game ID or title/projectName.');
 if(identity.lastSubmittedVersion&&compareVersions(pkg.version,identity.lastSubmittedVersion)<=0)throw new Error('Version must be higher than lastSubmittedVersion.');
 if(identity.minimumBaseLibraryVersion!==null)versionParts(identity.minimumBaseLibraryVersion);
 if(!['landscape','portrait'].includes(profile.orientation))throw new Error('Invalid orientation.');
 if(typeof profile.computationWasm!=='boolean')throw new Error('Set computationWasm to true or false in release/taptap.json; this is the default for migrated CPU calculations.');
 if(typeof profile.engineWasmSubpackage!=='boolean')throw new Error('Set engineWasmSubpackage to true or false in release/taptap.json; this controls Cocos module packages, not platform WASM function splitting.');
 if(!Number.isFinite(profile.initialPackageBudgetMiB)||profile.initialPackageBudgetMiB<=0||!Number.isSafeInteger(identity.uploadZipLimitBytes)||identity.uploadZipLimitBytes<=0)throw new Error('Invalid package size policy.');
 if(Object.keys(auth).sort().join(',')!=='mode,timeoutMs'||auth.mode!=='platform')throw new Error('Use TapTap platform login: auth config contains only mode: platform and timeoutMs. No custom auth URL or Secret belongs here.');
 if(!Number.isInteger(auth.timeoutMs)||auth.timeoutMs<1000||auth.timeoutMs>60000)throw new Error('Auth timeout must be 1000..60000 ms.');
 const keys=['request','connectSocket','uploadFile','downloadFile'];if(Object.keys(identity.networkTimeout).sort().join(',')!==keys.sort().join(',')||Object.values(identity.networkTimeout).some(x=>!Number.isInteger(x)||x<1000||x>60000))throw new Error('Configure all four network timeouts in 1000..60000 ms.');
 if(identity.networkTimeout.request<auth.timeoutMs)throw new Error('Global request timeout must cover login request timeout.');
 if(identity.branding){for(const key of ['icon','iconLarge','coverLandscape','coverSquare','webIcon','favicon']){const file=path.resolve(project,identity.branding[key]||'');if(!file.startsWith(project+path.sep)||!fs.existsSync(file))throw new Error('Missing project branding asset: '+key);}}
 return {version:pkg.version,...identity,orientation:profile.orientation,showStatusBar:false,auth,localBlockers:[],
  consoleChecks:['Confirm unique increasing version against live/review packages.','Use platform-parsed minimum library version.','Verify TapTap platform login, foreground session renewal and account switching on device.','Confirm platform account/compliance capabilities and complete privacy declaration.','Complete credentials/filing and real-device self-test before review.'],
  sources:{version:'../../package.json',identity:'release/taptap-project.json',resources:'release/taptap.json',auth:'release/taptap-auth.json'}};
}
function generatedSources(config){return {
 'shared/BuildProfile.ts':runtimeSource(config.buildProfile?.name||'test'),
 'app/BuildInfo.ts':'/** Generated by tools/taptap-config.cjs. */\nexport const BUILD_INFO = '+JSON.stringify({title:config.title,version:config.version,miniAppId:config.miniAppId,orientation:config.orientation})+' as const;\n',
 'platform/TapAuthConfig.ts':'/** Generated by tools/taptap-config.cjs. Public values only. */\nexport const TAP_AUTH_CONFIG = '+JSON.stringify(config.auth)+';\n'};}
function synchronize(config){
 for(const file of [path.join(project,'package.json'),path.join(project,'package-lock.json')]){const value=read(file);value.version=config.version;if(value.packages?.[''])value.packages[''].version=config.version;write(file,value);}
 const runtime=path.join(project,'assets/scripts');
 for(const [name,text]of Object.entries(generatedSources(config)))write(path.join(runtime,name),text);
}
module.exports={loadConfig,synchronize,versionParts,compareVersions};
if(require.main===module){try{
 const args=process.argv.slice(2),get=(flag,fallback)=>args.includes(flag)?args[args.indexOf(flag)+1]:fallback;
 let updatedPackage;
 if(args.includes('--version')){
  const file=path.join(root,'package.json'),pkg=read(file),old=pkg.version,requested=get('--version');let next=requested;
  if(['patch','minor','major'].includes(requested)){const parts=versionParts(old),index={major:0,minor:1,patch:2}[requested];parts[index]++;for(let i=index+1;i<3;i++)parts[i]=0;next=parts.join('.');}
  if(compareVersions(next,old)<=0)throw new Error('New version must be higher than '+old);pkg.version=next;updatedPackage=pkg;
 }
 const config=loadConfig(updatedPackage?.version),mode=get('--mode','test'),provided=get('--app-id',config.miniAppId),previous=get('--previous-version');
 if(!['release','audit','preview','test','dev'].includes(mode))throw new Error('Invalid build mode.');
 const profile=get('--profile',['dev','test','release'].includes(mode)?mode:'test');
 if(['dev','test','release'].includes(mode)&&profile!==mode)throw new Error('Build mode and gameplay profile must agree.');
 if(mode==='audit'&&profile!=='test')throw new Error('Audit builds use normal test gameplay.');
 config.buildProfile=profileFor(profile);
 config.buildMode=mode;
 if(provided!==config.miniAppId)throw new Error('AppID must match taptap-project.json.');
 if(previous&&compareVersions(config.version,previous)<=0)throw new Error('Version must be higher than --previous-version.');
 if(mode==='release'&&config.localBlockers.length)throw new Error(config.localBlockers.join(' '));
 if(updatedPackage)write(path.join(root,'package.json'),updatedPackage);
 if(args.includes('--prepare')||args.includes('--version'))synchronize(config);
 if(args.includes('--check')){
  for(const file of ['package.json','package-lock.json']){const pkg=read(path.join(project,file));if(pkg.version!==config.version||pkg.packages?.['']&&pkg.packages[''].version!==config.version)throw new Error('Version drift in '+file+'; run npm run version:tap or prepare the TapTap build.');}
  for(const [file,text]of Object.entries(generatedSources(config))){const target=path.join(project,'assets/scripts',file);if(!fs.existsSync(target)||fs.readFileSync(target,'utf8').replace(/\r\n/g,'\n')!==text)throw new Error('Generated config drift in '+file+'; prepare the TapTap build.');}
 }
 if(args.includes('--json'))console.log(JSON.stringify(config));else console.log('TapTap '+config.version+'; '+config.miniAppId+'; mode='+mode+'; login=TapTap platform (no custom auth service)');
}catch(error){console.error(error.message);process.exitCode=1;}}
