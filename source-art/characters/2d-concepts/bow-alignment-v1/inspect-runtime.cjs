// Reuse the existing isolated Playwright/Cocos art inspection workflow.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const phase=process.argv[2]||'before',out=path.join(__dirname,phase);fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:7469/?view=2d&test=max&revision=bow-alignment-'+phase);
  await page.waitForFunction(()=>globalThis.System);
  await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>app()?.actors?.active.get('player')&&!app().loading,undefined,{timeout:90000});
  await page.evaluate(async()=>{globalThis.areas=(await System.import('chunks:///_virtual/WorldData.ts')).AREAS;const a=app();a.enabled=true;a.menu='qa';a.session.enter(areas.S02,areas.S02.spawn);await a.rebuild();a.enabled=false;a.menu='';a.hud.root.active=false;});
  const reports=[];
  for(const [weapon,direction,skill,holdFrames=42] of [
   ['W07','right',null],['W07','up',null],['W07','down',null],['W07','left',null],
   ['W08','right',null],['L02','left',null],['W07','right','BOW_01'],['W07','up','BOW_02'],['W07','down','BOW_03'],['W07','left','BOW_05'],['W07','right',null,60],['W07','left',null,4]]){
   await page.evaluate(({weapon,direction,skill,holdFrames})=>{
    const a=app(),g=a.session,p=g.state.player;
    g.enter(areas['S01-T1'],areas['S01-T1'].spawn);if(!g.equip(weapon))throw Error('Equip failed '+weapon);
    if(skill){for(let slot=0;slot<4;slot++)g.assignActiveSkill(slot,null);if(skill==='BOW_05'){if(!g.assignUltimate(skill))throw Error('Assign ultimate failed '+skill);}else if(!g.assignActiveSkill(0,skill))throw Error('Assign failed '+skill);}
    g.enter(areas.S02,areas.S02.spawn);g.state.enemies=[];
    a.combatFocus=null;a.aiming=null;a.heldAttack=false;a.keys.clear();a.manualCameraHeight=4.6;
    const c=a.camera.node,r=c.right,u=c.up,v=direction==='right'?[r.x,r.z]:direction==='left'?[-r.x,-r.z]:direction==='up'?[u.x,u.z]:[-u.x,-u.z];
    const angle=Math.atan2(v[0],v[1]),target={x:p.x+Math.sin(angle)*8,z:p.z+Math.cos(angle)*8};
    a.actors.update(g,0,false);a.effects.clear();a.positionCamera(1);
    const control=skill==='BOW_05'?'ultimate':'combat0';
    if(skill){if(!a.beginAim(control))throw Error('Aim failed '+skill);a.aimTarget=target;}
    globalThis.takeStep=i=>{
     const input={x:0,z:0,aim:angle,attack:!skill&&i<holdFrames};
     if(skill&&i===42)a.finishAim(control);
     a.process(g.advance(1/60,input));a.actors.update(g,1/60,false,false);a.effects.update(g);a.positionCamera(1/60);a.flatWorld?.update(a.camera,g);
     const hero=a.actors.active.get('player'),camera=a.camera,point=new cc.Vec3();camera.worldToScreen(hero.root.worldPosition,point);
     const shots=g.state.projectiles.filter(q=>q.owner==='player').map(q=>{
      const body=a.effects.bodies.find(b=>b.key===q.id);if(!body)return null;
      const screen=new cc.Vec3(),forward=cc.Vec3.transformQuat(new cc.Vec3(),new cc.Vec3(0,0,1),body.node.worldRotation);camera.worldToScreen(body.node.worldPosition,screen);
      const source=a.actors.playerPresentation();
      return {id:q.id,age:q.age,angle:q.angle,logical:{x:q.x,z:q.z},position:{...body.node.worldPosition},screen:{x:screen.x,y:screen.y},forward:{...forward},hand:source&&{...source.hand}};
     }).filter(Boolean);
     return {i,height:camera.orthoHeight,camera:{...camera.node.position},feet:{x:point.x,y:point.y},pose:hero.sampledAction,ordinal:hero.ordinal,shots};
    };
   },{weapon,direction,skill,holdFrames});
   await page.waitForTimeout(60); // Let Cocos publish the settled camera matrices.
   const frames=[];
   for(let i=0;i<360;i++){
    frames.push(await page.evaluate(i=>takeStep(i),i));
    if([15,41,44,48,53,70].includes(i)){
     await page.waitForTimeout(20);await page.screenshot({path:path.join(out,`${weapon}-${direction}-${skill||(holdFrames===42?'basic':`basic-${holdFrames}`)}-${i}.jpg`),type:'jpeg',quality:91});
    }
   }
   reports.push({weapon,direction,skill,holdFrames,frames});
   fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({fixture:'isolated full-item test profile; S02 normal commands, enemies omitted only to isolate stationary camera/shot geometry',reports,errors},null,2));
  }
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({fixture:'isolated full-item test profile; S02 normal commands, enemies omitted only to isolate stationary camera/shot geometry',reports,errors},null,2));
  console.log(JSON.stringify({phase,errors,shots:reports.map(r=>({weapon:r.weapon,direction:r.direction,skill:r.skill,heightRange:Math.max(...r.frames.map(f=>f.height))-Math.min(...r.frames.map(f=>f.height)),feetRange:Math.max(...r.frames.map(f=>f.feet.x))-Math.min(...r.frames.map(f=>f.feet.x)),shotFrames:r.frames.filter(f=>f.shots.length).length}))}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
