// Reuse the installed official converter. This entry point never installs dependencies.
const fs=require('node:fs');
const path=require('node:path');
const project=path.resolve(__dirname,'..');
const {loadConfig}=require('./taptap-config.cjs');
const release=loadConfig();
const args=process.argv.slice(2);
const value=name=>{
 const index=args.indexOf(name);
 if(index<0||!args[index+1]||args[index+1].startsWith('--'))throw new Error('Missing argument '+name);
 return args[index+1];
};
const audit=args.includes('--audit-only');
const testPackage=args.includes('--test-package');
const guestTest=args.includes('--guest-test');
const {profileFor,verifyBuild}=require('./build-profile.cjs');
const profile=profileFor(args.includes('--profile')?value('--profile'):'test');
if(testPackage&&profile.name!=='test')throw new Error('--test-package requires the test gameplay profile.');
if(audit&&profile.name!=='test')throw new Error('Audit packages must use normal test gameplay.');
if(audit&&testPackage)throw new Error('An audit package cannot also be an upload-test package.');
if(guestTest&&(profile.name!=='test'||audit))throw new Error('Guest access is allowed only in test packages.');
const source=path.resolve(value('--source'));
const target=path.resolve(value('--target'));
const buildRoot=fs.realpathSync(path.join(project,'build'))+path.sep;
for(const dir of [source,target]){
 if(!dir.startsWith(buildRoot)||dir===path.resolve(buildRoot))throw new Error('Conversion paths must stay inside the project build directory.');
 if(fs.existsSync(dir)&&!fs.realpathSync(dir).startsWith(buildRoot))throw new Error('Resolved conversion path escapes the project build directory.');
}
if(fs.existsSync(path.join(target,'game'))&&!fs.realpathSync(path.join(target,'game')).startsWith(buildRoot))throw new Error('Resolved output game directory escapes the build workspace.');
if(source===target||source.startsWith(target+path.sep)||target.startsWith(source+path.sep))throw new Error('Source and target must be separate build directories.');
const appId=args.includes('--app-id')?value('--app-id'):'';
if(args.includes('--version')&&value('--version')!==release.version)throw new Error('Version must match root package.json.');
if(!audit&&!appId)throw new Error('A real TapTap minigame AppID is required outside audit mode.');
if(audit&&appId)throw new Error('Audit packages cannot contain a platform identity.');
if(!audit&&(appId!==release.miniAppId||profile.name==='release'&&release.localBlockers.length))throw new Error('Release identity/login configuration is not ready.');
verifyBuild(source,profile.name);
const releaseNotes=profile.name==='release'?require('./release-notes.cjs').verifyNotes(source,release.version):null;
if(!releaseNotes)for(const file of ['RELEASE_NOTES.md','source-manifest.json','release-changes.json'])if(fs.existsSync(path.join(source,file)))throw new Error('Rebuild the export: non-release source contains stale release metadata.');
const extension=path.join(project,'extensions/taptap-minigame-tools');
if(!fs.existsSync(path.join(extension,'converter/node_modules')))throw new Error('Official converter dependencies are missing. Automatic network installation is disabled.');
if(!/^[A-Za-z][A-Za-z0-9_-]*$/.test(release.projectName))throw new Error('English projectName must use ASCII letters, digits, underscores or hyphens for package filenames.');
const buildMode=audit?'audit':guestTest?'guest-test':profile.name;
const builtAt=new Date().toISOString();
const buildStamp=builtAt.replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');
const converterVersion=require(path.join(extension,'package.json')).version;
const packageFilename=`${release.projectName}_${release.version}_TapTap_${audit?'audit_':guestTest?'guest_':''}${buildStamp}_${profile.name}.zip`;
const releaseInfo={schemaVersion:1,projectName:release.projectName,title:release.title,version:release.version,
 platform:'TapTap-minigame',buildMode,buildProfile:profile,releaseNotes,builtAt,timeZone:'UTC',packageFilename,
 miniAppId:audit?null:release.miniAppId,orientation:release.orientation,cocosVersion:'3.8.8',converterVersion,
 contentScope:{playableChapters:[1,2],plannedChapters:[3,4,5,6,7,8]},
 loginMode:guestTest?'guest':'platform',localSaveOnly:true,
 loginProvider:'taptap-minigame',customAuthService:false,identityExchange:false,localBlockers:release.localBlockers,
 platformValidated:false,uploadPerformed:false};
