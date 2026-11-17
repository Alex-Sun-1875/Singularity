const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const {chromium}=require(path.join(root,'src/cocos/node_modules/playwright'));
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:2,isMobile:true,hasTouch:true});
  page.on('pageerror',e=>console.error('PAGE ERROR',e.message));
  await page.goto('http://127.0.0.1:7470/?view=2d&player=3d');
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findCaptureApp=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  const deadline=Date.now()+180000;while(true){const ready=await page.evaluate(()=>{const a=findCaptureApp();return !!(a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready);});if(ready)break;if(Date.now()>deadline)throw Error('Startup timeout');await page.waitForTimeout(250);}
  const data=await page.evaluate(async()=>{
   const module=n=>System.import('chunks:///_virtual/'+n+'.ts'),a=findCaptureApp(),s=a.session.state;
   const world=await module('WorldData'),eq=await module('Equipment');
   const areas=Object.values(world.AREAS).filter(d=>/^(S0[1-4]|S1[1-9]|H\d\d|T[1-6]|U1-0[12])$/.test(d.id)).map(d=>({id:d.id,name:d.name,spawn:d.spawn,enemies:d.enemies.map(e=>({id:e.id,name:e.name,kind:e.kind,x:e.x,z:e.z,level:e.level,hunting:e.hunting})).slice(0,8)}));
   return {menu:a.menu,level:s.progression.level,player:s.player,equipment:s.equipment,combat:s.combat,areas,modules:{world:Object.keys(world),eq:Object.keys(eq)},items:Object.values(eq.EQUIPMENT).filter(i=>i.kind!=='spell'&&(!i.requiredLevel||i.requiredLevel<=20)&&(!i.chapter||i.chapter<=2)).map(i=>({id:i.id,name:i.name,slot:i.slot,quality:i.quality,requiredLevel:i.requiredLevel,maxEnhance:i.maxEnhance})),forging:s.forging,gems:s.gems};
  });
  fs.mkdirSync(path.join(root,'promotion/records'),{recursive:true});fs.writeFileSync(path.join(root,'promotion/records/inspection.json'),JSON.stringify(data,null,2));
  console.log(JSON.stringify({menu:data.menu,level:data.level,areas:data.areas.map(d=>({id:d.id,name:d.name,enemies:d.enemies.length})),equipment:data.equipment,gemState:data.gems}));
  await page.screenshot({path:path.join(root,'promotion/records/initial.png')});
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
