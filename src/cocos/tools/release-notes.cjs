// Compare verified published source manifests, including uncommitted build inputs.
// Git enumerates sources; built-in hashing avoids new dependencies or a network service.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'../../..');
const INPUTS=['package.json','src/cocos/assets','src/cocos/build-templates','src/cocos/settings',
 'src/cocos/tools','src/cocos/*.ps1','src/cocos/package*.json','src/cocos/tsconfig*.json','src/cocos/release/taptap*.json','src/cocos/release/changes.json'];
const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const encode=value=>JSON.stringify(value,null,2)+'\n';
const git=(root,args)=>execFileSync('git',args,{cwd:root,encoding:'utf8',maxBuffer:32*1024*1024});
function hashFile(file){const digest=crypto.createHash('sha256'),fd=fs.openSync(file,'r'),buffer=Buffer.alloc(1024*1024);try{let count;while((count=fs.readSync(fd,buffer,0,buffer.length,null))>0)digest.update(buffer.subarray(0,count));}finally{fs.closeSync(fd);}return digest.digest('hex');}
function compareVersions(a,b){const parse=v=>{if(!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(v))throw new Error('Invalid release version: '+v);return v.split('.').map(Number);};const x=parse(a),y=parse(b);for(let i=0;i<3;i++)if(x[i]!==y[i])return Math.sign(x[i]-y[i]);return 0;}
function changeEntries(root){
 const entries=read(path.join(root,'src/cocos/release/changes.json')),ids=new Set();
 if(!Array.isArray(entries))throw new Error('Release changes must be an array.');
 for(const entry of entries){if(!/^[a-zA-Z0-9_-]+$/.test(entry.id)||ids.has(entry.id)||!['新增','调整','修复','兼容与存档','已知问题'].includes(entry.category)||typeof entry.summary!=='string'||!entry.summary.trim())throw new Error('Invalid or duplicate release change entry.');ids.add(entry.id);}
 return entries;
}
function sourceSnapshot(root,version){
 const files=[...new Set(git(root,['ls-files','-z','--cached','--others','--exclude-standard','--',...INPUTS]).split('\0').filter(Boolean))].sort();
 const entries=[];
 for(const relative of files){const file=path.resolve(root,relative);if(!file.startsWith(root+path.sep))throw new Error('Source path escapes repository.');if(!fs.existsSync(file))continue;if(!fs.lstatSync(file).isFile())throw new Error('Build sources must be regular files: '+relative);entries.push({path:relative,bytes:fs.statSync(file).size,sha256:hashFile(file)});}
 return {schemaVersion:1,version,profile:'release',gitCommit:git(root,['rev-parse','HEAD']).trim(),
  dirty:!!git(root,['status','--porcelain','--untracked-files=normal']).trim(),inputs:INPUTS,
  changeIds:changeEntries(root).map(entry=>entry.id),entries};
}
function publishedBaseline(root){
 const registry=read(path.join(root,'src/cocos/release/published-release.json'));
 if(registry.schemaVersion!==1)throw new Error('Unknown published release registry schema.');
 if(!registry.lastPublished){
  const identity=read(path.join(root,'src/cocos/release/taptap-project.json'));
  if(identity.publiclyReleased!==false)throw new Error('Published baseline is missing; record the actual published release before making another release.');
  return null;
 }
 const previous=registry.lastPublished;
 compareVersions(previous.version,previous.version);
 const base=path.resolve(root,'src/cocos/release/published'),file=path.resolve(root,previous.manifest);
 if(!file.startsWith(base+path.sep)||!fs.existsSync(file)||hashFile(file)!==previous.manifestSha256)throw new Error('Published source manifest is missing or its checksum differs.');
 const manifest=read(file);
 if(manifest.profile!=='release'||manifest.version!==previous.version||manifest.schemaVersion!==1||!Array.isArray(manifest.entries)||!Array.isArray(manifest.changeIds))throw new Error('Invalid published release source manifest.');
 const seen=new Set();for(const entry of manifest.entries){if(typeof entry.path!=='string'||seen.has(entry.path)||!/^([a-f0-9]{64})$/.test(entry.sha256))throw new Error('Invalid published source entry.');seen.add(entry.path);}
 return {...previous,source:manifest};
}
function diffSources(previous,current){
 const old=new Map((previous?.entries||[]).map(entry=>[entry.path,entry])),now=new Map(current.entries.map(entry=>[entry.path,entry])),changes=[];
 for(const [file,entry]of now){const before=old.get(file);if(!before||before.sha256!==entry.sha256)changes.push({path:file,kind:before?'modified':'added',before:before?.sha256||null,after:entry.sha256});}
 for(const [file,entry]of old)if(!now.has(file))changes.push({path:file,kind:'deleted',before:entry.sha256,after:null});
 return changes.sort((a,b)=>a.path.localeCompare(b.path,'en'));
}
function prepare({root=ROOT,version,output}){
 root=path.resolve(root);compareVersions(version,version);
 if(read(path.join(root,'package.json')).version!==version)throw new Error('Release notes version must match root package.json.');
 const baseline=publishedBaseline(root);
 if(baseline&&compareVersions(version,baseline.version)<=0)throw new Error('Release version must be newer than the last published release.');
 const source=sourceSnapshot(root,version),changes=diffSources(baseline?.source,source);
 const included=new Set(baseline?.source.changeIds||[]),notes=changeEntries(root).filter(entry=>!included.has(entry.id));
 const generatedAt=new Date().toISOString(),date=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(generatedAt));
 const lines=[`# ${version} release 更新日志`,'',`日期：${date}（Asia/Shanghai）`,'状态：本地 release 候选包；尚未上传、提审或上线。',
  `对比：${baseline?baseline.version+'（已登记正式发布）':'首次发布（仓库记录尚未正式发布）'} → ${version}`,
  `源码：${source.gitCommit}${source.dirty?' + 工作区变更':''}；完整 SHA-256 清单见 source-manifest.json。`,'','## 更新内容',''];
 for(const category of ['新增','调整','修复','兼容与存档','已知问题']){const selected=notes.filter(entry=>entry.category===category);if(selected.length){lines.push(`### ${category}`,'',...selected.map(entry=>'- '+entry.summary),'');}}
 if(!notes.length)lines.push('本次没有新增的语义更新条目；实际源码与资源差异列于下方，不据文件名推断未验证的玩法效果。','');
 if(!baseline)lines.push('首次候选包的可玩内容范围沿用当前发布配置：第一、第二章；后续章节不据此声明已开放。','');
 const groups=new Map();
 for(const change of changes){const match=change.path.match(/src\/cocos\/assets\/scripts\/features\/([^/]+)/);const group=match?'功能模块 / '+match[1]:change.path.includes('/assets/resources/')?'游戏资源':change.path.includes('/assets/scripts/')?'公共运行代码':'构建与发布配置';if(!groups.has(group))groups.set(group,[]);groups.get(group).push(change);}
 lines.push('## 源码与资源差异','');
 for(const [group,items]of groups){lines.push(`- ${group}：新增 ${items.filter(x=>x.kind==='added').length}、修改 ${items.filter(x=>x.kind==='modified').length}、删除 ${items.filter(x=>x.kind==='deleted').length} 个文件。`);}
 if(!changes.length)lines.push('- 构建输入与上一正式发布清单一致。');
 lines.push('','完整路径和前后哈希见 release-changes.json。输入清单包含构建依赖，文件数量不代表已开放功能数量。','','## 验证与已知限制','',
  '- 本日志在导出前自动生成；只有最终包体检查通过后才归档并交付。随包 report.json 记录本地包体、分包及校验结果。',
  '- TapTap 平台登录、触控、前后台恢复、存档和目标真机表现仍需对应设备证据；本地 release 包不代表已通过平台验收。',
  '- 构建不会更新正式发布基线；实际发布后才登记该交付产物。','');
 fs.mkdirSync(output,{recursive:true});
 fs.writeFileSync(path.join(output,'source-manifest.json'),encode(source));
 fs.writeFileSync(path.join(output,'release-changes.json'),encode({schemaVersion:1,generatedAt,version,baseline:baseline?{version:baseline.version,manifest:baseline.manifest,manifestSha256:baseline.manifestSha256}:null,notes,changes}));
 fs.writeFileSync(path.join(output,'RELEASE_NOTES.md'),lines.join('\n'));
 return {version,previousVersion:baseline?.version||null,firstRelease:!baseline,
  sourceManifestSha256:hashFile(path.join(output,'source-manifest.json')),notesSha256:hashFile(path.join(output,'RELEASE_NOTES.md')),
  changesSha256:hashFile(path.join(output,'release-changes.json'))};
}
function verifySource(directory,root=ROOT){const saved=read(path.join(directory,'source-manifest.json')),current=sourceSnapshot(path.resolve(root),saved.version);if(encode(current)!==encode(saved))throw new Error('Build inputs changed during Cocos export; rebuild to generate release notes for the actual source.');return saved;}
function verifyNotes(directory,version){
 const source=read(path.join(directory,'source-manifest.json')),changes=read(path.join(directory,'release-changes.json'));
 if(source.version!==version||source.profile!=='release'||changes.version!==version)throw new Error('Release notes do not match this release.');
 return {version,previousVersion:changes.baseline?.version||null,firstRelease:!changes.baseline,
  sourceManifestSha256:hashFile(path.join(directory,'source-manifest.json')),notesSha256:hashFile(path.join(directory,'RELEASE_NOTES.md')),changesSha256:hashFile(path.join(directory,'release-changes.json'))};
}
function recordPublished(directory,root=ROOT){
 const settings=read(path.join(directory,'upload-settings.json'));
 if(settings.buildMode!=='release'||settings.releasePreflightPassed!==true||!settings.releaseNotes)throw new Error('Only a checked release artifact can be recorded as published.');
 const zip=path.join(directory,path.basename(settings.packageFilename));
 if(hashFile(zip)!==settings.packageSha256)throw new Error('Published ZIP checksum mismatch.');
 const notes=verifyNotes(directory,settings.version);
 if(encode(notes)!==encode(settings.releaseNotes))throw new Error('Published release metadata differs from the verified artifact.');
 const previous=publishedBaseline(root);
 if(previous&&compareVersions(settings.version,previous.version)<=0)throw new Error('Published release version must strictly increase.');
 // Check the sidecars against the files actually embedded in this ZIP.
 const verifier='import hashlib,json,sys,zipfile\nwith zipfile.ZipFile(sys.argv[1]) as z:\n print(json.dumps({n:hashlib.sha256(z.read(n)).hexdigest() for n in ["RELEASE_NOTES.md","source-manifest.json","release-changes.json"]}))';
 const embedded=JSON.parse(execFileSync('python',['-c',verifier,zip],{encoding:'utf8'}));
 if(embedded['source-manifest.json']!==notes.sourceManifestSha256||embedded['RELEASE_NOTES.md']!==notes.notesSha256||embedded['release-changes.json']!==notes.changesSha256)throw new Error('Release sidecars differ from the actual published ZIP.');
 const relative=`src/cocos/release/published/${settings.version}.json`,manifest=path.join(root,relative);
 fs.mkdirSync(path.dirname(manifest),{recursive:true});
 if(fs.existsSync(manifest))throw new Error('Published manifest already exists; preserving it.');
 fs.copyFileSync(path.join(directory,'source-manifest.json'),manifest);
 const record={schemaVersion:1,lastPublished:{version:settings.version,publishedAt:new Date().toISOString(),manifest:relative,manifestSha256:notes.sourceManifestSha256,packageSha256:settings.packageSha256}};
 fs.writeFileSync(path.join(root,'src/cocos/release/published-release.json'),encode(record));
 return record;
}
module.exports={sourceSnapshot,publishedBaseline,diffSources,prepare,verifySource,verifyNotes,recordPublished,hashFile};
if(require.main===module){try{
 const args=process.argv.slice(2),get=name=>{const i=args.indexOf(name);if(i<0||!args[i+1]||args[i+1].startsWith('--'))throw new Error('Missing '+name);return args[i+1];};
 let result;
 if(args.includes('--check-baseline'))result=publishedBaseline(ROOT);
 else if(args.includes('--verify-source'))result={version:verifySource(get('--verify-source')).version,verified:true};
 else if(args.includes('--record-published'))result=recordPublished(path.resolve(get('--record-published')));
 else if(args.includes('--prepare'))result=prepare({version:get('--version'),output:path.resolve(get('--output'))});
 else throw new Error('Use --check-baseline, --prepare, --verify-source or --record-published.');
 console.log(JSON.stringify(result));
}catch(error){console.error(error.message);process.exitCode=1;}}
