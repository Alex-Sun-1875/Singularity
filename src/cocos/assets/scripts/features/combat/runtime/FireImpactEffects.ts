import {Camera,EffectAsset,Material,Mesh,MeshRenderer,Node,Texture2D,Vec3,Vec4,utils} from 'cc';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import type {Point} from '../../../core/Contracts';

type Impact={key:string;node:Node;renderer:MeshRenderer;mesh?:Mesh;touched:boolean;radius:number;progress:number;time:number;vertices:number;indices:number;clip:number[];origin:Point;position:Vec3;ground:number;maxHeight:number;width:number;kind:'contact'|'meteor';age:number;frontRadius:number;layers:number;lobes:number;peakHeight:number;supportWidth:number;supportDepth:number;ignitionProgress:number};
type Geometry={positions:number[];uvs:number[];colors:number[];indices:number[];minPos:Vec3;maxPos:Vec3};
const LIMIT=8,ANGLES=48,TAU=Math.PI*2;
const PATH='vfx/production/';
const CONTACT_U=.138990646117,CONTACT_V=.369657187871;
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const smooth=(n:number)=>{n=clamp(n);return n*n*(3-2*n);};

/** A single connected impact, followed by a low moving sheet of embers.
 * One selected, registered relief surface carries the complete impact; no
 * emitter grid, separate cones, target search, damage or new game clock. */
export class FireImpactEffects {
 private static textures:Texture2D[]=[];
 private static effect:EffectAsset|undefined;
 private static pending:Promise<void>|undefined;
 private static revision=0;
 private readonly root:Node;
 private readonly items:Impact[]=[];
 private material:Material|undefined;
 private lastTime=NaN;
 private disposed=false;
 reducedMotion=false;

