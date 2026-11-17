// Isolated v29 proposal: thick-front curved shockwave with a tapered wake and forward flight.
window.installUltimatePreview=function(){
 const {app,cc}=motionStudy,{Vec3,Quat,utils}=cc,pool=app.effects.warrior,native=pool.ultimateWave;
 const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{const q=clamp(x);return q*q*(3-2*q);};
 const study=window.ultimatePreview={enabled:false,phase:null,launches:new Map()};
 const actors=app.actors.player??app.actors,nativeContactPose=actors.contactPose;
 actors.contactPose=function(actor,time){if(study.enabled&&motionStudy.state.action?.skillId==='WAR_05'){this.heldPose=undefined;return;}return nativeContactPose.call(this,actor,time);};
 const skills=app.effects.skills,nativeAdd=skills.add;
 skills.add=function(e,kind,duration,keyed=false){
  if(study.enabled&&e.skillId==='WAR_05'&&e.segment===2&&kind==='meleeSweep')duration=1.05;
  return nativeAdd.call(this,e,kind,duration,keyed);
 };
 const distance=age=>.15+3.50*smooth(age/.15)+1.90*clamp((age-.15)/.85);
 const front=u=>{const s=1-u;return [s*s*s*3.10+3*s*s*u*2.62+3*s*u*u*.85+u*u*u*.06,s*s*s*.08+3*s*s*u*.70+3*s*u*u*.80];};
 function waveMesh(age){
  const index=Math.round(clamp(age/1.05)*47),key='proposal-traveling-pressure:'+index;let mesh=pool.meshes.get(key);if(mesh)return mesh;
  const sampled=index/47*1.05,head=.10+.90*smooth(sampled/.075),tail=Math.min(.65+1.90*smooth(sampled/.30),.55+distance(sampled));
  const positions=[],normals=[],uvs=[],indices=[],nx=48,nv=12;
  for(let i=0;i<=nx;i++)for(let j=0;j<=nv;j++){
   const u=i/nx,v=j/nv,p=front(u*head),narrow=1-.96*Math.pow(v,1.65);
   // A broad upright forward face contracts into a low thin wake behind it.
   // No long needle, separate knife tip, circular radius, or returning hook.
   const height=.12+(p[0]-.12)*narrow+.035*Math.sin(u*19-v*7)*v;
   const depth=p[1]-.58*v-tail*Math.pow(v,1.35)+.045*Math.sin(u*23-v*5)*v*v;
   positions.push(Math.max(.025,height),.04*Math.sin(u*15+v*5)*v,depth);normals.push(0,1,0);uvs.push(u,v);
  }
  for(let i=0;i<nx;i++)for(let j=0;j<nv;j++){const a=i*(nv+1)+j,b=a+nv+1;indices.push(a,b,a+1,b,b+1,a+1);}
  mesh=utils.createMesh({positions,normals,uvs,indices,minPos:new Vec3(0,-.10,-3.3),maxPos:new Vec3(3.2,.10,.75),boundingRadius:4.7});pool.meshes.set(key,mesh);return mesh;
 }
 function renderWave(key,launch,forward,age,alpha,heightScale=1){
  if(age<0||alpha<.02)return;
  const layer=pool.acquire(key,'pressure-flow');if(!layer)return;
  const mesh=waveMesh(age);if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;
  const dissolve=smooth((age-.48)/.57),mat=pool.flowMaterial(layer,alpha,dissolve);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
  const p=launch.clone().add(forward.clone().multiplyScalar(distance(age)));p.y=pool.ground(p.x,p.z,launch.y);
  const normal=Vec3.cross(new Vec3(),forward,Vec3.UNIT_Y).normalize();
  layer.node.setWorldPosition(p);layer.node.setWorldRotation(Quat.fromAxes(new Quat(),Vec3.UNIT_Y,normal,forward));layer.node.setWorldScale(heightScale,1,1);layer.node.active=true;layer.touched=true;layer.phase='traveling-saber-wave';
  return p;
 }
 pool.ultimateWave=function(key,center,angle,reach,alpha,t,stage){
  if(!study.enabled||stage<3)return native.call(this,key,center,angle,reach,alpha,t,stage);
  const age=t*1.05,power=clamp(alpha/245),forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  if(age<.62){
   const q=age/.62,travel=clamp(age/.32),growth=.82+.18*smooth(travel/.35),tip=reach*(.50+.48*smooth(travel/.62));
   const radius=reach*.61*growth,at=center.clone().add(forward.clone().multiplyScalar(tip-radius)).add(new Vec3(0,.38,0)),strength=1-.28*smooth((age-.045)/.10);
   this.crescent(key+':ultimate-cross:horizontal',at,side,Vec3.UNIT_Y,forward,radius,power*smooth(age/.035)*strength,2.85,.30,smooth((q-.38)/.62));
   const axis=this.crossingAxis(forward,side),normal=Vec3.cross(new Vec3(),forward,axis).normalize();
   this.crescent(key+':ultimate-cross:vertical',at,axis,normal,forward,radius,power*smooth((age-.020)/.045)*.96*strength,2.85,.28,smooth((q-.46)/.54),.54);
  }
  let launch=study.launches.get(key);
  if(!launch){const p=motionStudy.state.player;launch=new Vec3(p.x,this.ground(p.x,p.z,center.y-1.02),p.z);study.launches.set(key,launch);if(study.launches.size>8)study.launches.delete(study.launches.keys().next().value);}
  const waveAge=age-.018;
  const position=renderWave(key+':ultimate-downcut',launch,forward,waveAge,power*smooth(waveAge/.035));
  if(!this.reducedMotion)renderWave(key+':ultimate-downcut-tail',launch,forward,waveAge-.065,power*.16*smooth((waveAge-.065)/.035),.82);
  if(position)study.phase={age:waveAge,position:[position.x,position.y,position.z],launchFoot:[launch.x,launch.y,launch.z],distance:distance(waveAge),forward:[forward.x,0,forward.z],formation:clamp(waveAge/.075),shape:'thick curved front, narrowing rear wake, detached forward shockwave'};
 };
 for(let i=0;i<48;i++)waveMesh(i/47*1.05);
};
