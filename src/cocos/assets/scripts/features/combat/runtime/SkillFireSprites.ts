import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,Material,Mesh,MeshRenderer,Node,Quat,Texture2D,Vec3,Vec4,gfx,primitives,utils} from 'cc';

type Point={x:number;z:number};
type FireBody={key:string;root:Node;card:Node;renderer:MeshRenderer;material:Material;touched:boolean;textureId:number;phase:number;width:number;height:number;region:number;meshId:number;tailMesh?:Mesh};
const LIMIT=64,ASPECT=1.5;
const SHORT_TAIL_STEPS=[0,.125,.25,.375,.5];
const REGIONS=[{u:0,v:0,w:1,h:1,foot:.44},{u:.03,v:.48,w:.44,h:.46,foot:.5},{u:.53,v:.48,w:.44,h:.46,foot:.5}];
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const smooth=(n:number)=>{n=clamp(n);return n*n*(3-2*n);};
/** Detailed pyro keyframes crossfade on spatially sorted rolls. Compact CC0
 * ignition cores and native particle tails are separate from ground blasts.
 * This layer only reads resolved combat positions and footprints. */
export class SkillFireSprites {
 private static textures:Texture2D[]=[];
 private static pending:Promise<void>|null=null;
 private static revision=0;
 private readonly root:Node;
 private readonly mesh:Mesh;
 private readonly shortTailGeometry:primitives.IDynamicGeometry[]=[];
 private readonly shortTailUpdates:primitives.IDynamicGeometry[]=[];
 private readonly items:FireBody[]=[];
 private readonly rotation=new Quat();
 private readonly roll=new Quat();
 private readonly point=new Vec3();
 private readonly color=new Vec4();
 private readonly tiling=new Vec4();
 private readonly clipped=new Map<string,number>();
 reducedMotion=false;
 private disposed=false;
 static preload():Promise<void>{
  if(this.pending)return this.pending;const revision=this.revision;
  this.pending=Promise.all(['fire-pyro-v7','fire-core-v7','fire-low-rolls-v7','fire-bolt-v9','fire-comet-v10'].map((name,index)=>new Promise<void>((resolve,reject)=>resources.load('vfx/production/'+name+'/texture',Texture2D,(error,texture)=>{
   if(error){reject(error);return;}if(revision!==this.revision){reject(new Error('Fire sequence load cancelled'));return;}
   texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);texture.addRef();this.textures[index]=texture;resolve();
  })))).then(()=>undefined).catch(error=>{this.dispose();throw error;});return this.pending;
 }
 static dispose(){this.revision++;for(const t of this.textures)t?.decRef();this.textures=[];this.pending=null;}
 constructor(parent:Node,private readonly camera?:Camera,private readonly groundHeight?:(p:Point)=>number,private readonly visible?:(a:Point,b:Point)=>boolean){
  this.root=new Node('FirePyroSequence');this.root.layer=parent.layer;parent.addChild(this.root);const g=primitives.quad();for(let i=1;i<g.uvs!.length;i+=2)g.uvs![i]=1-g.uvs![i];this.mesh=utils.createMesh(g);this.mesh.name='FireSharedQuad';
  // Two native quad strips keep the round head unchanged while compressing
  // only the wake. Keep all five authored shapes. A card changes its dynamic
  // positions only on a stage transition, retaining its native SubModel/UBOs.
  for(const scale of SHORT_TAIL_STEPS){
   const positions:number[]=[],normals:number[]=[],uvs:number[]=[],indices:number[]=[];
   for(const u of [0,.70,1])for(const y of [-.5,.5]){positions.push(u<.70?.20+(u-.70)*scale:u-.5,y,0);normals.push(0,0,1);uvs.push(u,.5-y);}
   for(let col=0;col<2;col++){const b=col*2;indices.push(b,b+2,b+1,b+2,b+3,b+1);}
   const minPos={x:Math.min(...positions.filter((_,i)=>i%3===0)),y:-.5,z:0},maxPos={x:Math.max(...positions.filter((_,i)=>i%3===0)),y:.5,z:0};
   const geometry={positions:new Float32Array(positions),normals:new Float32Array(normals),uvs:new Float32Array(uvs),indices16:new Uint16Array(indices),minPos,maxPos};
   this.shortTailGeometry.push(geometry);this.shortTailUpdates.push({positions:geometry.positions,indices16:geometry.indices16,minPos,maxPos});
  }
 }
 begin(){for(const item of this.items)item.touched=false;}
 private sprite(key:string,p:Vec3,width:number,frame:number,alpha:number,region=0,core=false,direction?:Vec3,comet=false,meshId=-1){
  if(this.disposed||!(width>0&&alpha>1))return;
  let item=this.items.find(i=>i.key===key);
  if(!item)item=this.items.find(i=>!i.touched&&!i.root.active&&(i.meshId>=0)===(meshId>=0));
  if(!item&&this.items.length>=LIMIT)item=this.items.find(i=>!i.touched&&(i.meshId>=0)===(meshId>=0))??this.items.find(i=>!i.touched);
  if(!item){
   if(this.items.length>=LIMIT)return;
   const root=new Node('FireFoot'),card=new Node('FirePyroRoll');root.layer=card.layer=this.root.layer;root.active=false;this.root.addChild(root);root.addChild(card);
   const material=new Material();material.name='FirePyroV7';material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
   const renderer=card.addComponent(MeshRenderer);renderer.mesh=this.mesh;renderer.setSharedMaterial(material,0);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   item={key,root,card,renderer,material,touched:false,textureId:-1,phase:-1,width:0,height:0,region:-1,meshId:-1};this.items.push(item);
  }
  item.key=key;item.touched=true;
  if(item.meshId!==meshId){
   if(meshId<0)item.renderer.mesh=this.mesh;
   else{
    if(!item.tailMesh){item.tailMesh=utils.MeshUtils.createDynamicMesh(0,this.shortTailGeometry[meshId],undefined,{maxSubMeshes:1,maxSubMeshVertices:6,maxSubMeshIndices:12});item.tailMesh.name='FireOwnedShortWake';}
    else item.tailMesh.updateSubMesh(0,this.shortTailUpdates[meshId]);
    if(item.renderer.mesh!==item.tailMesh)item.renderer.mesh=item.tailMesh;else item.renderer.onGeometryChanged();
   }
   item.meshId=meshId;
  }
  item.root.active=true;
  if(!Vec3.strictEquals(item.root.worldPosition,p))item.root.setWorldPosition(p);
  if(core&&this.camera?.node.isValid){
   Quat.copy(this.rotation,this.camera.node.worldRotation);
   if(direction){
    const right=this.camera.node.right,up=this.camera.node.up;
    const angle=Math.atan2(Vec3.dot(direction,up),Vec3.dot(direction,right));
    Quat.fromEuler(this.roll,0,0,angle*180/Math.PI);Quat.multiply(this.rotation,this.rotation,this.roll);
   }
  }
  else if(this.camera?.node.isValid){const f=this.camera.node.forward;Quat.fromEuler(this.rotation,0,Math.atan2(-f.x,-f.z)*180/Math.PI,0);}else Quat.fromEuler(this.rotation,0,40,0);
  if(!Quat.equals(item.root.worldRotation,this.rotation))item.root.setWorldRotation(this.rotation);
  const r=REGIONS[region],height=direction?width*(comet?.375:.52):core?width:width/(region?128/96:ASPECT),y=core?0:(region?90/96-.5:r.foot)*height,x=direction?-width*((comet?.835:194/256)-.5):0;
  if(item.card.position.y!==y||item.card.position.x!==x)item.card.setPosition(x,y,0);
  if(item.width!==width||item.height!==height){item.card.setScale(width,height,1);item.width=width;item.height=height;}
  frame=Math.max(0,Math.min(core?3:15,Math.floor(frame)));if(!core&&region===2)frame+=16;
  const id=comet?4:direction?3:core?1:region?2:0,cols=4,rows=core?1:region?8:4;
  if(item.textureId!==id){item.material.setProperty('mainTexture',SkillFireSprites.textures[id]);item.textureId=id;item.phase=-1;}
  if(item.phase!==frame||item.region!==region){item.phase=frame;item.region=region;this.tiling.set(1/cols,1/rows,frame%cols/cols,Math.floor(frame/cols)/rows);item.material.setProperty('tilingOffset',this.tiling);}
  const gain=this.reducedMotion?.88:1.06;this.color.set(gain,gain,gain,clamp(alpha/255));item.material.setProperty('mainColor',this.color);
 }
 private phase(key:string,p:Vec3,width:number,clock:number,alpha:number,region=0){
  const frame=Math.max(0,Math.min(15,clock)),whole=Math.floor(frame),blend=this.reducedMotion?0:smooth(frame-whole);
  // Straight-alpha source-over loses 25% of the body at a 50/50 fade, even
  // before texture/field opacity. Hold the outgoing fire until the incoming
  // frame is dense, then retire it; the existing two-card budget is unchanged.
  const outgoing=1-smooth((blend-.58)/.42),incoming=smooth(blend/.72);
  this.sprite(key+':a',p,width,whole,alpha*outgoing,region);
  if(incoming>0&&whole<15)this.sprite(key+':b',p,width,whole+1,alpha*incoming,region);
 }
 private visibleWidth(origin:Point,p:Point,width:number,dx:number,dz:number,key:string){
  if(!this.visible)return width;
  const cache=`${key}:${origin.x.toFixed(3)}:${origin.z.toFixed(3)}:${p.x.toFixed(3)}:${p.z.toFixed(3)}:${width.toFixed(3)}:${dx.toFixed(3)}:${dz.toFixed(3)}`;
  const cached=this.clipped.get(cache);if(cached!==undefined)return cached;
  let ratio=this.visible(origin,p)?1:0;
  if(ratio)for(const sign of [-1,1]){
   const end=(t:number)=>({x:p.x+dx*width*.5*sign*t,z:p.z+dz*width*.5*sign*t});if(this.visible(origin,end(1)))continue;
   let lo=0,hi=1;for(let i=0;i<7;i++){const mid=(lo+hi)/2;if(this.visible(origin,end(mid)))lo=mid;else hi=mid;}ratio=Math.min(ratio,lo);
  }
  const result=width*ratio;if(this.clipped.size>=384)this.clipped.delete(this.clipped.keys().next().value!);this.clipped.set(cache,result);return result;
 }
 drawProjectile(key:string,center:Vec3,direction:Vec3,size:number,time:number,alpha=255){
  const beat=Math.floor(time*24)%6,frame=beat<4?beat:6-beat;
  // The head stays on the resolved projectile; a textured, directional flame
  // extends behind it. A small ignition core replaces the former round orb.
  this.sprite(key,center,size*1.75,frame,alpha,0,true,direction);
  this.sprite(key+':core',center,size*.24,frame,alpha,0,true);
 }
 drawComet(key:string,head:Vec3,direction:Vec3,size:number,time:number,alpha=255,tailStage=-1){
  // One coherent fire silhouette includes the round head and tapered wake.
  // The head is the pivot; rotating the card never detaches the tail from it.
  const clock=time*12,frame=Math.floor(clock)%4,blend=this.reducedMotion?0:smooth(clock-Math.floor(clock));
  this.sprite(key+':a',head,size*3.5,frame,alpha*(1-smooth((blend-.58)/.42)),0,true,direction,true,tailStage);
  if(blend>0)this.sprite(key+':b',head,size*3.5,(frame+1)%4,alpha*smooth(blend/.72),0,true,direction,true,tailStage);
 }
 drawBasicComet(key:string,head:Vec3,direction:Vec3,size:number,time:number,travel:number,hand?:Vec3){
  const normal=this.camera?.node.forward,dot=normal?Vec3.dot(direction,normal):0;
  const length=Math.sqrt(Math.max(0,direction.lengthSqr()-dot*dot));if(length<.0001)return;
  let distance=travel*length;
  if(hand){
   const x=direction.x-(normal?.x??0)*dot,y=direction.y-(normal?.y??0)*dot,z=direction.z-(normal?.z??0)*dot;
   distance=Math.min(distance,((head.x-hand.x)*x+(head.y-hand.y)*y+(head.z-hand.z)*z)/length);
  }
  // Grow only as much wake as fits between the moving head and the fixed
  // release point. Even its first visible frame leaves a .20m camera-plane gap.
  const available=((distance-.20)/(size*3.5)-(.835-.70))/.70;
  if(available<0)return;
  let stage=0;while(stage<SHORT_TAIL_STEPS.length-1&&SHORT_TAIL_STEPS[stage+1]<=available)stage++;
  this.drawComet(key,head,direction,size,time,255,stage);
 }
 draw(key:string,foot:Vec3,width:number,height:number,phase:number,alpha:number){this.phase(key,foot,Math.min(width,height*ASPECT),phase*4,alpha);}
 drawPlume(key:string,foot:Vec3,size:number,time:number,alpha:number){const beat=time*7%8;this.phase(key,foot,size,4+(beat<4?beat:8-beat),alpha,1);}
 drawVolume(key:string,foot:Vec3,radius:number,rank:number,progress:number,alpha:number){
  if(!(radius>0&&alpha>0)||progress>=1)return;
  const t=clamp(progress),spread=.62+.38*smooth(t/.16),fade=1-smooth((t-.78)/.22),clock=t<.20?t*30:6+(t-.20)*11.25;
  let tx=.643,tz=.766,rx=.766,rz=-.643;
  if(this.camera?.node.isValid){const f=this.camera.node.forward,length=Math.hypot(f.x,f.z);if(length>.001){tx=-f.x/length;tz=-f.z/length;rx=tz;rz=-tx;}}
  const base=this.groundHeight?.(foot),lift=base===undefined?0:foot.y-base;
  const x=foot.x-radius*tx*.12,z=foot.z-radius*tz*.12;
  this.point.set(x,this.groundHeight?this.groundHeight({x,z})+lift:foot.y,z);
  const width=this.visibleWidth(foot,{x,z},radius*1.70*spread,rx,rz,key+':main');this.phase(key+':main',this.point,width,clock,alpha*fade);
  if(radius<.8||t<.12||this.reducedMotion)return;
  for(const side of [-1,1]){
   const x=foot.x+radius*spread*(rx*side*.35+tx*.28),z=foot.z+radius*spread*(rz*side*.35+tz*.28);
   this.point.set(x,this.groundHeight?this.groundHeight({x,z})+lift:foot.y,z);
   const width=this.visibleWidth(foot,{x,z},radius*.85*spread,rx,rz,key+':front:'+side);
   this.phase(`${key}:front:${side}`,this.point,width,Math.max(0,clock-1),alpha*.68*fade*smooth((t-.12)/.10),side<0?1:2);
  }
 }
 drawRibbon(key:string,foot:Vec3,width:number,depth:number,angle:number,time:number,alpha:number,origin:Point=foot){
  if(!(width>0&&depth>0&&alpha>0))return;
  const cols=Math.max(2,Math.min(8,Math.ceil(width/1.25))),rows=depth>3?3:depth>1.3?2:1;
  const sx=Math.cos(angle),sz=-Math.sin(angle),fx=Math.sin(angle),fz=Math.cos(angle),base=this.groundHeight?.(foot),lift=base===undefined?0:foot.y-base;
  const f=this.camera?.node.isValid?this.camera.node.forward:undefined,len=f?Math.hypot(f.x,f.z):0,rx=len>.001?-f!.z/len:.766,rz=len>.001?f!.x/len:-.643,across=Math.abs(rx*sx+rz*sz),along=Math.abs(rx*fx+rz*fz);
  for(let row=0;row<rows;row++)for(let col=0;col<cols;col++){
   const side=((col+.5)/cols-.5)*width,forward=rows===1?0:((row+.5)/rows-.5)*depth*.70,x=foot.x+sx*side+fx*forward,z=foot.z+sz*side+fz*forward;
   const sideLimit=across>.001?2*(width/2-Math.abs(side))/across:Infinity,depthLimit=along>.001?2*(depth/2-Math.abs(forward))/along:Infinity;
   const desired=Math.min(2.1,width/cols*1.70,sideLimit,depthLimit),size=this.visibleWidth(origin,{x,z},desired,rx,rz,`${key}:${row}:${col}`);if(size<=0)continue;
   this.point.set(x,this.groundHeight?this.groundHeight({x,z})+lift:foot.y,z);
   const beat=(time*5+col*.71+row*1.3)%10,clock=4+(beat<5?beat:10-beat);
   this.phase(`${key}:${row}:${col}`,this.point,size,clock,alpha*(row===0?1:.90),(col+row)%2?1:2);
  }
 }
 end(){for(const item of this.items)if(!item.touched)item.root.active=false;}
 clear(){this.clipped.clear();for(const item of this.items){item.root.active=false;item.touched=false;item.key='';}}
 inspect(){return{model:'pyro-keyframes-v7',capacity:LIMIT,allocated:this.items.length,active:this.items.filter(i=>i.root.active).map(i=>({key:i.key,phase:i.phase,textureId:i.textureId,region:i.region,width:i.width,height:i.height,tailScale:i.meshId<0?1:SHORT_TAIL_STEPS[i.meshId],position:{x:i.root.worldPosition.x,y:i.root.worldPosition.y,z:i.root.worldPosition.z}}))};}
 destroy(){if(this.disposed)return;this.disposed=true;for(const item of this.items)item.material.destroy();this.root.destroy();for(const item of this.items)item.tailMesh?.destroy();this.items.length=0;this.mesh.destroy();}
}
