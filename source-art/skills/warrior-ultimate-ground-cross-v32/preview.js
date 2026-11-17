// Isolated v32: ground the final cross remnants as well as the traveling crescent.
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
 const reference=window.crescentReferenceProfile;
 if(!reference?.outer||!reference?.inner)throw Error('Horizontal crescent profile missing');
 function groundCrossAxes(side,forward){
  // Preserve the projected 120-degree crossing by rotating within XZ.
  // Both planes must face world Y; lowering the old tilted plane buries half of it.
  const right=app.camera.node.right,up=app.camera.node.up;
  const phi=Math.atan2(Vec3.dot(side,up),Vec3.dot(side,right))-Math.PI/3;
  const a=up.x*Math.cos(phi)-right.x*Math.sin(phi),b=up.z*Math.cos(phi)-right.z*Math.sin(phi);
  const across=new Vec3(b,0,-a).normalize(),along=Vec3.cross(new Vec3(),across,Vec3.UNIT_Y).normalize();
  if(Vec3.dot(along,forward)<0){across.multiplyScalar(-1);along.multiplyScalar(-1);}
  return {across,along};
 }
 const groundedCrossMeshes=new Map();
 function groundCross(key,at,across,along,radius,alpha,span,width,dissolve,acrossScale=1){
  pool.crescent(key,at,across,Vec3.UNIT_Y,along,radius,alpha,span,width,dissolve,acrossScale);
  const layer=pool.layers.find(l=>l.key===key&&l.touched&&l.node.active);if(!layer||alpha<.02)return;
  const stamp=key+':'+[at.x,at.y,at.z,radius,across.x,across.z].map(v=>v.toFixed(5)).join(':');
  let mesh=groundedCrossMeshes.get(stamp);
  if(!mesh){
   // Reuse the native crescent topology/UVs. Drape only its height over terrain,
   // keeping the wave a low ground sweep even on the ordinary map's slope.
   const base=pool.spinMesh(span,width),p=Array.from(base.readAttribute(0,'a_position'));
   const normals=Array.from(base.readAttribute(0,'a_normal')),uvs=Array.from(base.readAttribute(0,'a_texCoord'));
   const colors=Array.from(base.readAttribute(0,'a_color')),indices=[];
   const anchorGround=at.y-.10,world=new Vec3(),min=new Vec3(Infinity,Infinity,Infinity),max=new Vec3(-Infinity,-Infinity,-Infinity);
   for(let i=0;i<p.length;i+=3){
    world.set(p[i],p[i+1],p[i+2]);Vec3.transformMat4(world,world,layer.node.worldMatrix);
    p[i+1]+=(pool.ground(world.x,world.z,anchorGround)-anchorGround)/radius;
    min.x=Math.min(min.x,p[i]);min.y=Math.min(min.y,p[i+1]);min.z=Math.min(min.z,p[i+2]);
    max.x=Math.max(max.x,p[i]);max.y=Math.max(max.y,p[i+1]);max.z=Math.max(max.z,p[i+2]);
   }
   for(let i=0;i<64;i++)for(let j=0;j<12;j++){const a=i*13+j,b=a+13;indices.push(a,b,a+1,b,b+1,a+1);}
   min.y-=.02;max.y+=.02;
   mesh=utils.createMesh({positions:p,normals,uvs,colors,indices,minPos:min,maxPos:max,boundingRadius:2});
   groundedCrossMeshes.set(stamp,mesh);
  }
  layer.renderer.mesh=mesh;
 }
 const cubic=(points,t)=>{const s=1-t;return [0,1].map(i=>s*s*s*points[0][i]+3*s*s*t*points[1][i]+3*s*t*t*points[2][i]+t*t*t*points[3][i]);};
 function contour(u,back=false){
  const p=cubic(back?reference.inner:reference.outer,u);
  if(back)for(const notch of reference.innerScallops)p[1]+=notch.depth*Math.exp(-Math.pow((u-notch.u)/notch.width,2))*Math.sin(Math.PI*u);
  return p;
 }
 function waveMesh(age){
  const index=Math.round(clamp(age/1.05)*47),key='proposal-horizontal-crescent:'+index;let mesh=pool.meshes.get(key);if(mesh)return mesh;
  const sampled=index/47*1.05,head=.10+.90*smooth(sampled/.075),tail=Math.min(.65+1.90*smooth(sampled/.30),.55+distance(sampled));
  const positions=[],normals=[],uvs=[],indices=[],nx=48,nv=12;
  for(let i=0;i<=nx;i++)for(let j=0;j<=nv;j++){
   const u=i/nx,v=j/nv,p=contour(u),rawBack=contour(u,true),tipTaper=smooth(u/reference.tipTaper.start)*smooth((1-u)/reference.tipTaper.end);
   const back=[p[0]+(rawBack[0]-p[0])*tipTaper,p[1]+(rawBack[1]-p[1])*tipTaper],endWeight=Math.pow(Math.max(0,Math.sin(Math.PI*u)),.75)*tipTaper;
   // Always use the complete outline: both ends stay pointed during formation.
   // Taper turbulence and the wake too, so neither terminal becomes a flat cut.
   const q=v<=.42?v/.42:smooth((v-.42)/.58)*endWeight;
   const endAcross=.12+(p[0]-.12)*.04,endDepth=p[1]-.58-tail;
   const across=((v<=.42?p[0]+(back[0]-p[0])*q:back[0]+(endAcross-back[0])*q)+.035*Math.sin(u*19-v*7)*v*endWeight)*(.30+.70*head);
   const depth=(v<=.42?p[1]+(back[1]-p[1])*q:back[1]+(endDepth-back[1])*q)+.045*Math.sin(u*23-v*5)*v*v*endWeight;
   positions.push(across,0,depth);normals.push(0,1,0);uvs.push(u,v);
  }
  for(let i=0;i<nx;i++)for(let j=0;j<nv;j++){const a=i*(nv+1)+j,b=a+nv+1;indices.push(a,b,a+1,b,b+1,a+1);}
  mesh=utils.createMesh({positions,normals,uvs,indices,minPos:new Vec3(-2.1,-.05,-4.1),maxPos:new Vec3(2.1,.05,1.1),boundingRadius:4.8});pool.meshes.set(key,mesh);return mesh;
 }
 function renderWave(key,launch,forward,age,alpha,heightScale=1){
  if(age<0||alpha<.02)return;
  const layer=pool.acquire(key,'pressure-flow');if(!layer)return;
  const mesh=waveMesh(age);if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;
  const dissolve=smooth((age-.48)/.57),mat=pool.flowMaterial(layer,alpha,dissolve);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
  const p=launch.clone().add(forward.clone().multiplyScalar(distance(age)));p.y=pool.ground(p.x,p.z,launch.y)+reference.planeLift;
  const side=Vec3.cross(new Vec3(),Vec3.UNIT_Y,forward).normalize();
  layer.node.setWorldPosition(p);layer.node.setWorldRotation(Quat.fromAxes(new Quat(),side,Vec3.UNIT_Y,forward));layer.node.setWorldScale(heightScale,1,1);layer.node.active=true;layer.touched=true;layer.phase='traveling-saber-wave';
  return p;
 }
 pool.ultimateWave=function(key,center,angle,reach,alpha,t,stage){
  if(!study.enabled||stage<3)return native.call(this,key,center,angle,reach,alpha,t,stage);
  const age=t*1.05,power=clamp(alpha/245),forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  if(age<.62){
   const q=age/.62,travel=clamp(age/.32),growth=.82+.18*smooth(travel/.35),tip=reach*(.50+.48*smooth(travel/.62));
   const radius=reach*.61*growth,at=center.clone().add(forward.clone().multiplyScalar(tip-radius)),strength=1-.28*smooth((age-.045)/.10);
   at.y=this.ground(at.x,at.z,center.y-1.02)+.10;
   groundCross(key+':ultimate-cross:horizontal',at,side,forward,radius,power*smooth(age/.035)*strength,2.85,.30,smooth((q-.38)/.62));
   const crossed=groundCrossAxes(side,forward);
   // Retain the legacy key for same-frame comparisons; this is now an XZ-plane arc.
   groundCross(key+':ultimate-cross:vertical',at,crossed.across,crossed.along,radius,power*smooth((age-.020)/.045)*.96*strength,2.85,.28,smooth((q-.46)/.54),.54);
  }
  let launch=study.launches.get(key);
  if(!launch){const p=motionStudy.state.player;launch=new Vec3(p.x,this.ground(p.x,p.z,center.y-1.02),p.z);study.launches.set(key,launch);if(study.launches.size>8)study.launches.delete(study.launches.keys().next().value);}
  const waveAge=age-.018;
  const position=renderWave(key+':ultimate-downcut',launch,forward,waveAge,power*smooth(waveAge/.035));
  if(!this.reducedMotion)renderWave(key+':ultimate-downcut-tail',launch,forward,waveAge-.065,power*.16*smooth((waveAge-.065)/.035),.82);
  if(position)study.phase={age:waveAge,position:[position.x,position.y,position.z],launchFoot:[launch.x,launch.y,launch.z],distance:distance(waveAge),forward:[forward.x,0,forward.z],formation:clamp(waveAge/.075),planeLift:reference.planeLift,shape:'horizontal irregular crescent, both ends pointed'};
 };
 for(let i=0;i<48;i++)waveMesh(i/47*1.05);
};
