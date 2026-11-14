// Isolated local MediaPipe measurement through the existing browser runtime.
// All JS/WASM/model/image bytes are served from disk by Playwright routes.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../../../..');
const models='F:/Models/PoseCalibration';
const actor=path.join(root,'src/cocos/assets/resources/flat2d/characters/raphael');
const inventory=JSON.parse(fs.readFileSync(path.join(__dirname,'inventory.json'),'utf8'));
const destination=path.join(__dirname,'pose-landmarks.json');
const records=fs.existsSync(destination)?JSON.parse(fs.readFileSync(destination,'utf8')).frames:[];
const completed=new Set(records.map(r=>r.image+':'+r.index));
const pilot=process.argv.includes('--pilot');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.origin!=='http://127.0.0.1:8191')return route.abort();
   if(url.pathname==='/')return route.fulfill({contentType:'text/html',body:'<!doctype html><title>Local body measurement</title>'});
   const relative=decodeURIComponent(url.pathname).slice(1),file=path.resolve(models,relative);
   if(!file.startsWith(path.resolve(models)+path.sep)||!fs.existsSync(file))return route.abort();
   const type=file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')||file.endsWith('.mjs')?'text/javascript':'application/octet-stream';
   await route.fulfill({contentType:type,body:fs.readFileSync(file)});
  });
  const page=await context.newPage();
  await page.goto('http://127.0.0.1:8191/');
  await page.evaluate(async()=>{
   const mp=await import('/package/vision_bundle.mjs');
   const files=await mp.FilesetResolver.forVisionTasks('/package/wasm');
   globalThis.pose=await mp.PoseLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:'/pose_landmarker_full.task',delegate:'CPU'},runningMode:'IMAGE',numPoses:1,minPoseDetectionConfidence:.25,minPosePresenceConfidence:.25,outputSegmentationMasks:false});
   globalThis.sheets=new Map();
  });
  let sampled=0;
  for(const record of inventory.frames){
   if(completed.has(record.image+':'+record.index))continue;
   if(pilot&&sampled>=104)break;
   const payload=await page.evaluate(async({r,base64})=>{
    if(!sheets.has(r.image)){const im=new Image();im.src='data:image/png;base64,'+base64;await im.decode();sheets.set(r.image,im);}
    const [x,y,w,h]=r.rect,pad=32,c=document.createElement('canvas');c.width=w+pad*2;c.height=h+pad*2;
    const cx=c.getContext('2d',{willReadFrequently:true});cx.fillStyle='#d0d0d0';cx.fillRect(0,0,c.width,c.height);cx.drawImage(sheets.get(r.image),x,y,w,h,pad,pad,w,h);
    let result=pose.detect(c),retried=false;
    if(!result.landmarks.length){cx.fillStyle='#ffffff';cx.fillRect(0,0,c.width,c.height);cx.drawImage(sheets.get(r.image),x,y,w,h,pad,pad,w,h);result=pose.detect(c);retried=true;}
    const landmarks=result.landmarks[0]?.map(p=>({x:p.x*c.width-pad,y:p.y*c.height-pad,z:p.z*c.width,visibility:p.visibility,presence:p.presence}))??[];
    return{landmarks,worldLandmarks:result.worldLandmarks[0]??[],retried};
   },{r:record,base64:await page.evaluate(name=>sheets.has(name),record.image)?null:fs.readFileSync(path.join(actor,record.image)).toString('base64')});
   records.push({image:record.image,index:record.index,...payload});sampled++;
   if(sampled%20===0){fs.writeFileSync(destination,JSON.stringify({model:'MediaPipe Pose Landmarker full v1',localOnly:true,frames:records}));console.log(JSON.stringify({measured:records.length,detected:records.filter(r=>r.landmarks.length===33).length}));}
  }
  fs.writeFileSync(destination,JSON.stringify({model:'MediaPipe Pose Landmarker full v1',localOnly:true,frames:records}));
  console.log(JSON.stringify({measured:records.length,detected:records.filter(r=>r.landmarks.length===33).length,pilot}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
