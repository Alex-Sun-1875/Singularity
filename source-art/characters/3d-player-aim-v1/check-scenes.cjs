const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&revision=scene-check');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:90000});assert.equal(await page.evaluate(()=>app().failure),'');
 const result=await page.evaluate(async()=>{
  const areas=(await System.import('chunks:///_virtual/WorldData.ts')).AREAS,{GameSession}=await System.import('chunks:///_virtual/GameSession.ts'),a=app();a.enabled=false;a.menu='qa';const g=a.session;g.equip('W07');const rows=[];
  for(const id of ['S01-T1','S01','S02','H01','U1-04']){
   a.enabled=true;g.enter(areas[id],areas[id].spawn);await a.rebuild();a.enabled=false;a.menu='qa';a.hud.root.active=false;
   const hero=a.actors.player.active.get('player'),frames=[];
   for(const magnitude of [1,.48])for(let heading=0;heading<4;heading++)for(let i=0;i<14;i++){
    const angle=heading*Math.PI/2;g.advance(1/30,{x:Math.sin(angle)*magnitude,z:Math.cos(angle)*magnitude});a.actors.update(g,1/30,true,false,magnitude);a.effects.update(g);a.positionCamera(1);a.flatWorld.update(a.camera,g);
    if(hero.speed>.08&&!g.state.action&&g.state.player.hurtTime<=.33)frames.push({magnitude,state:hero.state,speed:hero.speed});
    if(i%4===0)await new Promise(r=>setTimeout(r,16));
   }
   const textureRefs=[...a.actors.player.nativeMaterials.ownedTextures].map(t=>({uuid:t.uuid,refCount:t.refCount}));
   const snapshot=g.snapshot(),restored=GameSession.restore(snapshot,a.query);rows.push({id,run:frames.filter(f=>f.magnitude===1&&f.state==='run').length,walk:frames.filter(f=>f.magnitude<1&&f.state==='walk').length,wrongGait:frames.filter(f=>f.state!==(f.magnitude===1?'run':'walk')),savedLevel:restored.state.progression.level,savedWeapon:restored.state.equipment.weapon,skinRenderers:hero.model.getComponentsInChildren(cc.SkinnedMeshRenderer).length,textureRefs});
  }
  return {temporaryMax:a.temporaryMax,rows};
 });
 assert.equal(result.temporaryMax,false);assert.ok(result.rows.every(r=>r.run>0&&r.walk>0&&!r.wrongGait.length&&r.savedLevel===40&&r.savedWeapon==='W07'&&r.skinRenderers===13));assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(__dirname,'runtime/scenes.json'),JSON.stringify({...result,errors},null,2));console.log(JSON.stringify({scenes:result.rows.map(r=>({id:r.id,run:r.run,walk:r.walk,wrong:r.wrongGait.length,savedLevel:r.savedLevel,weapon:r.savedWeapon})),errors}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
