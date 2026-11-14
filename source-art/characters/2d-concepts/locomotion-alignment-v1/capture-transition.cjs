// Focused manual-visual capture using the project's existing Playwright runtime.
// This is not a test suite. Uses normal GameSession movement/attack commands and
// real FlatActors routing; no source PNG editing or pose substitution.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const label=process.argv[2]||'after',out=path.join(__dirname,label);
fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
let context;try{
 context=await browser.newContext({viewport:{width:1280,height:720},recordVideo:{dir:path.join(out,'video'),size:{width:1280,height:720}}});
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&locomotion='+label);
 await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.__captureApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>{const a=__captureApp();return a?.actors&&!a.loading&&!a.failure;},undefined,{timeout:60000});
 await page.mouse.click(640,530);
 await page.evaluate(()=>{const a=__captureApp();a.menu='qa';a.enabled=false;a.hud.root.active=false;a.camera.orthoHeight=2.0;});
 const reports=[];
 for(const held of [false,true])for(const direction of ['right','down','left','up']){
  await page.evaluate(({held,direction})=>{const a=__captureApp(),g=a.session,p=g.state.player;
   const r=a.camera.node.right,u=a.camera.node.up;
   const v=direction==='right'?[r.x,r.z]:direction==='left'?[-r.x,-r.z]:direction==='up'?[u.x,u.z]:[-u.x,-u.z];
   const n=Math.hypot(...v);globalThis.__captureVector=[v[0]/n,v[1]/n];globalThis.__captureAim=Math.atan2(v[0],v[1]);
   // Clear normal presentation grace, then trigger held presentation through
   // an ordinary attack. The short following sequence fits its2s grace.
   for(let i=0;i<120;i++){g.advance(1/30,{x:0,z:0,aim:__captureAim});a.actors.update(g,1/30,false,false);}
   if(held)for(let i=0;i<26;i++){g.advance(1/30,{x:0,z:0,aim:__captureAim,attack:i===0});a.actors.update(g,1/30,false,false);}
   a.positionCamera(1);a.flatWorld?.update(a.camera);
  },{held,direction});
  for(const [state,amount,frames]of [['idle',0,6],['walk',.48,24],['run',1,18],['stop',0,6]]){
   const samples=[];
   for(let i=0;i<frames;i++){
    const sample=await page.evaluate(({amount})=>{const a=__captureApp(),g=a.session,v=__captureVector;g.advance(1/30,{x:v[0]*amount,z:v[1]*amount,aim:__captureAim});a.actors.update(g,1/30,amount>0,false,amount||1);a.effects.update(g);a.world.presentation?.update(g);a.positionCamera(1);a.flatWorld?.update(a.camera);
     const h=a.actors.active.get('player'),pose=h.asset.manifest.actions[h.sampledAction],image=(pose.frameImages?.[h.ordinal]??pose.image).replace(/\.png$/,'');
     return{sampledAction:h.sampledAction,state:h.state,direction:h.direction,ordinal:h.ordinal,textureMatchesPose:h.material.getProperty('mainTexture')===h.asset.textures.get(image),spriteScale:[h.sprite.scale.x,h.sprite.scale.y],image};
    },{amount});samples.push(sample);await page.waitForTimeout(33);
   }
   await page.screenshot({path:path.join(out,`${held?'held':'explore'}-${direction}-${state}.png`)});
   reports.push({held,direction,state,samples});
  }
 }
 const video=page.video();await context.close();context=null;await video.saveAs(path.join(out,'idle-walk-run.webm'));
 fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify({label,orthoHeight:2,viewport:[1280,720],reports,errors},null,2));
 console.log(JSON.stringify({label,errors,actions:[...new Set(reports.flatMap(r=>r.samples.map(s=>s.sampledAction)))],materialMismatches:reports.flatMap(r=>r.samples).filter(s=>!s.textureMatchesPose).length,video:path.join(out,'idle-walk-run.webm')},null,2));
}finally{await context?.close();await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
