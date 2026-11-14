// Exercise the actual equip callback and cloned native inventory models.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const ids=JSON.parse(fs.readFileSync(path.join(__dirname,'designs.json'),'utf8')).map(r=>r.id);
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await b.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max');await page.waitForFunction(()=>globalThis.System);await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:120000});
 await page.evaluate(ids=>{const a=app();if(a.failure)throw Error(a.failure);a.enabled=false;a.menu='';a.session.cancelInput();for(let i=0;i<155;i++){a.session.advance(1/30,{x:0,z:0});a.actors.update(a.session,1/30,false);}for(const id of ids)a.session.state.inventory[id]=1;a.menu='inventory';a.modalKey='';a.renderModal();},ids);
 const records=[];
 for(const id of ids){
  await page.evaluate(id=>app().hud.actions.click('equip:'+id),id);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const r=await page.evaluate(()=>{const a=app(),scene=cc.director.getScene(),stage=scene.getChildByName('CharacterPreviewStage'),model=stage?.children[0],visible=new Set();
   for(const renderer of model.getComponentsInChildren(cc.MeshRenderer)){if(!renderer.node.activeInHierarchy)continue;let n=renderer.node;while(n&&!n.name.startsWith('WeaponVariant:'))n=n.parent;if(n)visible.add(n.name);}
   const find=(n,name)=>n.name===name?n:n.children.map(c=>find(c,name)).find(Boolean);
   return {id:a.session.state.equipment.weapon,stages:scene.children.filter(n=>n.name==='CharacterPreviewStage').length,variants:[...visible],quiver:!!find(model,'CarriedQuiver')?.activeInHierarchy,skins:model.getComponentsInChildren(cc.SkinnedMeshRenderer).length,carry:a.actors.inspect()[0].weaponCarry,pose:a.actors.inspect()[0].state};
  });
  assert.equal(r.id,id);assert.equal(r.stages,1);assert.deepEqual(r.variants,['WeaponVariant:design-'+id.toLowerCase()]);assert.equal(r.skins,13);assert.equal(r.carry,'stowed');if(['W11','W12','W13','W14','DR2-03','DU1-04'].includes(id))assert.equal(r.pose,'idle');records.push(r);
 }
 // The existing authored staff idle must also be used in a ready preview.
 await page.evaluate(()=>{const a=app();a.hud.actions.click('close');a.session.equip('W12');for(let i=0;i<27;i++){a.session.advance(1/30,{x:0,z:0,attack:i===0});a.actors.update(a.session,1/30,false);}a.hud.actions.click('inventory');});await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 const staff=await page.evaluate(()=>{const stage=cc.director.getScene().getChildByName('CharacterPreviewStage'),animation=stage.getComponentsInChildren(cc.SkeletalAnimation)[0],clip=animation.clips.find(c=>c?.name.split('|').pop()==='idle_staff');return {clip:clip?.name,playing:!!clip&&animation.getState(clip.name).isPlaying,carry:app().actors.inspect()[0].weaponCarry};});
 assert.ok(staff.clip&&staff.playing);assert.equal(staff.carry,'ready');await page.screenshot({path:path.join(__dirname,'runtime/inventory-staff.jpg'),type:'jpeg',quality:94});
 await page.evaluate(()=>app().hud.actions.click('close'));await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));const remaining=await page.evaluate(()=>cc.director.getScene().children.filter(n=>n.name==='CharacterPreviewStage').length);assert.equal(remaining,0);assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(__dirname,'runtime/inventory-review.json'),JSON.stringify({records,staff,remaining,errors},null,2));console.log(JSON.stringify({weapons:records.length,staff,remaining,errors}));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
