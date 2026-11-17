// Record the current compiled skill without material, module or texture overrides.
const fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../fire-kit-implementation-v22/capture.cjs'),'utf8');
eval(source.replace('for(const def of shots){',"for(const def of shots.filter(s=>s.id==='FIR_04')){")
 .replace('width:960,height:470','width:1280,height:626')
 .replace('info.activeSlots=await page.evaluate(()=>[...motionStudy.state.combat.activeSlots]);',`info.activeSlots=await page.evaluate(()=>[...motionStudy.state.combat.activeSlots]);
 info.jetProjection=await page.evaluate(g=>{
  const {app,state,cc}=motionStudy,camera=app.camera,a=state.player.angle,d=g.lengthMetres/10;
  const p={x:state.player.x+Math.sin(a)*d,z:state.player.z+Math.cos(a)*d},y=app.world.height(p)+.095,right=camera.node.right;
  const screen=v=>{const q=camera.worldToScreen(v);return[q.x,cc.game.canvas.height-q.y];};
  const centre=screen(new cc.Vec3(p.x,y,p.z)),left=screen(new cc.Vec3(p.x-right.x*g.widthMetres/2,y,p.z-right.z*g.widthMetres/2)),edge=screen(new cc.Vec3(p.x+right.x*g.widthMetres/2,y,p.z+right.z*g.widthMetres/2));
  return{centre,diameter:Math.hypot(edge[0]-left[0],edge[1]-left[1]),cameraUpY:camera.node.up.y};
 },info.skillGeometry);`)
 .replaceAll('fire-kit-implementation-v22','fire-jet-reference-fidelity-v23'));
