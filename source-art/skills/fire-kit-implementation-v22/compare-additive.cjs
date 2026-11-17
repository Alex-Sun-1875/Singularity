// Material-only native study. This does not replace shipped modules or assets.
const source=require('node:fs').readFileSync(require('node:path').join(__dirname,'capture.cjs'),'utf8');
const study=source.replace('for(const def of shots){',"for(const original of shots.filter(s=>s.id==='FIR_04')){ const def={...original,seconds:1.5};")
 .replace("probe?'probe':'final'","probe?'probe':'additive-study'")
 .replace('const result=await page.evaluate(save=>{',`if(frame===24)await page.evaluate(async()=>{
  const cc=await System.import('cc'),ground=motionStudy.app.effects.fireGround;
  for(const item of ground.surfaces){if(item.kind!=='jets')continue;
   const texture=item.material.getProperty('mainTexture'),previous=item.material,material=new cc.Material();
   material.initialize({effectName:'builtin-unlit',technique:2,defines:{USE_TEXTURE:true,USE_VERTEX_COLOR:true},states:{rasterizerState:{cullMode:cc.gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
   material.setProperty('mainTexture',texture);material.setProperty('colorScale',new cc.Vec3(1,.65,.8));
   item.material=material;item.renderer.setSharedMaterial(material,0);previous.destroy();
  }
 });
 const result=await page.evaluate(save=>{`)
 .replace('const lifecycle=await page.evaluate(async()=>{','return; const lifecycle=await page.evaluate(async()=>{');
eval(study);
