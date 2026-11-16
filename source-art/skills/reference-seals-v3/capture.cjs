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
    const page=await browser.newPage({viewport:{width:1280,height:624},deviceScaleFactor:1});
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
      const materials={};
      for(const family of ['WAR','BOW','FIR','THU']){
        const image=new Image();image.src='/review/'+family+'.png';await image.decode();
        const texture=new cc.Texture2D();texture.image=new cc.ImageAsset(image);
        const material=new cc.Material();material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:cc.gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},blendState:{targets:[{blend:true,blendSrc:cc.gfx.BlendFactor.SRC_ALPHA,blendDst:cc.gfx.BlendFactor.ONE_MINUS_SRC_ALPHA,blendSrcAlpha:cc.gfx.BlendFactor.ONE,blendDstAlpha:cc.gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}});
        material.setProperty('mainTexture',texture);materials[family]=material;
      }
      const seal=new cc.Node('SuppliedReferenceGroundSeal');seal.layer=app.effects.root.layer;app.effects.root.addChild(seal);
      const renderer=seal.addComponent(cc.MeshRenderer);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
      let family='FIR',start=0,duration=1.45,mesh;
      const original=app.effects.update.bind(app.effects);
      app.effects.update=game=>{
        original(game);
        const age=game.state.time-start;
        const fadeIn=Math.min(1,Math.max(0,age/.30));
        const fadeOut=age<duration?1:Math.pow(Math.max(0,1-(age-duration)/.24),1.4);
        const pulse=.92+.08*Math.sin(Math.max(0,age-.3)*Math.PI*3);
        const alpha=fadeIn*fadeOut*pulse;
        seal.active=alpha>.001;
        materials[family].setProperty('mainColor',new cc.Vec4(1.04,1.04,1.04,alpha));
      };
      window.configureReferenceSeal=(info,id)=>{
        family=id.slice(0,3);
        const def=COMBAT_SKILLS[id];def.windupSeconds=duration;def.releaseCommitSeconds=duration;
        const g=def.ranks[0].geometry,r=g.radiusMetres;
        if(!(r>0))throw Error('No circular area geometry for '+id);
        const center=info.targets[0],camera=app.camera,right=camera.node.right.clone();right.y=0;right.normalize();
        const far=camera.node.up.clone();far.y=0;far.normalize();
        const positions=[],uvs=[],normals=[],indices=[],n=20;
        const half=r/(460/512);
        for(let j=0;j<=n;j++)for(let i=0;i<=n;i++){
          const x=(i/n*2-1)*half,z=(1-j/n*2)*half;
          const point={x:center.x+right.x*x+far.x*z,z:center.z+right.z*x+far.z*z};
          positions.push(point.x,app.world.height(point)+.052,point.z);normals.push(0,1,0);uvs.push(i/n,1-j/n);
        }
        for(let j=0;j<n;j++)for(let i=0;i<n;i++){const a=j*(n+1)+i,b=a+1,c=a+n+1;indices.push(a,c,b,b,c,c+1);}
        renderer.mesh=null;mesh?.destroy();mesh=cc.utils.createMesh({positions,uvs,normals,indices});renderer.mesh=mesh;
        renderer.setSharedMaterial(materials[family],0);
        start=app.session.state.time+.30;
        seal.active=false;
        // Frame the current fire card against the actual camera after equipment pool recreation.
        for(const pool of [app.effects.fireSprites,app.effects.blades])pool.camera=camera;
        return {center,radius:r,windup:duration,texture:family+'.png'};
      };
    });
    const definitions=[
      {id:'WAR_04',family:'WAR',centre:2.65,height:3.60,targets:[[3.5,0],[4.5,.85]],seconds:3.3},
      {id:'BOW_06',family:'BOW',centre:2.65,height:3.60,targets:[[4.1,0],[4.9,.7]],seconds:3.3},
      {id:'FIR_02',family:'FIR',centre:2.75,height:4.30,targets:[[4.7,.10],[5.85,-.85],[5.3,1.35]],seconds:3.3},
      {id:'THU_05',family:'THU',centre:3.3,height:4.10,targets:[[4.9,.05],[6.4,-1.15],[5.65,1.4],[7.35,.42]],seconds:3.3},
    ];
    for(const def of definitions){
      const dir=path.join(cache,def.family);fs.mkdirSync(dir,{recursive:true});
      const info=await page.evaluate(d=>motionStudy.select(d),def);
      const seal=await page.evaluate(({info,id})=>configureReferenceSeal(info,id),{info,id:def.id});
      console.log('Loaded reference seal',def.family,seal);
      for(let i=0;i<99;i++){
        const jpg=await page.evaluate(()=>motionStudy.next(true));
        fs.writeFileSync(path.join(dir,String(i).padStart(3,'0')+'.jpg'),Buffer.from(jpg,'base64'));
      }
      const report=await page.evaluate(()=>motionStudy.report());
      if(errors.length)throw Error(errors[0]);
      if(!report.events.some(e=>e.type==='skill_release'))throw Error('Missing release '+def.id);
      fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify({info,seal,...report,errors},null,2));
      console.log('Captured reference',def.family,report.frames,report.clips);
    }
  }finally{await browser.close();}
}
run().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>server.close());