 static preload():Promise<void>{
  if(this.pending)return this.pending;
  const revision=this.revision,names=['fire-contact-fan-v30','fire-meteor-burst-v32'];
  const textures=names.map(name=>new Promise<Texture2D>((resolve,reject)=>resources.load(PATH+name+'/texture',Texture2D,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);})));
  const effect=new Promise<EffectAsset>((resolve,reject)=>resources.load(PATH+'fire-impact-v34',EffectAsset,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);}));
  this.pending=(async()=>{
   const results=await Promise.allSettled([...textures,effect]);
   const failure=results.find(result=>result.status==='rejected');
   if(failure||revision!==this.revision){for(const result of results)if(result.status==='fulfilled')result.value.decRef();throw failure?.status==='rejected'?failure.reason:new Error('Fire impact load cancelled');}
   this.textures=results.slice(0,2).map(result=>(result as PromiseFulfilledResult<Texture2D>).value);
   this.effect=(results[2] as PromiseFulfilledResult<EffectAsset>).value;
   for(let i=0;i<this.textures.length;i++){
    const texture=this.textures[i],wrap=i===2?Texture2D.WrapMode.REPEAT:Texture2D.WrapMode.CLAMP_TO_EDGE;
    texture.setWrapMode(wrap,wrap);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);
   }
  })().catch(error=>{if(revision===this.revision)this.pending=undefined;throw error;});
  return this.pending;
 }
 /** Detach all instances before releasing their shared shader and textures. */
 static dispose(){this.revision++;for(const texture of this.textures)texture.decRef();this.textures=[];this.effect?.decRef();this.effect=undefined;this.pending=undefined;}
 constructor(parent:Node,private readonly camera:Camera|undefined,private readonly groundHeight:(p:Point)=>number,private readonly visible?:(a:Point,b:Point)=>boolean){
  this.root=new Node('ConnectedFireImpacts');this.root.layer=parent.layer;parent.addChild(this.root);
 }
 begin(){for(const item of this.items)item.touched=false;}
 private sharedMaterial(time:number):Material{
  if(!this.material){
   if(!FireImpactEffects.effect||FireImpactEffects.textures.length!==2)throw new Error('FireImpactEffects.preload must finish before drawing');
   this.material=new Material();this.material.name='ProjectProcedural:IgnitedMeteorImpactV34';this.material.initialize({effectAsset:FireImpactEffects.effect});
   this.material.setProperty('contactTexture',FireImpactEffects.textures[0]);this.material.setProperty('burstTexture',FireImpactEffects.textures[1]);
  }
  const clock=time*(this.reducedMotion?.35:1);
  if(clock!==this.lastTime){this.material.setProperty('flowState',new Vec4(clock,1,0,0));this.lastTime=clock;}
  return this.material;
 }
 private acquire(key:string,foot:Vec3,radius:number,time:number):Impact|undefined{
  let item=this.items.find(item=>item.key===key)??this.items.find(item=>!item.touched&&!item.node.active);
  if(!item){
   if(this.items.length>=LIMIT)return;
   const node=new Node('ConnectedMeteorFire');node.layer=this.root.layer;node.active=false;this.root.addChild(node);
   const renderer=node.addComponent(MeshRenderer);renderer.setSharedMaterial(this.sharedMaterial(time),0);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   item={key:'',node,renderer,touched:false,radius:0,progress:0,time:0,vertices:0,indices:0,clip:[],origin:{x:NaN,z:NaN},position:new Vec3(),ground:0,maxHeight:0,width:0,kind:'meteor',age:0,frontRadius:0,layers:0,lobes:0,peakHeight:0,supportWidth:0,supportDepth:0,ignitionProgress:0};this.items.push(item);
  }
  if(item.key!==key||item.radius!==radius||item.origin.x!==foot.x||item.origin.z!==foot.z){
   item.key=key;item.radius=radius;item.origin={x:foot.x,z:foot.z};item.ground=this.groundHeight(item.origin);item.clip=[];
   // Cache visibility at this resolved footprint, rather than tracing every
   // animated surface each frame. No visible fire travels through a wall.
   for(let i=0;i<ANGLES;i++){
    if(!this.visible||radius<1.1){item.clip.push(1);continue;}
    const angle=i/ANGLES*TAU,point=(fraction:number)=>({x:foot.x+Math.cos(angle)*radius*fraction,z:foot.z+Math.sin(angle)*radius*fraction});
    let lo=0,hi=1;if(this.visible(item.origin,point(1))){item.clip.push(1);continue;}
    for(let n=0;n<7;n++){const mid=(lo+hi)*.5;if(this.visible(item.origin,point(mid)))lo=mid;else hi=mid;}item.clip.push(lo);
   }
  }
  item.touched=true;item.time=time;item.position.set(foot);item.node.active=true;return item;
 }
 private geometry():Geometry{return{positions:[],uvs:[],colors:[],indices:[],minPos:new Vec3(Infinity,Infinity,Infinity),maxPos:new Vec3(-Infinity,-Infinity,-Infinity)};}
 private vertex(g:Geometry,item:Impact,x:number,y:number,z:number,u:number,v:number,opacity:number,kind:number,phase:number,supportDistance?:number){
  const dx=x-item.origin.x,dz=z-item.origin.z,distance=Math.hypot(dx,dz),theta=(Math.atan2(dz,dx)+TAU)%TAU/TAU*ANGLES,index=Math.floor(theta),blend=theta-index;
  const bound=item.radius*(item.clip[index%ANGLES]*(1-blend)+item.clip[(index+1)%ANGLES]*blend);
  const clipped=bound>=item.radius*.998?1:smooth((bound-distance)/Math.max(.05,item.radius*.10));
  // The final support never scales. Its fixed outer boundary and visibility
  // live in opacity; a separate stable support distance drives local ignition.
  const radial=kind===4?distance/Math.max(.001,item.radius):1,boundary=kind===4?1-smooth((radial-.91)/.19):1;
  g.positions.push(x,y,z);g.uvs.push(u,v);g.colors.push(clamp(opacity*clipped*boundary),kind,phase,supportDistance??radial);
  g.minPos.x=Math.min(g.minPos.x,x);g.minPos.y=Math.min(g.minPos.y,y);g.minPos.z=Math.min(g.minPos.z,z);
  g.maxPos.x=Math.max(g.maxPos.x,x);g.maxPos.y=Math.max(g.maxPos.y,y);g.maxPos.z=Math.max(g.maxPos.z,z);
 }
 /** alpha uses the same 0..255 contract as SkillFireSprites.drawVolume. */
 draw(key:string,foot:Vec3,radius:number,rank:number,progress:number,alpha:number,time:number,angle?:number,age?:number,duration?:number){
  if(this.disposed||!(radius>0&&alpha>0)||progress>=1)return;
  const t=clamp(progress),small=radius<1.1,life=Math.max(1.66,duration??4.55);
  // Resolved blast cues pass their existing event age. The legacy fallback
  // holds the old oscillating .22..35 presentation interval at a fixed stage;
  // it is never accumulated as a second simulation or gameplay clock.
  const fallbackAge=t<=.35?.32*Math.min(1,t/.22):t<.68?1.2+.45*(t-.35)/.33:1.65+(life-1.65)*(t-.68)/.32;
  const blastAge=Math.max(0,age??fallbackAge),tail=clamp((blastAge-1.65)/(life-1.65));
  if(!small&&blastAge>=life)return;
  const opacity=clamp(alpha/255)*(small?(1-smooth((t-.74)/.26))*(1-smooth((t-.24)/.28)):Math.pow(1-tail,1.3));if(opacity<=.002)return;
  this.sharedMaterial(time);const item=this.acquire(key,foot,radius,time);if(!item)return;item.progress=t;
  const g=this.geometry();item.kind=small?'contact':'meteor';item.renderer.priority=small?3:0;item.age=small?(age??0):blastAge;item.layers=0;item.lobes=0;item.frontRadius=0;item.peakHeight=0;item.supportWidth=0;item.supportDepth=0;item.ignitionProgress=0;
  const forward=this.camera?.node.isValid?this.camera.node.forward:undefined,flat=forward?Math.max(.001,Math.hypot(forward.x,forward.z)):1;
  const tx=forward?-forward.x/flat:.643,tz=forward?-forward.z/flat:.766,rx=tz,rz=-tx;
  if(small){
   // The separately authored short fan has a single pinned star nucleus. Its
   // camera-plane +X curls back along the incoming ray, beyond the body edge;
   // it does not reuse the meteor's sparse high-frequency ribbon texture.
   const up=this.camera?.node.isValid?this.camera.node.up:new Vec3(0,1,0),right=this.camera?.node.isValid?this.camera.node.right:new Vec3(rx,0,rz),growth=.25+.75*smooth(t/.14),width=radius*3*growth,tall=radius*1.4*growth;
   const incoming=new Vec3(Math.sin(angle??0),0,Math.cos(angle??0));
   let px=-Vec3.dot(incoming,right),py=-Vec3.dot(incoming,up),planeLength=Math.hypot(px,py);
   if(planeLength<.001){px=1;py=0;planeLength=1;}px/=planeLength;py/=planeLength;
   const along=new Vec3(right.x*px+up.x*py,right.y*px+up.y*py,right.z*px+up.z*py),across=new Vec3(-right.x*py+up.x*px,-right.y*py+up.y*px,-right.z*py+up.z*px);
   for(let row=0;row<=6;row++)for(let col=0;col<=12;col++){
    const u=col/12,v=row/6,lx=(u-CONTACT_U)*width,ly=(CONTACT_V-v)*tall,tip=smooth((u-CONTACT_U)/Math.max(.01,1-CONTACT_U));
    const bend=this.reducedMotion?0:Math.sin(time*7-u*6)*tall*.028*tip*Math.sin(v*Math.PI),bias=.20+.018*Math.sin((u-CONTACT_U)*Math.PI)*Math.sin(v*Math.PI);
    const x=foot.x+along.x*lx+across.x*(ly+bend)-(forward?.x??0)*bias,y=foot.y+along.y*lx+across.y*(ly+bend)-(forward?.y??0)*bias,z=foot.z+along.z*lx+across.z*(ly+bend)-(forward?.z??0)*bias;
    this.vertex(g,item,x,y,z,u,v,opacity*1.08,2,0);
    if(row<6&&col<12){const i=row*13+col;g.indices.push(i,i+1,i+14,i,i+14,i+13);}
   }
  }else{
   // One registered relief surface carries the selected complete impact. Its
   // screen silhouette and single nucleus come from the user's design, while
   // the middle plume rises in world Y and the low outer curls follow terrain.
   const q=clamp((blastAge-.020)/.260),front=radius*(.12+.88*(1-Math.pow(1-q,1.5))),settling=smooth((blastAge-1.20)/.45);
   const tier=Math.max(1,Math.min(5,rank)),main=1-settling,mainHeight=2.46+(tier-1)*.144,height=mainHeight*main+(.20+(tier-1)*.025)*settling*(1-.55*smooth(tail));
   const anchorU=.5287162162162162,anchorV=.5993150684931506,width=radius*2.20,screenHeight=width*292/592;
   const up=this.camera?.node.isValid?this.camera.node.up:new Vec3(0,.76,.65),right=this.camera?.node.isValid?this.camera.node.right:new Vec3(rx,0,rz);
   const flatUp=up.x*tx+up.z*tz,projection=Math.abs(flatUp)>.1?flatUp:-.65,base=foot.y-item.ground,motion=this.reducedMotion?.25:1;
   const us=Array.from({length:33},(_,i)=>i/32).concat(anchorU).sort((a,b)=>a-b),vs=Array.from({length:25},(_,i)=>i/24).concat(anchorV).sort((a,b)=>a-b);
   item.frontRadius=front;item.layers=1;item.lobes=1;item.supportWidth=width;item.supportDepth=screenHeight/Math.abs(projection);item.ignitionProgress=q;
   for(let row=0;row<vs.length;row++)for(let col=0;col<us.length;col++){
    const u=us[col],v=vs[row],du=u-anchorU,dv=anchorV-v,r=Math.hypot(du,dv),pin=smooth(r/.065);
    const plume=Math.exp(-Math.pow(du/.155,2))*Math.pow(Math.max(0,dv/anchorV),.88);
    const side=(Math.exp(-Math.pow((u-.81)/.17,2)-Math.pow((v-.45)/.18,2))*.28+Math.exp(-Math.pow((u-.23)/.17,2)-Math.pow((v-.67)/.14,2))*.12)*pin;
    const ripple=Math.sin(time*4.3*motion-u*12+v*7)*.045*motion*pin*Math.sin(u*Math.PI)*Math.sin(v*Math.PI);
    const lift=height*(plume+side)+Math.max(0,height*.05*(1-r*1.4))*pin;
    // Height is compensated in ground depth so the chosen camera retains the
    // approved complete silhouette instead of stretching it into upright cards.
    // Keep the projected surface monotonic while it settles. The previous
    // local compression inverted its derivative around 1.5s, folding the
    // rear centre into a V-shaped gap. A single positive scale preserves the
    // complete fire footprint as world height and overall opacity decline.
    // Match the reference plume/actor height ratio without stretching the
    // ground range. This positive expansion retains a positive derivative;
    // settling never reintroduces the former local compression/fold.
    const upperPlume=Math.exp(-Math.pow(du/.18,2))*smooth(Math.max(0,dv)/.20);
    const screenX=du*width,screenY=dv*screenHeight*(1-.16*settling)*(1+.20*main*upperPlume)+ripple*main;
    const depth=(screenY-lift*up.y)/projection,x=foot.x+right.x*screenX+tx*depth,z=foot.z+right.z*screenX+tz*depth;
    // A vertex's support is measured on the full-size steady relief, including
    // the upright central plume. It never moves with the reveal front, global
    // opacity, or the later positive settling projection.
    const supportLift=mainHeight*(plume+side)+Math.max(0,mainHeight*.05*(1-r*1.4))*pin,supportY=dv*screenHeight*(1+.20*upperPlume),supportZ=(supportY-supportLift*up.y)/projection;
    const supportDistance=Math.hypot(right.x*screenX+tx*supportZ,right.z*screenX+tz*supportZ)/Math.max(.001,radius);
    this.vertex(g,item,x,this.groundHeight({x,z})+base+lift,z,u,v,opacity,4,blastAge,supportDistance);
    item.peakHeight=Math.max(item.peakHeight,base+lift);
    if(row<vs.length-1&&col<us.length-1){const i=row*us.length+col;g.indices.push(i,i+1,i+us.length+1,i,i+us.length+1,i+us.length);}
   }
  }
  const geometry={positions:new Float32Array(g.positions),uvs:new Float32Array(g.uvs),colors:new Float32Array(g.colors),indices16:new Uint16Array(g.indices),minPos:g.minPos,maxPos:g.maxPos};
  if(!item.mesh){item.mesh=utils.MeshUtils.createDynamicMesh(0,geometry,undefined,{maxSubMeshes:1,maxSubMeshVertices:3200,maxSubMeshIndices:18000});item.mesh.name='ConnectedImpactOwnedMesh';item.renderer.mesh=item.mesh;}
  else{item.mesh.updateSubMesh(0,geometry);item.renderer.onGeometryChanged();}
  item.vertices=g.positions.length/3;item.indices=g.indices.length;item.maxHeight=g.maxPos.y-foot.y;item.width=Math.max(g.maxPos.x-g.minPos.x,g.maxPos.z-g.minPos.z);if(small)item.peakHeight=item.maxHeight;
 }
 end(){for(const item of this.items)if(!item.touched)item.node.active=false;}
 clear(){for(const item of this.items){item.node.active=false;item.touched=false;item.key='';}}
 inspect(){return{model:'fixed-support-radial-ignition-v34',capacity:LIMIT,allocated:this.items.length,sharedMaterials:this.material?1:0,cameraBound:!!this.camera,active:this.items.filter(item=>item.node.active).map(item=>({key:item.key,kind:item.kind,radius:item.radius,progress:item.progress,phase:item.progress,frameBlend:item.kind==='meteor'?(item.time*(this.reducedMotion?.35:1)*24)%1:0,atlasFrame:item.kind==='meteor'?Math.floor((item.time*(this.reducedMotion?.35:1)*24)%16):0,time:item.time,age:item.age,footprintRadius:item.kind==='meteor'?item.radius:undefined,supportWidth:item.kind==='meteor'?item.supportWidth:undefined,supportDepth:item.kind==='meteor'?item.supportDepth:undefined,geometryScale:item.kind==='meteor'?1:undefined,ignitionProgress:item.kind==='meteor'?item.ignitionProgress:undefined,frontRadius:item.frontRadius,layers:item.layers,lobes:item.lobes,cards:item.lobes,peakHeight:item.peakHeight,width:item.width,height:item.maxHeight,position:{x:item.position.x,y:item.position.y,z:item.position.z},vertices:item.vertices,triangles:item.indices/3,maxHeight:item.maxHeight,clippedDirections:item.clip.filter(bound=>bound<.999).length}))};}
 destroy(){if(this.disposed)return;this.disposed=true;this.clear();this.root.destroy();for(const item of this.items)item.mesh?.destroy();this.items.length=0;this.material?.destroy();this.material=undefined;}
}
