// Actual Cocos meshes/materials rendered into an isolated native RenderTexture.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const ids=JSON.parse(fs.readFileSync(path.join(__dirname,'designs.json'),'utf8')).map(r=>r.id),out=path.join(__dirname,'runtime/gallery');fs.mkdirSync(out,{recursive:true});
const selected=process.argv.includes('--ids')?process.argv[process.argv.indexOf('--ids')+1].split(','):ids;
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await b.newPage({viewport:{width:1200,height:800}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto((process.env.WEAPONS_REVIEW_URL??'http://127.0.0.1:7469/')+'?view=2d&player=3d&test=max');await page.waitForFunction(()=>globalThis.System);await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:120000});
 await page.evaluate(()=>{
  if(app().failure)throw Error(app().failure);app().enabled=false;app().hud.root.active=false;
  const scene=cc.director.getScene();globalThis.stage=new cc.Node('WeaponModelReviewStage');scene.addChild(stage);stage.setPosition(10000,0,10000);
  globalThis.spin=new cc.Node('Turntable');stage.addChild(spin);const layer=1<<20;
  globalThis.setLayer=n=>{n.layer=layer;for(const c of n.children)setLayer(c);};
  const camNode=new cc.Node('WeaponModelReviewCamera');scene.addChild(camNode);globalThis.cam=camNode.addComponent(cc.Camera);cam.projection=cc.Camera.ProjectionType.ORTHO;cam.near=.1;cam.far=20;cam.visibility=layer;cam.priority=-11;cam.clearColor=new cc.Color(0,0,0,0);cam.clearFlags=cc.Camera.ClearFlag.SOLID_COLOR;
  camNode.setPosition(10000,.15,10004);camNode.lookAt(new cc.Vec3(10000,0,10000));globalThis.texture=new cc.RenderTexture();texture.reset({width:384,height:640});cam.targetTexture=texture;
  for(const [x,y,z,power,color]of[[-2,3,3,25000,new cc.Color(255,242,222)],[2,1,-2,18000,new cc.Color(205,224,255)]]){const n=new cc.Node('StudioLight');stage.addChild(n);n.setPosition(x,y,z);const l=n.addComponent(cc.PointLight);l.color=color;l.visibility=layer;l.range=7;l.term=0;l.luminousFlux=power;}
  globalThis.prepare=id=>{
   for(const n of [...spin.children]){n.removeFromParent();n.destroy();}spin.setRotationFromEuler(0,0,0);
   const actor=app().actors.player.active.get('player'),resource='WeaponVariant:design-'+id.toLowerCase();let source;
   for(const binding of Object.values(actor.swordCarry.grips))source=source??binding.heldModels.children.find(n=>n.name===resource);
   if(!source)throw Error('No native source '+id);const model=cc.instantiate(source);spin.addChild(model);model.active=true;setLayer(model);
   const lo=new cc.Vec3(Infinity,Infinity,Infinity),hi=new cc.Vec3(-Infinity,-Infinity,-Infinity);
   for(const r of model.getComponentsInChildren(cc.MeshRenderer)){
    r.shadowCastingMode=0;r.receiveShadow=0;const morph=r.mesh?.struct.morph,k=morph?.targetNames?.indexOf('Draw')??-1;if(k>=0)for(let i=0;i<morph.subMeshMorphs.length;i++)if(morph.subMeshMorphs[i])r.setWeight(0,i,k);
    const points=r.mesh?.readAttribute(0,'a_position');if(!points)continue;
    for(let i=0;i<points.length;i+=3){const v=cc.Vec3.transformMat4(new cc.Vec3(),new cc.Vec3(points[i],points[i+1],points[i+2]),r.node.worldMatrix);lo.x=Math.min(lo.x,v.x);lo.y=Math.min(lo.y,v.y);lo.z=Math.min(lo.z,v.z);hi.x=Math.max(hi.x,v.x);hi.y=Math.max(hi.y,v.y);hi.z=Math.max(hi.z,v.z);}
   }
   const center=cc.Vec3.add(new cc.Vec3(),lo,hi).multiplyScalar(.5).subtract(stage.worldPosition);model.setPosition(model.position.clone().subtract(center));
   cam.orthoHeight=Math.max(hi.y-lo.y,(hi.x-lo.x)*640/384)*.58;
   return {id,bounds:{min:{...lo},max:{...hi}},height:cam.orthoHeight,renderers:model.getComponentsInChildren(cc.MeshRenderer).length};
  };
  globalThis.saveTexture=async()=>{
   const raw=texture.readPixels(),source=new OffscreenCanvas(texture.width,texture.height);source.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(raw.buffer,raw.byteOffset,raw.byteLength),texture.width,texture.height),0,0);
   const flipped=new OffscreenCanvas(texture.width,texture.height),c=flipped.getContext('2d');c.translate(0,texture.height);c.scale(1,-1);c.drawImage(source,0,0);const bytes=new Uint8Array(await(await flipped.convertToBlob({type:'image/png'})).arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=16384)binary+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(binary);
  };
 });
 const records=[];
 for(const id of selected){
  const info=await page.evaluate(id=>prepare(id),id);await page.waitForTimeout(50);
  for(let i=0;i<12;i++){const degrees=i*30;await page.evaluate(d=>spin.setRotationFromEuler(0,d,0),degrees);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));const data=await page.evaluate(()=>saveTexture());const file=`${id}-${degrees}.png`;fs.writeFileSync(path.join(out,file),Buffer.from(data,'base64'));records.push({...info,degrees,file});}
  console.log('Rendered native model '+id);
 }
 if(process.argv.includes('--merge')){const previous=JSON.parse(fs.readFileSync(path.join(out,'frames.json'),'utf8'));records.push(...previous.records.filter(x=>!selected.includes(x.id)));}
 fs.writeFileSync(path.join(out,'frames.json'),JSON.stringify({records,errors},null,2));if(errors.length)throw Error(errors.join('\n'));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
