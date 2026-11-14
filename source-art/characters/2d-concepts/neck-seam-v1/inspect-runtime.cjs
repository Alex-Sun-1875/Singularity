// Reuses the existing native Cocos/Playwright frame and texture inspection.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../../..'),actor=path.join(root,'src/cocos/assets/resources/flat2d/characters/raphael'),out=path.join(__dirname,'runtime');fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const context=await browser.newContext({viewport:{width:1280,height:900}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&test=max&revision=neck-seam-v1');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors?.active.get('player')&&!app().loading||app()?.failure,undefined,{timeout:90000});assert.equal(await page.evaluate(()=>app().failure),'');
 const prepared=JSON.parse(fs.readFileSync(path.join(__dirname,'prepare.json'),'utf8'));
 const live=await page.evaluate(()=>{const a=app(),p=a.actors.active.get('player');a.enabled=false;a.menu='qa';a.hud.root.active=false;a.manualCameraHeight=1.65;a.positionCamera(1);return {manifest:p.asset.manifest,urls:[...p.asset.textures].map(([name,t])=>[name,t.image.nativeUrl])};});
 assert.equal(sha(fs.readFileSync(path.join(actor,'manifest.json'))),prepared.manifestSHA256);assert.deepEqual(live.manifest,JSON.parse(fs.readFileSync(path.join(actor,'manifest.json'),'utf8')));
 const textures=[];
 for(const [name,expected] of Object.entries(prepared.files)){
  const entry=live.urls.find(([key])=>key===name.replace(/\.png$/,''));assert.ok(entry,'runtime loaded '+name);
  const response=await context.request.get(new URL(entry[1],page.url()).href);assert.ok(response.ok());const actual=sha(await response.body());assert.equal(actual,expected);textures.push({name,sha256:actual});
 }
 await page.waitForTimeout(70);const samples=[];
 for(let i=0;i<prepared.changes.length;i++){
  const change=prepared.changes[i],ref=change.refs.find(v=>/_(W\d+|L\d+)$/.test(v.action))||change.refs[0];
  const result=await page.evaluate(({ref,expected})=>{const a=app(),p=a.actors.active.get('player'),m=p.asset.manifest,clip=m.actions[ref.action],r=a.camera.node.right;p.angle=Math.atan2(r.x,r.z);p.renderedWeaponId=ref.action.match(/_(W\d+|L\d+)$/)?.[1]??'W01';
   const begin=clip.phaseStarts?.[ref.phase]??ref.phase/clip.frames,end=clip.phaseStarts?.[ref.phase+1]??(ref.phase+1)/clip.frames,state=ref.action.includes('idle')?'idle':ref.action.includes('bow')?'attack_bow':ref.action.includes('staff')?'attack_staff':'attack_sword';
   a.actors.show(p,state,0,begin+(end-begin)*.025,true,ref.action);const image=(clip.frameImages?.[p.ordinal]??clip.image).replace(/\.png$/,''),point=new cc.Vec3();a.camera.worldToScreen(p.root.worldPosition.clone().add(cc.Vec3.multiplyScalar(new cc.Vec3(),a.camera.node.up,1.45)),point);
   return {action:ref.action,phase:p.ordinal,frame:p.frame,direction:m.directions[p.direction],textureMatches:p.material.getProperty('mainTexture')===p.asset.textures.get(image),clip:{x:Math.max(0,Math.min(1000,point.x-140)),y:Math.max(0,Math.min(580,900-point.y-150)),width:280,height:320}};
  },{ref,expected:change.index});
  assert.equal(result.phase,ref.phase);assert.equal(result.frame,change.index);assert.equal(result.direction,'right');assert.ok(result.textureMatches);
  await page.waitForTimeout(20);const file=`${i}-${ref.action}-${ref.phase}.jpg`;await page.screenshot({path:path.join(out,file),type:'jpeg',quality:94,clip:result.clip});samples.push({...result,file});
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({manifestSHA256:prepared.manifestSHA256,textures,samples,errors},null,2));console.log(`PASS ${textures.length} compiled texture hashes, ${samples.length} actual collar poses, no runtime errors.`);
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
