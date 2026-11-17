// A disposable Cocos scene for reviewing the supplied artwork and its timing.
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const root=path.resolve(__dirname,'../../..');
const cocos=path.join(root,'src/cocos');
const build=path.join(cocos,'build/concept-2d');
const cache=path.join(root,'src/.tmp/reference-seals-v3');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const mime={'.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.html':'text/html','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{
  const url=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
  const local=url.startsWith('/review/')?path.resolve(__dirname,'assets',url.slice(8)):path.resolve(build,'.'+(url==='/'?'/index.html':url));
  if(!(local.startsWith(build+path.sep)||local.startsWith(path.join(__dirname,'assets')+path.sep))||!fs.existsSync(local)||!fs.statSync(local).isFile()){res.writeHead(404).end();return;}
  res.setHeader('Content-Type',mime[path.extname(local)]??'application/octet-stream');
  fs.createReadStream(local).pipe(res);
});

async function run(){
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
  try{
    const page=await browser.newPage({viewport:{width:960,height:470},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
    await page.goto('http://127.0.0.1:'+server.address().port+'/?view=3d&player=3d&test=max',{waitUntil:'load'});
    await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
    await page.evaluate(async()=>{
      const cc=await System.import('cc');
      window.findReviewChapter=()=>{
        function find(node){return node?.getComponent('ChapterGame')||node?.children.map(find).find(Boolean);}
        return find(cc.director.getScene());
      };
    });
    await page.waitForFunction(()=>{const app=findReviewChapter();return app?.session&&app?.actors&&!app.loading&&app.platform.auth.ready;},undefined,{timeout:180000});
    await page.addScriptTag({path:path.join(__dirname,'../cocos-motion-study-v2/review-fixture.js')});
    await page.evaluate(async()=>{
      await installMotionStudy('current');
      const cc=motionStudy.cc,app=motionStudy.app;
      const {COMBAT_SKILLS}=await System.import('chunks:///_virtual/PureSkills.ts');
      const duration=1.45;
      window.configureReferenceSeal=(info,id)=>{
        const family=id.slice(0,3);
        if(id!=='FIR_02')return {enabled:false,family,reason:'Ornate seal applies to meteor only'};
        const def=COMBAT_SKILLS[id];def.windupSeconds=duration;def.releaseCommitSeconds=duration;
        const g=def.ranks[0].geometry,r=g.radiusMetres;
        if(!(r>0))throw Error('No circular area geometry for '+id);
        const center=info.targets[0],camera=app.camera,right=camera.node.right.clone();right.y=0;right.normalize();
        const far=camera.node.up.clone();far.y=0;far.normalize();
        const half=r/(460/512);
        const projection=[[-1,1],[1,1],[1,-1],[-1,-1]].map(([u,v])=>{
          const p={x:center.x+right.x*u*half+far.x*v*half,z:center.z+right.z*u*half+far.z*v*half};
          const pixel=camera.worldToScreen(new cc.Vec3(p.x,app.world.height(p)+.052,p.z));
          return [pixel.x,cc.game.canvas.height-pixel.y];
        });
        // Frame the current fire card against the actual camera after equipment pool recreation.
        for(const pool of [app.effects.fireSprites,app.effects.blades])pool.camera=camera;
        return {enabled:true,center,radius:r,windup:duration,texture:family+'.png',projection,viewport:[cc.game.canvas.width,cc.game.canvas.height]};
      };
    });
    const definitions=[
      {id:'WAR_04',family:'WAR',centre:2.65,height:3.60,targets:[[3.5,0],[4.5,.85]],seconds:3.3},
      {id:'BOW_06',family:'BOW',centre:2.65,height:3.60,targets:[[4.1,0],[4.9,.7]],seconds:3.3},
      {id:'FIR_02',family:'FIR',centre:2.75,height:4.30,targets:[[4.7,.10],[5.85,-.85],[5.3,1.35]],seconds:3.3},
      {id:'THU_05',family:'THU',centre:3.3,height:4.10,targets:[[4.9,.05],[6.4,-1.15],[5.65,1.4],[7.35,.42]],seconds:3.3},
    ];
    for(const def of (process.argv.includes('--probe')?definitions.slice(0,1):definitions)){
      const dir=path.join(cache,def.family);fs.mkdirSync(dir,{recursive:true});
      const info=await page.evaluate(d=>motionStudy.select(d),def);
      const seal=await page.evaluate(({info,id})=>configureReferenceSeal(info,id),{info,id:def.id});
      console.log('Loaded reference seal',def.family,seal);
      fs.writeFileSync(path.join(dir,'projection.json'),JSON.stringify(seal,null,2));
      if(process.argv.includes('--projection-only')){
        continue;
      }
      for(let i=0;i<99;i++){
        const jpg=await page.evaluate(()=>motionStudy.next(true));
        fs.writeFileSync(path.join(dir,String(i).padStart(3,'0')+'.jpg'),Buffer.from(jpg,'base64'));
        if(i===38&&process.argv.includes('--probe'))break;
      }
      const report=await page.evaluate(()=>motionStudy.report());
      if(errors.length)throw Error(errors[0]);
      if(!process.argv.includes('--probe')&&!report.events.some(e=>e.type==='skill_release'))throw Error('Missing release '+def.id);
      fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify({info,seal,...report,errors},null,2));
      console.log('Captured reference',def.family,report.frames,report.clips);
    }
  }finally{await browser.close();}
}
run().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>server.close());
