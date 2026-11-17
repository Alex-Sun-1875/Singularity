// Narrow follow-up to the v1 real Cocos QA: complete square portrait bounds only.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),{chromium,devices}=require(path.join(cocos,'node_modules/playwright'));
const proof=JSON.parse(fs.readFileSync(path.join(__dirname,'snapshot.json'),'utf8')),build=path.resolve(root,proof.servedSnapshot),out=path.join(__dirname,'native-qa');
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
if(sha(path.join(build,proof.mainFile))!==proof.compiledSha256||sha(proof.copyManifest)!==proof.copyManifestSha256)throw Error('Snapshot proof mismatch');
if(fs.existsSync(path.join(out,'report.json')))throw Error('Completed portrait evidence already exists; preserve it');fs.mkdirSync(out,{recursive:true});
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.wasm':'application/wasm','.css':'text/css'};
const server=http.createServer((req,res)=>{const url=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(url==='/'?'/index.html':url));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.setHeader('Cache-Control','no-store');fs.createReadStream(file).pipe(res);});
async function capture(browser,label,options){const context=await browser.newContext(options),page=await context.newPage(),errors=[],consoleErrors=[],result={label,viewport:options.viewport,dpr:options.deviceScaleFactor,errors,consoleErrors};
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
 try{
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d',{waitUntil:'load'});await page.waitForFunction(()=>!!globalThis.System,undefined,{timeout:60000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findForgeApp=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  await page.waitForFunction(()=>{const a=findForgeApp();return a?.session&&a.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:120000});
  result.initial=await page.evaluate(()=>{const a=findForgeApp(),s=a.session.state;return{level:s.progression.level,inventory:JSON.stringify(s.inventory),equipment:JSON.stringify(s.equipment)};});
  await page.evaluate(()=>findForgeApp().click('forge-item:W11'));
  await page.waitForFunction(()=>{const a=findForgeApp();function find(n){return n.name==='ForgeRoom'||n.children.some(find);}return a.menu==='forge-item:W11'&&!a.preparingPage&&find(a.hud.modal);},undefined,{timeout:90000});
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  result.layout=await page.evaluate(async()=>{
   const cc=await System.import('cc'),a=findForgeApp(),all=[];function visit(n){all.push(n);n.children.forEach(visit);}visit(a.hud.modal);
   const node=name=>all.find(n=>n.name===name),room=node('ForgeRoom'),host=node('ForgeWeaponArt'),portrait=host.children.find(n=>n.name.startsWith('EquipmentIconFrame:')),anvil=room.children.find(n=>n.name==='Skin:ui/quiet-bronze/rpg-forge-anvil-v7'),labels=room.children.map(n=>n.getComponent(cc.Label)).filter(Boolean),title=labels.find(l=>/\+\d/.test(l.string)),quality=labels.find(l=>l.string.includes(' · ')),s=innerHeight/a.hud.height;
   // Transform only each node's own rect. getBoundingBoxToWorld also merges
   // descendants and therefore cannot prove a Mask viewport's clip bounds.
   const rect=n=>{const t=n.getComponent(cc.UITransform),p=t.convertToWorldSpaceAR(new cc.Vec3(-t.width*t.anchorPoint.x,-t.height*t.anchorPoint.y)),q=t.convertToWorldSpaceAR(new cc.Vec3(t.width*(1-t.anchorPoint.x),t.height*(1-t.anchorPoint.y)));return{x:(p.x+a.hud.width/2)*s,y:innerHeight-(q.y+a.hud.height/2)*s,width:(q.x-p.x)*s,height:(q.y-p.y)*s};};
   const r=rect(room),p=rect(portrait),h=rect(host),v=rect(anvil),t=rect(title.node),q=rect(quality.node),unit=r.width/310;
   return{menu:a.menu,appEnabled:a.enabled,gamePaused:cc.game.isPaused(),resources:a.preparationResources.inspect(),room:r,portrait:p,host:h,anvil:v,title:{string:title.string,rect:t},quality:{string:quality.string,rect:q},portraitDesignWidth:p.width/unit,portraitDesignHeight:p.height/unit,roomDesignHeight:r.height/unit,topGapLogical:p.y-r.y,bottomGapToAnvilLogical:v.y-p.y-p.height,topGapDesign:(p.y-r.y)/unit,bottomGapToAnvilDesign:(v.y-p.y-p.height)/unit,leftGapLogical:p.x-r.x,rightGapLogical:r.x+r.width-p.x-p.width,titleGapLogical:t.x-p.x-p.width,qualityGapLogical:q.x-p.x-p.width,titleQualityGapLogical:q.y-t.y-t.height,level:a.session.state.progression.level,inventory:JSON.stringify(a.session.state.inventory),equipment:JSON.stringify(a.session.state.equipment)};
  });
  await page.screenshot({path:path.join(out,label+'-complete-square.png')});const l=result.layout;
  if(l.topGapLogical<-.05||l.bottomGapToAnvilLogical<-.05||l.leftGapLogical<-.05||l.rightGapLogical<-.05||l.titleGapLogical<0||l.qualityGapLogical<0)throw Error('Portrait clipped or intruding into stone/name/quality');
  if(label==='desktop'&&Math.abs(l.portraitDesignWidth-136)>.05)throw Error('Desktop136 size changed');
  if(label==='iphone14'&&(l.topGapDesign<7.95||l.bottomGapToAnvilDesign<7.95))throw Error('Phone lacks its planned8-unit top/stone gaps');
  if(l.inventory!==result.initial.inventory||l.equipment!==result.initial.equipment||l.level!==result.initial.level||!l.appEnabled||l.gamePaused)throw Error('Unexpected gameplay/input state mutation');
  result.pass=errors.length===0&&consoleErrors.length===0;return result;
 }catch(error){result.failure=String(error);await page.screenshot({path:path.join(out,label+'-failure.png')}).catch(()=>{});return result;}
 finally{fs.writeFileSync(path.join(out,label+'.json'),JSON.stringify(result,null,2));await context.close();}}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']}),results=[];try{
 results.push(await capture(browser,'desktop',{viewport:{width:1280,height:636},deviceScaleFactor:1}));console.log('desktop',results.at(-1).pass,results.at(-1).failure??'');
 results.push(await capture(browser,'iphone14',{...devices['iPhone 14 landscape'],viewport:{width:844,height:390},deviceScaleFactor:3}));console.log('iphone14',results.at(-1).pass,results.at(-1).failure??'');
 const report={compiledSha256:proof.compiledSha256,servedSnapshot:build,copyManifestSha256:proof.copyManifestSha256,previousColdLoadEvidence:'source-art/ui/forge-cold-load-fix-v1/verification.json',scope:'Only final portrait completeness/name-quality bounds; cold-load and tab workflows not repeated. Real initial test W11, no inventory grants, level changes, training, clock pause or camera changes.',snapshotMainStillMatches:sha(path.join(build,proof.mainFile))===proof.compiledSha256,results};fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));if(results.some(r=>!r.pass))process.exitCode=1;
 }finally{await browser.close();server.close();}})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
