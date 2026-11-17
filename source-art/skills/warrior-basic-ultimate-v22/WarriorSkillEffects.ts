import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,Color,EffectAsset,Material,Mesh,MeshRenderer,Node,Vec3,Vec4,Quat,Texture2D,gfx,utils} from 'cc';
import {WHIRLWIND,whirlwindPose,whirlwindFinisher} from '../common/WhirlwindSkill';
type Layer={key:string;node:Node;renderer:MeshRenderer;touched:boolean;phase:string;family?:string;flowMaterial?:Material};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const t=clamp(x);return t*t*(3-2*t);};
/** Silver pressure waves driven only by real gameplay clocks and contacts. */
export class WarriorSkillEffects {
 private static texture:Texture2D|null=null;
 private static whiteTexture:Texture2D|null=null;
 private static flowTexture:Texture2D|null=null;
 private static flowEffect:EffectAsset|null=null;
 private static pending:Promise<void>|null=null;
 private static revision=0;
 static preload(){
  if(this.pending)return this.pending;
  const revision=this.revision,retained:(Texture2D|EffectAsset)[]=[];
  const load=(name:string,repeat=false)=>new Promise<Texture2D>((resolve,reject)=>resources.load('vfx/production/'+name+'/texture',Texture2D,(error,texture)=>{if(error){reject(error);return;}if(revision!==this.revision){reject(new Error('Warrior wave load cancelled'));return;}texture.setWrapMode(repeat?Texture2D.WrapMode.REPEAT:Texture2D.WrapMode.CLAMP_TO_EDGE,repeat?Texture2D.WrapMode.REPEAT:Texture2D.WrapMode.CLAMP_TO_EDGE);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);texture.addRef();retained.push(texture);resolve(texture);}));
  const effect=new Promise<EffectAsset>((resolve,reject)=>resources.load('vfx/production/warrior-pressure-wave-v2',EffectAsset,(error,asset)=>{if(error){reject(error);return;}if(revision!==this.revision){reject(new Error('Warrior wave effect load cancelled'));return;}asset.addRef();retained.push(asset);resolve(asset);}));
  return this.pending=Promise.all([load('warrior-silver-wave-v1'),load('warrior-white-v1'),load('warrior-flow-v1',true),effect]).then(([wave,white,flow,shader])=>{this.texture=wave;this.whiteTexture=white;this.flowTexture=flow;this.flowEffect=shader;}).catch(error=>{for(const asset of retained)asset.decRef();if(revision===this.revision)this.pending=null;throw error;});
 }
 static disposeAssets(){this.revision++;this.texture?.decRef();this.whiteTexture?.decRef();this.flowTexture?.decRef();this.flowEffect?.decRef();this.texture=null;this.whiteTexture=null;this.flowTexture=null;this.flowEffect=null;this.pending=null;}
 private root:Node;private layers:Layer[]=[];private meshes=new Map<string,Mesh>();private materials=new Map<string,Material>();private rotation=new Quat();private droppedLayers=0;private time=0;
 reducedMotion=false;
 constructor(parent:Node,private readonly camera:Camera|undefined,private readonly terrain:(x:number,z:number)=>number){this.root=new Node('WarriorSkillEffects');this.root.layer=parent.layer;parent.addChild(this.root);}
 private ground(x:number,z:number,fallback:number){return this.terrain(x,z)??fallback;}
 begin(time=0){this.time=time;for(const layer of this.layers)layer.touched=false;}
 prepare(){for(const [span,width]of [[2.30,.23],[2.05,.19],[2.50,.27],[2.20,.23],[2.78,.25],[2.10,.24],[2.35,.30],[2.70,.27],[2.55,.27],[2.85,.30],[2.85,.28]])this.spinMesh(span,width);for(let i=0;i<12;i++){const layer=this.acquire('warm-flow:'+i,'pressure-flow');if(layer)this.flowMaterial(layer,0,0);}for(let i=0;i<6;i++)this.acquire('warm-contact:'+i,'solid-quad');this.clear();}
 private acquire(key:string,family:string){
  let layer=this.layers.find(item=>item.key===key);if(layer){layer.node.active=true;return layer;}
  layer=this.layers.find(item=>!item.touched&&!item.node.active&&item.family===family);
  if(!layer){if(this.layers.length>=64){this.droppedLayers++;return undefined;}const node=new Node('WarriorSkillElement');node.layer=this.root.layer;this.root.addChild(node);const renderer=node.addComponent(MeshRenderer);renderer.shadowCastingMode=0;renderer.receiveShadow=0;layer={key,node,renderer,touched:false,phase:'',family};this.layers.push(layer);}layer.key=key;
  // Cocos 3.8 only rebuilds an existing renderer model while active. Wake the
  // pooled node before assigning its mesh/material, including its first use.
  layer.node.active=true;return layer;
 }
 private solid(colour:number[],alpha:number,vertex=false){
  const level=Math.max(1,Math.round(clamp(alpha)*32)),key='solid:'+colour.join(',')+':'+level+':'+vertex;
  const cached=this.materials.get(key);if(cached)return cached;
  const mat=new Material();mat.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true,USE_VERTEX_COLOR:vertex},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}});
  mat.setProperty('mainTexture',WarriorSkillEffects.whiteTexture!);mat.setProperty('tilingOffset',new Vec4(1,1,0,0));
  mat.setProperty('mainColor',new Color(colour[0]*255,colour[1]*255,colour[2]*255,level/32*255));this.materials.set(key,mat);return mat;
 }
 private unitQuad(){
  const key='solid-quad',cached=this.meshes.get(key);if(cached)return cached;
  const mesh=utils.createMesh({positions:[-.5,-.5,0,.5,-.5,0,.5,.5,0,-.5,.5,0],normals:[0,0,1,0,0,1,0,0,1,0,0,1],uvs:[0,0,1,0,1,1,0,1],indices:[0,1,2,0,2,3],minPos:new Vec3(-.5,-.5,0),maxPos:new Vec3(.5,.5,0),boundingRadius:.72});this.meshes.set(key,mesh);return mesh;
 }
 private element(key:string,mesh:Mesh,phase:string,position:Vec3,xAxis:Vec3,yAxis:Vec3,width:number,height:number,colour:number[],alpha:number,vertex=false){
  if(alpha<.015||width<.002||height<.002)return;const layer=this.acquire(key,'solid-quad');if(!layer)return;
  if(layer.phase!==phase){layer.renderer.mesh=mesh;layer.phase=phase;}
  const material=this.solid(colour,alpha,vertex);if(layer.renderer.sharedMaterial!==material)layer.renderer.setSharedMaterial(material,0);
  const normal=Vec3.cross(new Vec3(),xAxis,yAxis).normalize();Quat.fromAxes(this.rotation,xAxis,yAxis,normal);layer.node.setWorldPosition(position);layer.node.setWorldRotation(this.rotation);layer.node.setWorldScale(width,height,1);layer.touched=true;layer.node.active=true;
 }
 private bar(key:string,a:Vec3,b:Vec3,width:number,colour:number[],alpha:number,ground=false){
  const axis=b.clone().subtract(a),length=axis.length();if(length<.004)return;axis.multiplyScalar(1/length);
  let side=ground?Vec3.cross(new Vec3(),Vec3.UNIT_Y,axis):this.camera?.node.up.clone()??Vec3.UNIT_Y.clone();
  side.subtract(axis.clone().multiplyScalar(Vec3.dot(side,axis))).normalize();if(side.length()<.1)side=new Vec3(1,0,0);
  this.element(key,this.unitQuad(),'solid-quad',a.clone().add(b).multiplyScalar(.5),axis,side,length,width,colour,alpha);
 }
 private crossingAxis(forward:Vec3,side:Vec3){
  if(!this.camera)return side.clone().multiplyScalar(Math.cos(Math.PI/3)).add(new Vec3(0,Math.sin(Math.PI/3),0)).normalize();
  const right=this.camera.node.right,up=this.camera.node.up;
  const sx=Vec3.dot(side,right),sy=Vec3.dot(side,up),phi=Math.atan2(sy,sx)-Math.PI/3;
  const a=sy*Math.cos(phi)-sx*Math.sin(phi),b=up.y*Math.cos(phi)-right.y*Math.sin(phi);
  const roll=Math.atan2(-a,b),axis=side.clone().multiplyScalar(Math.cos(roll)).add(new Vec3(0,Math.sin(roll),0));
  if(Vec3.dot(axis,right)*Math.cos(phi)+Vec3.dot(axis,up)*Math.sin(phi)<0)axis.multiplyScalar(-1);
  return axis.normalize();
 }
 private spinMesh(span:number,width:number){
  const stamp='spin-mesh:'+span+':'+width,old=this.meshes.get(stamp);if(old)return old;
  const positions:number[]=[],normals:number[]=[],colors:number[]=[],uvs:number[]=[],indices:number[]=[],nx=64,nz=12;
  for(let i=0;i<=nx;i++)for(let j=0;j<=nz;j++){
   const s=i/nx,v=j/nz,theta=(s-.5)*span,taper=Math.pow(Math.max(0,Math.sin(Math.PI*s)),.67),radius=1-width*1.65*taper*v;
   positions.push(Math.sin(theta)*radius,.024*Math.sin(Math.PI*v)*taper,Math.cos(theta)*radius-width*.20*v*v);normals.push(0,1,0);uvs.push(s,v);colors.push(1,1,1,1);
  }
  for(let i=0;i<nx;i++)for(let j=0;j<nz;j++){const a=i*(nz+1)+j,b=a+nz+1;indices.push(a,b,a+1,b,b+1,a+1);}
  const mesh=utils.createMesh({positions,normals,uvs,colors,indices,minPos:new Vec3(-1,-.08,-1),maxPos:new Vec3(1,.22,1),boundingRadius:1.5});this.meshes.set(stamp,mesh);return mesh;
 }
 private flowMaterial(layer:Layer,alpha:number,dissolve:number){
  let mat=layer.flowMaterial;if(!mat){mat=new Material();mat.name='ProjectProcedural:WarriorPressure';mat.initialize({effectAsset:WarriorSkillEffects.flowEffect!});mat.setProperty('mainTexture',WarriorSkillEffects.texture!);mat.setProperty('flowTexture',WarriorSkillEffects.flowTexture!);layer.flowMaterial=mat;}
  mat.setProperty('mainColor',new Vec4(.80,.82,.84,alpha));mat.setProperty('flowState',new Vec4(this.time,dissolve,this.reducedMotion?.28:1,0));return mat;
 }
 private spinArc(key:string,position:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,tilt=0,dissolve=0){
  if(alpha<.02)return;const layer=this.acquire(key,'pressure-flow');if(!layer)return;
  const mesh=this.spinMesh(span,width);if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;layer.phase='pressure-flow';
  const mat=this.flowMaterial(layer,alpha,dissolve);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
  layer.node.setWorldPosition(position);layer.node.setWorldRotation(Quat.fromEuler(new Quat(),tilt,angle*180/Math.PI,0));layer.node.setWorldScale(radius,radius,radius);layer.node.active=true;layer.touched=true;
 }
 private crescent(key:string,position:Vec3,across:Vec3,normal:Vec3,forward:Vec3,radius:number,alpha:number,span=2.78,width=.25,dissolve=0,acrossScale=1){
  if(alpha<.02)return;const layer=this.acquire(key,'pressure-flow');if(!layer)return;
  const mesh=this.spinMesh(span,width);if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;layer.phase='crescent-wave';
  const mat=this.flowMaterial(layer,alpha,dissolve);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
  Quat.fromAxes(this.rotation,across,normal,forward);layer.node.setWorldPosition(position);layer.node.setWorldRotation(this.rotation);layer.node.setWorldScale(radius*acrossScale,radius,radius);layer.touched=true;
 }
 private basicWave(key:string,center:Vec3,angle:number,reach:number,alpha:number,t:number,stage:number){
  const travel=clamp(t*(stage===3?.42:.34)/.17),yaw=angle+(stage===2?-.18:.18)*(1-smooth(travel));
  const forward=new Vec3(Math.sin(yaw),0,Math.cos(yaw)),side=new Vec3(Math.cos(yaw),0,-Math.sin(yaw)),roll=[.25,-.10,1.22][stage-1];
  const across=side.multiplyScalar(Math.cos(roll)).add(new Vec3(0,Math.sin(roll),0)),normal=Vec3.cross(new Vec3(),forward,across).normalize();
  const radius=reach*(stage===3?.62:.58)*(.88+.12*smooth(travel/.40)),tip=reach*(.50+.38*smooth(travel/.60));
  const at=center.clone().add(forward.clone().multiplyScalar(tip-radius)),power=clamp(alpha/245)*smooth(t/.07)*(stage===3?1:.88);
  this.crescent(key+':'+['basic-sweep','basic-return','basic-downcut'][stage-1],at,across,normal,forward,radius,power,stage===3?2.35:2.10,stage===3?.30:.24,smooth((t-.22)/.78));
 }
 private ultimateWave(key:string,center:Vec3,angle:number,reach:number,alpha:number,t:number,stage:number){
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle)),power=clamp(alpha/245),duration=stage===3?.62:.52;
  const travel=clamp(t*duration/(stage===3?.32:.27)),growth=.82+.18*smooth(travel/.35),tip=reach*(.50+.48*smooth(travel/.62));
  if(stage<3){
   const roll=stage===1?.08:1.28,across=side.multiplyScalar(Math.cos(roll)).add(new Vec3(0,Math.sin(roll),0)),normal=Vec3.cross(new Vec3(),forward,across).normalize();
   const radius=reach*(stage===1?.61:.54)*growth,at=center.clone().add(forward.clone().multiplyScalar(tip-radius)).add(new Vec3(0,stage===1?-.04:.33,0));
   this.crescent(key+':'+(stage===1?'ultimate-sweep':'ultimate-rise'),at,across,normal,forward,radius,power*smooth(t/.07)*.94,stage===1?2.70:2.55,.27,smooth((t-.32)/.68),stage===1?1:.56);return;
  }
  const radius=reach*.61*growth,at=center.clone().add(forward.clone().multiplyScalar(tip-radius)).add(new Vec3(0,.38,0));
  this.crescent(key+':ultimate-cross:horizontal',at,side,Vec3.UNIT_Y,forward,radius,power*smooth(t/.08),2.85,.30,smooth((t-.38)/.62));
  const across=this.crossingAxis(forward,side),normal=Vec3.cross(new Vec3(),forward,across).normalize();
  this.crescent(key+':ultimate-cross:vertical',at,across,normal,forward,radius,power*smooth((t-.10)/.14)*.96,2.85,.28,smooth((t-.46)/.54),.54);
 }
 private focusedMoon(key:string,center:Vec3,angle:number,reach:number,alpha:number,t:number,stage:number){
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  const roll=stage===1?.60:stage===2?-.60:1.18,across=side.multiplyScalar(Math.cos(roll)).add(new Vec3(0,Math.sin(roll),0)),normal=Vec3.cross(new Vec3(),forward,across).normalize();
  const travel=clamp(t*.50/.28),growth=smooth(travel/.32),radius=reach*(.48+.08*growth),tip=reach*(.58+.42*smooth(travel/.64));
  const at=center.clone().add(forward.clone().multiplyScalar(tip-radius)),opening=smooth(t/.06);
  this.crescent(key+':focused-cut',at,across,normal,forward,radius,clamp(alpha/245)*opening,2.78,.25,smooth((t-.36)/.64));
 }
 draw(key:string,center:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,up?:Vec3){
  if(key.startsWith('echo:')||!WarriorSkillEffects.texture||radius<=0)return;
  const stage=Number(key.match(/:stage:(\d)/)?.[1]??1),t=clamp(progress);
  if(key.startsWith('basic:')){this.basicWave(key,center,angle,radius,alpha,t,stage);return;}
  if(key.includes('WAR_05')){
   this.ultimateWave(key,center,angle,radius,alpha,t,stage);
   return;
  }
  this.focusedMoon(key,center,angle,radius,alpha,t,stage);
 }
 cross(key:string,impact:Vec3,angle:number,length:number,t:number,alpha:number){
  const radius=length*.50,forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle)),power=clamp(alpha/245);
  const at=impact.clone().subtract(forward.clone().multiplyScalar(radius*.16)),opening=smooth(t/.12);
  this.crescent(key+':horizontal',at,side,Vec3.UNIT_Y,forward,radius,power*opening,2.78,.25,smooth((t-.34)/.66));
  const across=this.crossingAxis(forward,side),normal=Vec3.cross(new Vec3(),forward,across).normalize();
  this.crescent(key+':vertical',at.clone().add(new Vec3(0,.08,0)),across,normal,forward,radius*.98,power*smooth((t-.14)/.15),2.78,.25,smooth((t-.46)/.54));
 }
 rush(key:string,start:Vec3,current:Vec3,angle:number,t:number){
  const delta=current.clone().subtract(start),length=delta.length();if(length<.12)return;
  const forward=delta.normalize(),side=new Vec3(Math.cos(angle),0,-Math.sin(angle)),fade=.78*(1-smooth((t-.72)/.28));
  for(let i=0;i<3;i++){const offset=side.clone().multiplyScalar((i-1)*.24),a=start.clone().add(offset),b=current.clone().add(offset).subtract(forward.clone().multiplyScalar(.16));a.y=this.ground(a.x,a.z,start.y-.18)+.055;b.y=this.ground(b.x,b.z,current.y-.18)+.055;this.bar(key+':rush-streak:'+i,a,b,i===1?.065:.038,[.80,.86,.91],fade,true);}
 }
 pulse(key:string,center:Vec3,angle:number,t:number,alpha:number,iron=false,hand?:Vec3){
  if(!this.camera)return;
  const fade=Math.pow(1-clamp(t),1.4),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  if(iron){
   const at=center.clone().add(forward.clone().multiplyScalar(.43)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
   for(let i=0;i<3;i++){const a=at.clone().add(side.clone().multiplyScalar((i-1)*.20)).add(new Vec3(0,.20-.12*i,0)),b=a.clone().add(side.clone().multiplyScalar(.22)).add(new Vec3(0,-.26,0));this.bar(key+':armour-pulse:'+i,a,b,.04,[.92,.96,1],clamp(alpha/245)*fade);}
  }else{
   const position=(hand??center).clone().add(forward.clone().multiplyScalar(.22));
   const axis=forward.clone().multiplyScalar(.7).add(new Vec3(0,.72,0)).normalize(),widthAxis=this.camera.node.right.clone();
   widthAxis.subtract(axis.clone().multiplyScalar(Vec3.dot(axis,widthAxis))).normalize();
   this.bar(key+':blade-glint',position.clone().subtract(axis.clone().multiplyScalar(.27)),position.clone().add(axis.clone().multiplyScalar(.38)),.045,[.96,.98,1],clamp(alpha/245)*fade);
   this.bar(key+':blade-glint-tip',position.clone().subtract(widthAxis.clone().multiplyScalar(.12)),position.clone().add(widthAxis.clone().multiplyScalar(.12)),.025,[.96,.98,1],clamp(alpha/245)*fade);
  }
 }
 end(){for(const layer of this.layers)if(!layer.touched)layer.node.active=false;}

 whirlwind(key:string,center:Vec3,angle:number,elapsed:number,releaseAt:number,radius:number){
  const pose=whirlwindPose(elapsed,releaseAt),age=pose.age,q=clamp(age/WHIRLWIND.spinSeconds),scale=radius/WHIRLWIND.baseRadius,opening=smooth(age/.075);
  if(age>=0&&age<WHIRLWIND.spinSeconds+.12){
   const phase=angle+pose.turn,front=center.clone().add(new Vec3(0,.94,0));
   this.spinArc(key+':primary',front,phase,radius,2.30,.23,opening,5*Math.sin(q*Math.PI*2),smooth((age-.78)/.30));
   if(age>.08)this.spinArc(key+':secondary',center.clone().add(new Vec3(0,.65,0)),phase+Math.PI,1.96*scale,2.05,.19,smooth((age-.08)/.09)*.90,-7,smooth((age-.80)/.28));
   if(!this.reducedMotion)this.spinArc(key+':trailing',front.clone().add(new Vec3(0,.015,0)),phase-.28,2.11*scale,2.50,.27,opening*.13,0,smooth((age-.72)/.30));
  }
  if(age>=WHIRLWIND.spinSeconds&&age<WHIRLWIND.spinSeconds+WHIRLWIND.finishSeconds){
   const wave=whirlwindFinisher(age,radius),p=wave.progress,forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),at=center.clone().add(forward.multiplyScalar(wave.offset)).add(new Vec3(0,.86-.10*p,0));
   this.spinArc(key+':finisher',at,angle,wave.radius,2.20,.23,smooth(p/.07),6,smooth((p-.25)/.75));
  }
 }
 contact(key:string,center:Vec3,angle:number,strength:number,t:number){
  if(!this.camera)return;const fade=Math.pow(1-clamp(t),1.6),right=this.camera.node.right,up=this.camera.node.up;
  for(let i=0;i<(this.reducedMotion?2:3);i++){const a=angle+i*1.04,axis=right.clone().multiplyScalar(Math.cos(a)).add(up.clone().multiplyScalar(Math.sin(a))),length=.18+Math.min(2,strength)*.045;this.bar('contact:'+key+':'+i,center.clone().subtract(axis.clone().multiplyScalar(length)),center.clone().add(axis.multiplyScalar(length)),.028,[.96,.98,1],fade);}
 }
 clear(){for(const layer of this.layers){layer.node.active=false;layer.touched=false;}this.droppedLayers=0;}
 inspect(){return {capacity:64,allocated:this.layers.length,droppedLayers:this.droppedLayers,meshes:this.meshes.size,materials:this.materials.size+this.layers.filter(x=>x.flowMaterial).length,active:this.layers.filter(x=>x.node.active).map(x=>({key:x.key,mode:x.phase,flow:x.flowMaterial?.getProperty('flowState')}))};}
 destroy(){this.clear();this.root.destroy();for(const layer of this.layers)layer.flowMaterial?.destroy();for(const mesh of this.meshes.values())mesh.destroy();for(const mat of this.materials.values())mat.destroy();this.meshes.clear();this.materials.clear();}
}
