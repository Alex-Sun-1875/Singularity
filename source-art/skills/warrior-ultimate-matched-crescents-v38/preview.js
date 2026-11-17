// Isolated review: every pulse shares exactly the user's traced crescent mesh.
window.installUltimatePreview=function(){
 const {app,cc}=motionStudy,{Vec3,Quat,Vec4,utils}=cc,pool=app.effects.warrior,native=pool.ultimateWave;
 const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{const q=clamp(x);return q*q*(3-2*q);};
 const study=window.ultimatePreview={enabled:false,phase:null,phases:[],waveCount:1,launches:new Map()};
 const reference=window.swooshReferenceProfile;
 const actors=app.actors.player??app.actors,nativeContactPose=actors.contactPose;
 actors.contactPose=function(actor,time){if(study.enabled&&motionStudy.state.action?.skillId==='WAR_05'){this.heldPose=undefined;return;}return nativeContactPose.call(this,actor,time);};
 const skills=app.effects.skills,nativeAdd=skills.add;
 skills.add=function(e,kind,duration,keyed=false){if(study.enabled&&e.skillId==='WAR_05'&&e.segment===2&&kind==='meleeSweep')duration=reference.visualDuration;return nativeAdd.call(this,e,kind,duration,keyed);};
 const distance=age=>.15+2.65*smooth(age/.18)+3.10*clamp((age-.18)/.84);
 const source=pool.constructor.flowEffect;
 if(!source?.shaders?.length)throw Error('Compiled native pressure effect is unavailable');
 const effect=new cc.EffectAsset();effect.name='Isolated:MatchedCrescent:v38';
 effect.shaders=JSON.parse(JSON.stringify(source.shaders));effect.techniques=JSON.parse(JSON.stringify(source.techniques));effect.combinations=JSON.parse(JSON.stringify(source.combinations??[]));
 for(let i=0;i<effect.shaders.length;i++){
  const shader=effect.shaders[i],oldName=shader.name;shader.name='isolated-matched-crescent-v38-'+i;
  for(const backend of ['glsl3','glsl1','glsl4'])if(shader[backend]){
   const s=shader[backend];if(!s.frag.includes('vec4 frag ()'))throw Error('Unexpected shader entry');
   s.frag=s.frag.replace(/vec4 frag\s*\(\s*\)\s*\{[\s\S]*?\n\}/,window.swooshFragmentSource.trim());
   s.vert=s.vert.replace('p.xz *= 1.0 - rear * flowState.y * 0.12;','p.xz *= 1.0;').replace('rear * 0.018','rear * 0.0');
  }
  let hash=2166136261;for(const ch of shader.name+shader.glsl3.vert+shader.glsl3.frag)hash=Math.imul(hash^ch.charCodeAt(0),16777619);shader.hash=hash>>>0;
  for(const t of effect.techniques)for(const pass of t.passes)if(pass.program===oldName)pass.program=shader.name;
 }
 effect.onLoaded();
 const flow=new cc.Texture2D();flow.reset({width:256,height:256,format:cc.Texture2D.PixelFormat.RGBA8888});flow.uploadData(new Uint8Array(window.swooshFlowPixels));
 flow.setWrapMode(cc.Texture2D.WrapMode.REPEAT,cc.Texture2D.WrapMode.REPEAT);flow.setFilters(cc.Texture2D.Filter.LINEAR,cc.Texture2D.Filter.LINEAR);flow.setMipFilter(cc.Texture2D.Filter.NONE);
 function material(layer,alpha,dissolve){
  let mat=layer.matchedMaterial;
  if(!mat){mat=new cc.Material();mat.name='Isolated:MatchedCrescent:v38';mat.initialize({effectAsset:effect});mat.setProperty('flowTexture',flow);mat.setProperty('mainTexture',flow);layer.matchedMaterial=mat;}
  mat.setProperty('mainColor',new Vec4(.79,.83,.86,alpha));mat.setProperty('flowState',new Vec4(pool.time,dissolve,1,0));return mat;
 }
 // One immutable template: no age, ordinal, scale, or terrain in its geometry.
 const positions=[],normals=[],uvs=[],indices=[],nx=reference.outerSamples.length-1,nv=16;
 const min=new Vec3(Infinity,Infinity,Infinity),max=new Vec3(-Infinity,-Infinity,-Infinity);
 for(let i=0;i<=nx;i++)for(let j=0;j<=nv;j++){
  const u=i/nx,v=j/nv,outer=reference.outerSamples[i],inner=reference.innerSamples[i],w=Math.sin(Math.PI*u)**1.2;
  const q=v<=.66?v/.66:1,r=v>.66?smooth((v-.66)/.34):0;
  const y=reference.planeLift+outer[0]+(inner[0]-outer[0])*q+r*w*.015*Math.sin(u*23);
  const z=outer[1]+(inner[1]-outer[1])*q-r*w*1.10;
  const x=.012*w*Math.sin(Math.PI*v)*r;
  positions.push(x,y,z);normals.push(1,0,0);uvs.push(u,v);
  min.x=Math.min(min.x,x);min.y=Math.min(min.y,y);min.z=Math.min(min.z,z);max.x=Math.max(max.x,x);max.y=Math.max(max.y,y);max.z=Math.max(max.z,z);
 }
 for(let i=0;i<nx;i++)for(let j=0;j<nv;j++){const a=i*(nv+1)+j,b=a+nv+1;indices.push(a,b,a+1,b,b+1,a+1);}
 const mesh=utils.createMesh({positions,normals,uvs,indices,minPos:min,maxPos:max,boundingRadius:8});mesh.name='AuthoredRedCrescentV38';
 function renderWave(key,launch,forward,age,alpha){
  if(age<0||age>=reference.waveLife||alpha<.02)return;
  const layer=pool.acquire(key,'pressure-flow');if(!layer)return;
  const p=launch.clone().add(forward.clone().multiplyScalar(distance(age)));
  const side=Vec3.cross(new Vec3(),Vec3.UNIT_Y,forward).normalize();
  layer.renderer.mesh=mesh;layer.renderer.setSharedMaterial(material(layer,alpha,smooth((age-.40)/.62)),0);
  layer.node.setWorldPosition(p);layer.node.setWorldRotation(Quat.fromAxes(new Quat(),side,Vec3.UNIT_Y,forward));layer.node.setWorldScale(1,1,1);layer.node.active=true;layer.touched=true;layer.phase='matched-crescent-wave';
  return p;
 }
 pool.ultimateWave=function(key,center,angle,reach,alpha,t,stage){
  if(!study.enabled||stage<3)return native.call(this,key,center,angle,reach,alpha,t,stage);
  study.waveCount=reference.rankWaveCounts[String(motionStudy.state.progression.learned.WAR_05??1)]??1;
  const age=t*reference.visualDuration-.018,power=clamp(alpha/245),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  let launch=study.launches.get(key);
  if(!launch){const p=motionStudy.state.player;launch=new Vec3(p.x,this.ground(p.x,p.z,center.y-1.02),p.z);study.launches.set(key,launch);}
  study.phases=[];
  for(let i=0;i<study.waveCount;i++){
   const waveAge=age-i*reference.pulseInterval;
   const position=renderWave(key+':ultimate-downcut:wave:'+i,launch,forward,waveAge,power*smooth(waveAge/.025));
   if(!position)continue;
   const phase={waveIndex:i,age:waveAge,position:[position.x,position.y,position.z],launchFoot:[launch.x,launch.y,launch.z],distance:distance(waveAge),forward:[forward.x,0,forward.z],formation:1,scale:1,planeLift:reference.planeLift,shape:'fixed user-traced crescent; identical shape and world height for all waves',material:'isolated-matched-crescent-v38'};
   study.phases.push(phase);study.phase=phase;
  }
 };
};