// Native entry configuration must run before any Cocos modules. Always overwrite
// the previous profile so converting the same source cannot retain guest access.
const entryFile=path.join(source,'game.js');
const entry=fs.readFileSync(entryFile,'utf8').replace(/^\s*globalThis\.__SINGULARITY_GUEST_TEST__\s*=\s*(?:true|false);[^\n]*\n?/gm,'');
fs.writeFileSync(entryFile,`globalThis.__SINGULARITY_GUEST_TEST__ = ${guestTest};\n`+entry);
const configFile=path.join(source,'game.json');
const config=JSON.parse(fs.readFileSync(configFile,'utf8'));
config.deviceOrientation=release.orientation;
delete config.orientation;
config.showStatusBar=release.showStatusBar;
config.networkTimeout=release.networkTimeout;
config.productName=release.title;config.productVersion=release.version;
if(release.companyName)config.companyName=release.companyName;else delete config.companyName;
config.subPackages=config.subPackages||config.subpackages||[];
delete config.subpackages; // TapTap's documented key is camelCase.
for(const pack of config.subPackages){
 const dir=path.resolve(source,pack.root);
 if(!dir.startsWith(source+path.sep)||!fs.existsSync(path.join(dir,'game.js')))throw new Error('Invalid Cocos subpackage '+pack.name);
}
fs.writeFileSync(configFile,JSON.stringify(config,null,2)+'\n');
const projectFile=path.join(source,'project.config.json');
const projectConfig=JSON.parse(fs.readFileSync(projectFile,'utf8'));
projectConfig.projectname=release.projectName;
delete projectConfig.libVersion; // WeChat devtools value is not TapTap's upload minimum library setting.
if(audit)delete projectConfig.appid;else projectConfig.appid=appId;
fs.writeFileSync(projectFile,JSON.stringify(projectConfig,null,2)+'\n');
fs.writeFileSync(path.join(source,'release-info.json'),JSON.stringify(releaseInfo,null,2)+'\n');
fs.writeFileSync(path.join(source,'BUILD_README.txt'),[
 `${release.title} / ${release.projectName} ${release.version}`,
 `包名：${packageFilename}`,
 `平台：TapTap 小游戏；构建类型：${buildMode}；方向：${release.orientation}`,
 `玩法档位：${profile.name}；技能无冷却：${profile.noSkillCooldown}；怪物经验倍率：${profile.monsterExperienceMultiplier}；每日经验不限：${profile.unlimitedDailyExperience}`,
 `Boss 高级掉落：${profile.guaranteedBossHighTierLoot?'DEV 每次有效击杀分别结算一件传奇和一件神器；唯一装备已集齐／数量已满时沿用重复补偿':'正常概率与保底'}。`,
 `快速验证工具：${profile.developmentTools?'暂停／设置 → 旅途中的 DEV 快速验证，手动补给、成长与清除 Boss 再战等待':'未开放'}。`,
 `本机数据：${profile.storagePrefix?'dev 独立存储空间，不能读写正常进度':'正常存储空间'}。`,
 `构建时间：${builtAt}（UTC）；Cocos Creator 3.8.8；官方转换器 ${converterVersion}`,
 `MiniApp ID：${releaseInfo.miniAppId||'未绑定，仅本地审计'}`,
 '内容范围：第一、二章可玩；第三至八章保留规划。',
 guestTest?'登录模式：游客测试，未登录 TapTap；仅使用本机存档，不提供云存档或跨设备同步。':'登录模式：直接调用 TapTap 小游戏 tap.login；回到前台调用 tap.checkSession，失效后重新登录。无需自建登录服务。',
 '账号边界：未执行服务端 code2Session，不取得 openid、不创建游戏账号或自定义 token；不以临时 code 标识玩家。本机存档尚未按账号隔离或接入云同步。',
 '完整 ZIP 由官方转换器生成，所有分包已包含；上传时直接选择 ZIP，不要额外套一层目录。',
 'release-info.json 记录构建信息；包旁的报告和 SHA-256 文件记录体积与校验值。',
 ...release.localBlockers.map(blocker=>'待完成：'+blocker),
 '本次仅完成本地构建，尚未上传、提审、发布或通过 TapTap 真机验收。',
 audit?'审计包未绑定 AppID，不能作为正式上传包。':profile.name!=='release'?'开发／测试包仅用于检查，不能作为正式发布包。':'正式构建模式只代表本地预检通过，平台与真机验收仍需完成。',
 '官方流程：https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/',
 '',
].join('\n'),'utf8');
const {convertWechatToTap}=require(path.join(extension,'dist/converter-ts.js'));
(async()=>{
 await convertWechatToTap({source,target,gameVersion:release.version,useSubpackage:false});
 require('./render-policy.cjs').check(project,path.join(target,'game'));
 fs.writeFileSync(path.join(target,'identity.json'),JSON.stringify({
  identity:audit?'unbound-local-audit':'provided-app-id',appId:appId||null,
  buildMode,
  buildProfile:profile,releaseNotes,
  platformValidated:false,uploadPerformed:false,converterVersion,
  login:{mode:guestTest?'guest':'platform',provider:'taptap-minigame',localSaveOnly:true,
   clientFlow:guestTest?'guest test -> existing local save only':'tap.login -> platform-ready; foreground tap.checkSession -> tap.login if invalid',
   customAuthService:false,identityExchange:false,accountScopedLocalSave:false,
   platformValidated:false},
 },null,2)+'\n');
 console.log(audit?'LOCAL AUDIT ONLY: no TapTap AppID, upload, or device validation.':testPackage?'UPLOAD-TEST PACKAGE: real AppID bound; integration blockers remain in the report.':'Local conversion complete; platform validation and upload have not been performed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
