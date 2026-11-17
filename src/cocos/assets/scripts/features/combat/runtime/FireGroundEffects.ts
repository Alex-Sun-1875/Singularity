import {Camera,EffectAsset,Material,Mesh,MeshRenderer,Node,Texture2D,Vec3,Vec4,utils} from 'cc';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import type {Point} from '../../../core/Contracts';

type Kind='jets'|'smallSeal'|'meteorSeal';
type Surface={key:string;kind:Kind;node:Node;renderer:MeshRenderer;material:Material;mesh?:Mesh;vertices:number;indices:number;emitters:number;frames:number[][];touched:boolean;opacity:number};
type Geometry={positions:number[];uvs:number[];colors:number[];indices:number[];minPos:Vec3;maxPos:Vec3;emitters?:number;frames?:number[][];time?:number};
const PATH='vfx/production/',LIMIT=8,FLAME_FRAMES=32;
const smooth=(n:number)=>{const t=Math.max(0,Math.min(1,n));return t*t*(3-2*t);};

/** Native ground arrays and five upright selected-reference flame emitters.
 * Each cast batches its seals and curved flame surfaces into two bounded meshes. Events
 * supply the footprint; this class neither finds victims nor submits damage. */
export class FireGroundEffects {
 private static textures:Texture2D[]=[];private static effect:EffectAsset|undefined;private static meteorEffect:EffectAsset|undefined;private static pending:Promise<void>|undefined;private static revision=0;
 private readonly root:Node;private readonly surfaces:Surface[]=[];private disposed=false;
 reducedMotion=false;
 static preload():Promise<void>{
  if(this.pending)return this.pending;const revision=this.revision;
  const textures=Promise.all(['fire-ground-jets-v27','fire-jet-seal-v27','fire-meteor-seal-colour-v37','fire-flow-noise-v24','fire-meteor-seal-light-v37'].map((name,i)=>new Promise<void>((resolve,reject)=>{
   resources.load(PATH+name+'/texture',Texture2D,(error,texture)=>{
    if(error){reject(error);return;}if(revision!==this.revision){reject(new Error('Fire ground load cancelled'));return;}
    const wrap=i===3?Texture2D.WrapMode.REPEAT:Texture2D.WrapMode.CLAMP_TO_EDGE;
    texture.setWrapMode(wrap,wrap);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);
    texture.addRef();this.textures[i]=texture;resolve();
   });
  })));
  const effect=new Promise<void>((resolve,reject)=>resources.load(PATH+'fire-ground-v27',EffectAsset,(error,asset)=>{
   if(error){reject(error);return;}if(revision!==this.revision){reject(new Error('Fire ground effect load cancelled'));return;}
   asset.addRef();this.effect=asset;resolve();
  }));
  const meteorEffect=new Promise<void>((resolve,reject)=>resources.load(PATH+'fire-seal-v35r2',EffectAsset,(error,asset)=>{if(error){reject(error);return;}if(revision!==this.revision){reject(new Error('Meteor seal load cancelled'));return;}asset.addRef();this.meteorEffect=asset;resolve();}));
  this.pending=Promise.all([textures,effect,meteorEffect]).then(()=>undefined).catch(error=>{if(revision===this.revision)this.dispose();throw error;});return this.pending;
 }
 static dispose(){this.revision++;for(const texture of this.textures)texture?.decRef();this.textures=[];this.effect?.decRef();this.effect=undefined;this.meteorEffect?.decRef();this.meteorEffect=undefined;this.pending=undefined;}
 constructor(parent:Node,private readonly camera:Camera|undefined,private readonly height:(p:Point)=>number,private readonly visible:(a:Point,b:Point)=>boolean){
  this.root=new Node('FireGroundArrays');this.root.layer=parent.layer;parent.addChild(this.root);
 }
 begin(){for(const item of this.surfaces)item.touched=false;}
 private geometry():Geometry{return{positions:[],uvs:[],colors:[],indices:[],minPos:new Vec3(Infinity,Infinity,Infinity),maxPos:new Vec3(-Infinity,-Infinity,-Infinity)};}
 private quad(g:Geometry,points:readonly Vec3[],uv:readonly number[],frame:readonly number[]=[1,1,1,1]){
  const start=g.positions.length/3;
  for(let i=0;i<4;i++){
   const p=points[i];g.positions.push(p.x,p.y,p.z);g.uvs.push(uv[i*2],uv[i*2+1]);g.colors.push(frame[0],frame[1],frame[2],frame[3]);
   g.minPos.x=Math.min(g.minPos.x,p.x);g.minPos.y=Math.min(g.minPos.y,p.y);g.minPos.z=Math.min(g.minPos.z,p.z);
   g.maxPos.x=Math.max(g.maxPos.x,p.x);g.maxPos.y=Math.max(g.maxPos.y,p.y);g.maxPos.z=Math.max(g.maxPos.z,p.z);
  }
  g.indices.push(start,start+1,start+2,start,start+2,start+3);
 }
 private ground(g:Geometry,p:Point,size:number,cameraAligned=false,lift=cameraAligned?.095:.045){
  const right=cameraAligned?this.camera?.node.right:undefined,forward=cameraAligned?this.camera?.node.forward:undefined;
  const length=forward?Math.max(.001,Math.hypot(forward.x,forward.z)):1;
  const half=size*.5,steps=cameraAligned?6:1,start=g.positions.length/3;
  for(let row=0;row<=steps;row++)for(let col=0;col<=steps;col++){
   const x=col/steps*2-1,z=row/steps*2-1;
   const q=right&&forward?{x:p.x+(right.x*x-forward.x/length*z)*half,z:p.z+(right.z*x-forward.z/length*z)*half}:{x:p.x+x*half,z:p.z+z*half};
   const y=this.height(q)+lift;
   // Camera-aligned row zero is the far edge. Image row zero belongs there,
   // keeping the reference's small front loop on the near side of the circle.
   g.positions.push(q.x,y,q.z);g.uvs.push(col/steps,cameraAligned?row/steps:1-row/steps);g.colors.push(1,1,1,1);
   g.minPos.x=Math.min(g.minPos.x,q.x);g.minPos.y=Math.min(g.minPos.y,y);g.minPos.z=Math.min(g.minPos.z,q.z);
   g.maxPos.x=Math.max(g.maxPos.x,q.x);g.maxPos.y=Math.max(g.maxPos.y,y);g.maxPos.z=Math.max(g.maxPos.z,q.z);
   if(row<steps&&col<steps){const i=start+row*(steps+1)+col;g.indices.push(i,i+1,i+steps+2,i,i+steps+2,i+steps+1);}
  }
 }
 private surface(key:string,kind:Kind,data:Geometry,opacity:number){
  if(this.disposed||!data.indices.length||opacity<=.002)return;
  let item=this.surfaces.find(s=>s.key===key&&s.kind===kind)??this.surfaces.find(s=>!s.touched&&!s.node.active&&s.kind===kind);
  if(!item){
   if(this.surfaces.length>=LIMIT)return;
   const texture=FireGroundEffects.textures[kind==='jets'?0:kind==='smallSeal'?1:2];if(!texture)throw new Error('FireGroundEffects.preload must finish before rendering');
   const node=new Node('FireGround:'+kind);node.layer=this.root.layer;node.active=false;this.root.addChild(node);
   const material=new Material();material.name='ProjectProcedural:FireGround:'+kind;
   if(kind==='meteorSeal'){if(!FireGroundEffects.meteorEffect)throw new Error('Meteor seal effect not ready');material.initialize({effectAsset:FireGroundEffects.meteorEffect});}
   else{
    if(!FireGroundEffects.effect)throw new Error('Fire ground effect not ready');
    material.initialize({effectAsset:FireGroundEffects.effect});material.setProperty('noiseTexture',FireGroundEffects.textures[3]);
   }
   material.setProperty('mainTexture',texture);
   if(kind==='meteorSeal')material.setProperty('lightTexture',FireGroundEffects.textures[4]);
   const renderer=node.addComponent(MeshRenderer);renderer.setSharedMaterial(material,0);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   item={key,kind,node,renderer,material,touched:false,vertices:0,indices:0,emitters:0,frames:[],opacity:0};this.surfaces.push(item);
  }
  item.key=key;item.touched=true;item.node.active=true;
  const geometry={positions:new Float32Array(data.positions),uvs:new Float32Array(data.uvs),colors:new Float32Array(data.colors),indices16:new Uint16Array(data.indices),minPos:data.minPos,maxPos:data.maxPos};
  if(!item.mesh){item.mesh=utils.MeshUtils.createDynamicMesh(0,geometry,undefined,{maxSubMeshes:1,maxSubMeshVertices:640,maxSubMeshIndices:3072});item.renderer.mesh=item.mesh;}
  else{item.mesh.updateSubMesh(0,geometry);item.renderer.onGeometryChanged();}
  item.vertices=data.positions.length/3;item.indices=data.indices.length;item.emitters=data.emitters??0;item.frames=data.frames??[];
  const alpha=Math.max(0,Math.min(1,opacity));
  item.opacity=alpha;
  item.material.setProperty('mainColor',new Vec4(1,1,1,alpha));
  if(kind!=='meteorSeal')item.material.setProperty('surfaceState',new Vec4(kind==='smallSeal'?1:0,(data.time??0)*(this.reducedMotion?.4:1),this.reducedMotion?.3:1,0));
 }
 drawJets(key:string,origin:Point,angle:number,length:number,width:number,time:number,opacity:number,emitting=true,cooling=0){
  const fire=this.geometry(),seals=this.geometry(),right=this.camera?.node.right??new Vec3(.766,0,-.643);fire.time=time;seals.time=time;
  const forward=this.camera?.node.forward,flat=forward?Math.max(.001,Math.hypot(forward.x,forward.z)):1;
  const tx=forward?-forward.x/flat:.643,tz=forward?-forward.z/flat:.766;
  for(let i=0;i<5;i++){
   const distance=(i+.5)*length/5,p={x:origin.x+Math.sin(angle)*distance,z:origin.z+Math.cos(angle)*distance};
   if(!this.visible(origin,p))continue;
   this.ground(seals,p,width/(231/256),true);
   seals.emitters=(seals.emitters??0)+1;
   if(!emitting)continue;
   fire.emitters=(fire.emitters??0)+1;
   // Two soft curved curtains give the approved plume a circular footprint and
   // real depth. Its registered root stays on the sigil through the whole loop.
   const tall=2.62*smooth(time/.16)*(1-.65*smooth(cooling)),radius=width*.55,foot=this.height(p)+.10,bottom=foot-tall/12;
   const levels=[0,1/12,.25,.5,.75,1];
   for(const side of [-1,1]){
    const clock=(time*(this.reducedMotion?12:24)+i*5.7+(side<0?11:0))%FLAME_FRAMES,frame=Math.floor(clock),next=(frame+1)%FLAME_FRAMES,blend=clock-frame;
    (fire.frames??=[]).push([frame,next,blend]);
    const start=fire.positions.length/3,columns=8,alpha=side<0?.08:1;
    for(let row=0;row<levels.length;row++)for(let col=0;col<=columns;col++){
     const t=levels[row],u=col/columns,horizontal=u*2-1,lift=Math.max(0,(t-1/12)/(11/12));
     // Keep uniform horizontal UV scale. A sine mapping enlarged centre
     // filaments, and the old height-dependent bend made them read as arcs.
     const across=horizontal*radius,depth=Math.sqrt(Math.max(0,1-horizontal*horizontal))*radius*.4*Math.pow(1-lift,1.65)*side;
     const x=p.x+right.x*across+tx*depth,y=bottom+t*tall,z=p.z+right.z*across+tz*depth;
     fire.positions.push(x,y,z);fire.uvs.push(u,1-t);fire.colors.push(frame/(FLAME_FRAMES-1),next/(FLAME_FRAMES-1),blend,alpha);
     fire.minPos.x=Math.min(fire.minPos.x,x);fire.minPos.y=Math.min(fire.minPos.y,y);fire.minPos.z=Math.min(fire.minPos.z,z);
     fire.maxPos.x=Math.max(fire.maxPos.x,x);fire.maxPos.y=Math.max(fire.maxPos.y,y);fire.maxPos.z=Math.max(fire.maxPos.z,z);
     if(row<levels.length-1&&col<columns){const n=start+row*(columns+1)+col;fire.indices.push(n,n+1,n+columns+2,n,n+columns+2,n+columns+1);}
    }
   }
  }
  this.surface(key+':seal','smallSeal',seals,opacity*(emitting?1:.75));
  if(emitting)this.surface(key+':flame','jets',fire,opacity);
 }
 drawMeteorSeal(key:string,p:Point,radius:number,opacity:number){
  if(!(radius>0))return;const data=this.geometry();data.emitters=1;this.ground(data,p,radius*2/(460/512),true,.045);this.surface(key,'meteorSeal',data,opacity);
 }
 end(){for(const item of this.surfaces)if(!item.touched)item.node.active=false;}
 clear(){for(const item of this.surfaces){item.node.active=false;item.touched=false;item.key='';}}
 inspect(){return{capacity:LIMIT,allocated:this.surfaces.length,active:this.surfaces.filter(s=>s.node.active).map(s=>({key:s.key,kind:s.kind,opacity:s.opacity,emitters:s.emitters,triangles:s.indices/3,vertices:s.vertices,frames:s.frames})),cameraBound:!!this.camera};}
 destroy(){if(this.disposed)return;this.disposed=true;this.root.destroy();for(const item of this.surfaces){item.material.destroy();item.mesh?.destroy();}this.surfaces.length=0;}
}
