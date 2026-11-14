// Focused post-build asset audit, reusing the installed Playwright runtime.
// No model calls, browser uploads, generated tests or additional dependencies.
const {chromium}=require('../../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const root=path.resolve(__dirname,'../../../../..');
const actor=path.join(root,'src/cocos/assets/resources/flat2d/characters/raphael');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:720}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:7469/?view=2d&revision=qwen21-consistency-v2');
  await page.waitForFunction(()=>globalThis.System);
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.__auditApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>{const a=__auditApp();return a?.actors&&!a.loading&&!a.failure;},undefined,{timeout:60000});
  const source=JSON.parse(fs.readFileSync(path.join(actor,'manifest.json'),'utf8'));
  const live=await page.evaluate(()=>{
   const a=__auditApp(),asset=a.actors.active.get('player').asset;
   return {manifest:asset.manifest,textureURLs:[...asset.textures].map(([name,tex])=>[name,tex.image?.nativeUrl])};
  });
  // Cocos may reorder JSON object keys while serializing the asset. Arrays and
  // values must match; object property insertion order is not asset content.
  const manifestMatches=isDeepStrictEqual(live.manifest,source);
  const keys=['explore_idle_W01','explore_walk_W01','explore_run_W01'];
  const names=[...new Set(keys.flatMap(k=>source.actions[k].frameImages??[source.actions[k].image]))];
  const textures=[];
  for(const name of names){
   const url=live.textureURLs.find(([key])=>key===name.replace(/\.png$/,''))?.[1];
   if(!url)throw new Error('Missing live texture URL: '+name);
   const response=await context.request.get(new URL(url,page.url()).href);
   const bytes=await response.body(),expected=digest(fs.readFileSync(path.join(actor,name)));
   textures.push({name,url,sourceSHA256:expected,runtimeSHA256:digest(bytes),matches:expected===digest(bytes)});
  }
  const report={manifestMatches,textures,errors,revision:live.manifest.localQwenInstall};
  fs.writeFileSync(path.join(__dirname,'runtime-assets-report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({manifestMatches,texturesMatch:textures.every(t=>t.matches),errors,revision:report.revision},null,2));
  if(!manifestMatches||textures.some(t=>!t.matches)||errors.length)process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
