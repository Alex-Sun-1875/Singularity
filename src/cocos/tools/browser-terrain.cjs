const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await browser.newPage({viewport:{width:1280,height:720}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://localhost:7456/');await page.waitForFunction(()=>globalThis.__chapter?.inspect().ready, undefined, {timeout:60000});await page.mouse.click(640,540);await page.evaluate(()=>{__chapter.app.menu='qa';__chapter.app.hud.clearModal();});
 const reports=[];
 for(const id of ['S01','S02','S11','U1-02']){
  const r=await page.evaluate(async id=>{const app=__chapter.app,area=__chapter.areas[id],oldMeshes=[...app.world.generatedMeshes],oldMaterials=[...app.world.materials.values()];app.session.enter(area,area.spawn);await app.rebuild();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
   const terrain=app.world.terrain,deck=terrain.bridges[0],ramp=terrain.ramps.find(r=>r.id==='u102-dry-ramp'),start=deck?{x:deck.x-deck.width/2-.6,z:deck.z}:ramp.start,end=deck?{x:deck.x+deck.width/2+.6,z:deck.z}:ramp.end;
   // An isolated terrain fixture verifies physical movement. This setup is not
   // used as chapter playthrough evidence; that has a separate command pilot.
   app.session.enter(area,start);await app.rebuild();const path=app.world.navigation.path(start,end),heights=[];
   if(!path.length)throw Error('No actual terrain route '+id);
   for(const target of path.slice(1))for(let n=0;n<1200;n++){const p=app.session.state.player,dx=target.x-p.x,dz=target.z-p.z,d=Math.hypot(dx,dz);if(d<.16)break;app.session.advance(Math.min(1/30,d/3.6),{x:dx/d,z:dz/d});heights.push({terrain:app.world.height(p),controller:app.capsule.node.position.y});if(n===1199)throw Error('Capsule stuck '+id+' '+JSON.stringify({p,target}));}
   app.actors.update(app.session,.033,false);app.effects.update(app.session);app.positionCamera(1);app.camera.orthoHeight=id==='U1-02'?12:10;app.hud.root.active=false;const p=app.session.state.player;
   const road=app.world.root.children.find(n=>n.name==='Road'),mesh=road?.getComponent('cc.MeshRenderer')?.mesh;let roadFacing=1;if(mesh){const v=mesh.readAttribute(0,'a_position'),indices=mesh.readIndices(0),a=indices[0]*3,b=indices[1]*3,c=indices[2]*3;roadFacing=(v[b+2]-v[a+2])*(v[c]-v[a])-(v[b]-v[a])*(v[c+2]-v[a+2]);}
   return {id,start,end,actual:{x:p.x,z:p.z},heightRange:[Math.min(...heights.map(h=>h.terrain)),Math.max(...heights.map(h=>h.terrain))],maxFootError:Math.max(...heights.map(h=>Math.abs(h.terrain-h.controller))),oldMeshesAlive:oldMeshes.filter(m=>cc.isValid(m,true)).length,oldMaterialsAlive:oldMaterials.filter(m=>cc.isValid(m,true)).length,roadFacing};
  },id);
  assert.ok(Math.hypot(r.actual.x-r.end.x,r.actual.z-r.end.z)<.25,`${id} walk reaches other side`);assert.ok(r.maxFootError<.2,`${id} capsule follows the actual terrain ${r.maxFootError}`);assert.equal(r.oldMeshesAlive,0);assert.equal(r.oldMaterialsAlive,0);assert.ok(r.roadFacing>0,'roads must face upward to be visible');if(id==='U1-02')assert.ok(r.heightRange[1]-r.heightRange[0]>4.8);reports.push(r);await page.screenshot({path:`test-results/terrain-${id}.png`});
 }
 assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('test-results/browser-terrain.json',JSON.stringify({reports,errors},null,2));console.log(reports);
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
