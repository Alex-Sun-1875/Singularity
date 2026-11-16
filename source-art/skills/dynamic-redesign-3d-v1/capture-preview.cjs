#!/usr/bin/env node
'use strict';

// Deterministic screenshots of the independent design canvas. Never builds or edits the game.
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const {chromium}=require(path.resolve(__dirname,'../../../src/cocos/node_modules/playwright'));

function parseArgs(argv){
  const result={fps:20,width:1266,height:585,compare:false};
  for(let i=0;i<argv.length;i++){
    const arg=argv[i];
    if(arg==='--compare'){result.compare=true;continue;}
    if(arg==='--canvas-export'){result.canvasExport=true;continue;}
    if(arg==='--serve'){result.serve=true;continue;}
    if(arg==='--help'){result.help=true;continue;}
    if(!['--skill','--reel','--out','--fps','--duration','--width','--height','--browser','--port'].includes(arg))throw new Error('Unknown argument: '+arg);
    if(!argv[i+1]||argv[i+1].startsWith('--'))throw new Error('Missing value for '+arg);
    result[arg.slice(2)]=argv[++i];
  }
  return result;
}
function finiteNumber(value,name,min,max){const n=Number(value);if(!Number.isFinite(n)||n<min||n>max)throw new Error(`${name} must be ${min}–${max}`);return n;}
function browserPath(explicit){
  const candidates=[explicit,process.env.CHROME_PATH,chromium.executablePath(),'C:/Users/Alexa/AppData/Local/ms-playwright/chromium-1194/chrome-win/chrome.exe','C:/Program Files/Google/Chrome/Application/chrome.exe'].filter(Boolean);
  const found=candidates.find(p=>fs.existsSync(p));if(!found)throw new Error('No installed Chromium was found. This script does not install dependencies.');return found;
}
function servePreview(port){
  // Models may use repository-relative URLs. Expose only the source-art and Cocos subtrees, on loopback.
  const workspace=path.resolve(__dirname,'../../..');
  const entry='/source-art/skills/dynamic-redesign-3d-v1/preview.html';
  const types={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.glb':'model/gltf-binary','.gltf':'model/gltf+json','.bin':'application/octet-stream','.svg':'image/svg+xml','.woff2':'font/woff2','.ttf':'font/ttf'};
  const server=http.createServer(async(req,res)=>{
    try{
      const url=new URL(req.url,'http://127.0.0.1');
      let pathname=decodeURIComponent(url.pathname);if(pathname==='/')pathname=entry;
      if(!pathname.startsWith('/source-art/')&&!pathname.startsWith('/src/cocos/')){res.writeHead(404);res.end('Not found');return;}
      const file=path.resolve(workspace,'.'+pathname);
      if(!file.startsWith(workspace+path.sep)){res.writeHead(403);res.end('Forbidden');return;}
      const stat=await fs.promises.stat(file);if(!stat.isFile()){res.writeHead(404);res.end('Not found');return;}
      const body=await fs.promises.readFile(file);
      res.writeHead(200,{'Content-Type':types[path.extname(file).toLowerCase()]||'application/octet-stream','Content-Length':body.length,'Cache-Control':'no-store'});
      res.end(req.method==='HEAD'?undefined:body);
    }catch{res.writeHead(404);res.end('Not found');}
  });
  return new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',()=>resolve({server,url:`http://127.0.0.1:${server.address().port}${entry}`}));});
}
async function main(){
  const args=parseArgs(process.argv.slice(2));
  if(args.help){console.log('node capture-preview.cjs --serve [--port 7486]\nnode capture-preview.cjs --skill ID|--reel WAR|BOW|FIR|THU|ALL --out DIR [--fps 20] [--duration SEC] [--compare] [--width 1266 --height 585]');return;}
  if(args.serve){const hosted=await servePreview(Math.round(finiteNumber(args.port??7486,'port',0,65535)));console.log('3D concept preview (loopback only): '+hosted.url);return;}
  if(!args.out)throw new Error('--out is required');
  if(Boolean(args.skill)===Boolean(args.reel))throw new Error('Use exactly one of --skill or --reel');
  const fps=finiteNumber(args.fps,'fps',1,60),width=Math.round(finiteNumber(args.width,'width',320,3840)),height=Math.round(finiteNumber(args.height,'height',180,2160));
  const output=path.resolve(args.out);fs.mkdirSync(output,{recursive:true});
  const hosted=await servePreview(Math.round(finiteNumber(args.port??0,'port',0,65535)));
  let browser;
  try{
    browser=await chromium.launch({executablePath:browserPath(args.browser),headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
    const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(hosted.url,{waitUntil:'load'});
    await page.waitForFunction(()=>window.previewReady===true||window.previewError,{timeout:60000});
    const info=await page.evaluate(()=>({error:window.previewError,native3D:window.VfxPreview?.isNative3D===true,modelMetadata:window.VfxPreview?.modelMetadata,skills:window.VfxPreview?.skills.map(({id,name,family,role,duration})=>({id,name,family,role,duration}))}));
    if(info.error)throw new Error(info.error);
    if(!info.native3D)throw new Error('The preview did not confirm native 3D models. Refusing to capture a 2D fallback.');
    let skills;
    if(args.skill){skills=info.skills.filter(s=>s.id===args.skill);if(!skills.length)throw new Error('Unknown skill '+args.skill+'. Available: '+info.skills.map(s=>s.id).join(', '));}
    else{
      const family=String(args.reel).toUpperCase();
      if(!['WAR','BOW','FIR','THU','COM','ALL'].includes(family))throw new Error('Unknown reel family: '+family);
      skills=info.skills.filter(s=>family==='ALL'||String(s.family).toUpperCase()===family);
      if(!skills.length)throw new Error('No skills matched reel '+family);
    }
    // Every reel segment gets 0.25 seconds to settle after the skill; standalone clips use exact duration.
    let cursor=0;
    const timeline=skills.map(s=>{const duration=Math.max(.1,Number(s.duration)||3),item={...s,start:cursor,duration,end:cursor+duration};cursor=item.end+(args.reel?.length ? .25 : 0);return item;});
    const duration=args.duration===undefined?cursor:finiteNumber(args.duration,'duration',.05,600);
    const frameCount=Math.ceil(duration*fps);
    await page.evaluate(({width,height})=>{window.pausePreview();window.setPreviewCaptureSize(width,height);},{width,height});
    const canvas=page.locator('#preview-canvas');
    let segment=0;
    for(let frame=0;frame<frameCount;frame++){
      const time=frame/fps;
      while(segment<timeline.length-1&&time>=timeline[segment+1].start)segment++;
      const item=timeline[segment],local=Math.min(item.duration,Math.max(0,time-item.start));
      await page.evaluate(({skill,time,compare})=>window.renderAt(skill,time,compare),{skill:item.id,time:local,compare:Boolean(args.compare)});
      const filename=path.join(output,`frame-${String(frame).padStart(5,'0')}.png`);
      if(args.canvasExport){const png=await canvas.evaluate(node=>node.toDataURL('image/png').split(',')[1]);fs.writeFileSync(filename,Buffer.from(png,'base64'));}
      else await canvas.screenshot({path:filename,animations:'disabled'});
      if(frame===0||frame===frameCount-1||frame%Math.max(1,Math.floor(frameCount/5))===0)console.log(`Captured ${frame+1}/${frameCount}: ${item.id} ${local.toFixed(2)}s`);
    }
    if(errors.length)throw new Error('Browser errors: '+[...new Set(errors)].join('; '));
    const manifest={kind:'independent-native-3d-concept-animation',native3D:info.native3D,modelMetadata:info.modelMetadata,runtimeIntegrated:false,source:'preview.html + effects.js',captureMethod:args.canvasExport?'rendered-canvas-png':'canvas-element-screenshot',fps,width,height,duration,frameCount,comparison:Boolean(args.compare),selection:args.reel?{reel:String(args.reel).toUpperCase()}:{skill:args.skill},timeline,frames:'frame-%05d.png'};
    fs.writeFileSync(path.join(output,'capture.json'),JSON.stringify(manifest,null,2)+'\n');
    console.log(`Complete: ${frameCount} PNG frames in ${output}`);
  }finally{if(browser)await browser.close();await new Promise(resolve=>hosted.server.close(resolve));}
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
