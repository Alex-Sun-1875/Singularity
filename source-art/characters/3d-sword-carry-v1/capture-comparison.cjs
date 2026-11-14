// Export the actual inventory RenderTexture at a straight orthographic angle.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max&revision=carry-final');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});await page.waitForFunction(()=>app()?.actors&&!app().loading,undefined,{timeout:90000});
 const out=path.join(__dirname,'runtime/comparison');fs.mkdirSync(out,{recursive:true});const rows=[];
 for(const id of ['W01','W02','L01']){
  await page.evaluate(id=>{const a=app();a.enabled=false;a.menu='';a.session.cancelInput();for(let i=0;i<150;i++){a.session.advance(1/30,{x:0,z:0,aim:0});a.actors.update(a.session,1/30,false);}a.session.state.inventory[id]=1;if(!a.session.equip(id))throw Error('equip '+id);a.actors.update(a.session,1/30,false);a.menu='inventory';a.modalKey='';a.renderModal();},id);
  await page.waitForTimeout(80);
  for(const [name,yaw]of [['back',180],['side',90],['front',0]]){
   await page.evaluate(yaw=>{const scene=cc.director.getScene(),stage=scene.getChildByName('CharacterPreviewStage'),model=stage.children[0],cam=scene.getChildByName('CharacterPreviewCamera').getComponent(cc.Camera);model.setRotationFromEuler(0,yaw,0);cam.node.setPosition(stage.position.x,1.03,stage.position.z+5);cam.node.lookAt(new cc.Vec3(stage.position.x,1.03,stage.position.z));for(const anim of model.getComponentsInChildren(cc.SkeletalAnimation)){const clip=anim.clips.find(x=>x?.name.split('|').pop()==='idle'),state=clip&&anim.getState(clip.name);if(state){state.time=1/clip.sample;state.sample();state.time=0;state.sample();state.speed=0;}}},yaw);
   await page.waitForTimeout(110);
   const result=await page.evaluate(()=>{const scene=cc.director.getScene();const find=n=>n.name==='CharacterModel'?n:n.children.map(find).find(Boolean);const texture=find(scene).getComponent(cc.Sprite).spriteFrame.texture,pixels=texture.readPixels();let binary='';for(let i=0;i<pixels.length;i+=16384)binary+=String.fromCharCode(...pixels.subarray(i,i+16384));return {width:texture.width,height:texture.height,data:btoa(binary)};});
   const file=`${id}-${name}.rgba`;fs.writeFileSync(path.join(out,file),Buffer.from(result.data,'base64'));rows.push({id,name,file,width:result.width,height:result.height});
  }
 }
 fs.writeFileSync(path.join(out,'frames.json'),JSON.stringify({rows,errors},null,2));if(errors.length)throw Error(errors.join('\n'));console.log('Saved nine real inventory model views');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
