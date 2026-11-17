import {Camera,EffectAsset,Material,Mesh,MeshRenderer,Node,Texture2D,Vec3,Vec4,utils} from 'cc';
import {gameResources as resources} from '../../../shared/assets/GameResources';

type Point={x:number;z:number};
type Field={key:string;node:Node;renderer:MeshRenderer;material:Material;mesh?:Mesh;touched:boolean;phase:number;blend:number;width:number;depth:number;height:number;position:Vec3;vertices:number};
const LIMIT=4;
const smooth=(t:number)=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};

/** One connected, terrain-following fire surface with two low curling skins.
 * The approved field pattern spans the whole authoritative rectangle. It is
 * never distributed as separate bonfires, and does not own a damage clock. */
export class FireFieldEffects {
 private static texture:Texture2D|undefined;
 private static effect:EffectAsset|undefined;
 private static pending:Promise<void>|undefined;
 private static revision=0;
 private readonly root:Node;
 private readonly fields:Field[]=[];
 private readonly visibility=new Map<string,boolean>();
 private disposed=false;
 reducedMotion=false;
 static preload():Promise<void>{
  if(this.pending)return this.pending;const revision=this.revision;
  const texture=new Promise<Texture2D>((resolve,reject)=>resources.load('vfx/production/fire-field-flow-v30/texture',Texture2D,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);}));
  const effect=new Promise<EffectAsset>((resolve,reject)=>resources.load('vfx/production/fire-field-v30',EffectAsset,(error,asset)=>{if(error){reject(error);return;}asset.addRef();resolve(asset);}));
  this.pending=(async()=>{
   const [t,e]=await Promise.allSettled([texture,effect]);
   if(t.status==='rejected'||e.status==='rejected'||revision!==this.revision){
    if(t.status==='fulfilled')t.value.decRef();if(e.status==='fulfilled')e.value.decRef();
    throw t.status==='rejected'?t.reason:e.status==='rejected'?e.reason:new Error('Fire field load cancelled');
   }
   t.value.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);t.value.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);t.value.setMipFilter(Texture2D.Filter.NONE);this.texture=t.value;this.effect=e.value;
  })().catch(error=>{if(revision===this.revision)this.pending=undefined;throw error;});return this.pending;
 }
 static dispose(){this.revision++;this.texture?.decRef();this.effect?.decRef();this.texture=undefined;this.effect=undefined;this.pending=undefined;}
 constructor(parent:Node,_camera:Camera|undefined,private readonly height:(p:Point)=>number,private readonly visible?:(a:Point,b:Point)=>boolean){this.root=new Node('ContinuousFireFields');this.root.layer=parent.layer;parent.addChild(this.root);}
 begin(){for(const field of this.fields)field.touched=false;}
 private canSee(origin:Point,p:Point){
  if(!this.visible)return true;
  const key=`${origin.x.toFixed(2)}:${origin.z.toFixed(2)}:${p.x.toFixed(2)}:${p.z.toFixed(2)}`;
  const cached=this.visibility.get(key);if(cached!==undefined)return cached;
  const value=this.visible(origin,p);if(this.visibility.size>=1024)this.visibility.clear();this.visibility.set(key,value);return value;
 }
 draw(key:string,foot:Vec3,width:number,depth:number,angle:number,time:number,alpha:number,origin:Point=foot,cooling=-1){
  if(this.disposed||!(width>0&&depth>0&&alpha>1))return;
  let field=this.fields.find(f=>f.key===key)??this.fields.find(f=>!f.node.active&&!f.touched);
  if(!field){
   if(this.fields.length>=LIMIT)return;if(!FireFieldEffects.texture||!FireFieldEffects.effect)throw new Error('FireFieldEffects.preload must finish first');
   const node=new Node('ConnectedFireField');node.layer=this.root.layer;this.root.addChild(node);
   const material=new Material();material.name='ConnectedFireFieldDenseV38';material.initialize({effectAsset:FireFieldEffects.effect});material.setProperty('mainTexture',FireFieldEffects.texture);
   const renderer=node.addComponent(MeshRenderer);renderer.setSharedMaterial(material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   field={key,node,renderer,material,touched:false,phase:0,blend:0,width:0,depth:0,height:0,position:new Vec3(),vertices:0};this.fields.push(field);
  }
  const positions:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[],minPos=new Vec3(Infinity,Infinity,Infinity),maxPos=new Vec3(-Infinity,-Infinity,-Infinity);
  const sx=Math.cos(angle),sz=-Math.sin(angle),fx=Math.sin(angle),fz=Math.cos(angle),lift=foot.y-this.height(foot),settling=cooling<0?0:smooth(cooling),motion=this.reducedMotion?.35:1,clock=time*(this.reducedMotion?10:18),phase=((clock%16)+16)%16;
  const add=(u:number,v:number,side:number,forward:number,y:number,skin:number,weight:number)=>{
   const x=foot.x+sx*side+fx*forward,z=foot.z+sz*side+fz*forward,h=this.height({x,z})+lift+y;
   positions.push(x,h,z);uvs.push(u,v);colors.push(skin,weight,0,this.canSee(origin,{x,z})?1:0);
   minPos.x=Math.min(minPos.x,x);minPos.y=Math.min(minPos.y,h);minPos.z=Math.min(minPos.z,z);maxPos.x=Math.max(maxPos.x,x);maxPos.y=Math.max(maxPos.y,h);maxPos.z=Math.max(maxPos.z,z);
  };
  const cells=(start:number,cols:number,rows:number)=>{for(let row=0;row<rows;row++)for(let col=0;col<cols;col++){const a=start+row*(cols+1)+col;indices.push(a,a+1,a+cols+2,a,a+cols+2,a+cols+1);}};
  // Continuous lower fire flow, carrying the full width AND depth.
  for(let row=0;row<=12;row++)for(let col=0;col<=24;col++){
   const u=col/24,v=row/12,envelope=Math.sin(Math.PI*u)*Math.sin(Math.PI*v),wave=.5+.5*Math.sin(u*13-v*9-time*2.1*motion);
   add(u,v,(u-.5)*width,(v-.5)*depth,.055+envelope*(.10+.18*wave)*(1-.72*settling),0,1);
  }cells(0,24,12);
  // Two broad curls meet the lower sheet; neither is a row of separate cones.
  for(let skin=0;skin<2;skin++){
   const start=positions.length/3;
   for(let row=0;row<=4;row++)for(let col=0;col<=24;col++){
    const u=col/24,t=row/4,edge=Math.pow(Math.sin(Math.PI*u),.55),crest=(.75+.16*Math.sin(u*9+skin*2.8-time*1.35*motion))*(1-.72*settling);
    const forward=(skin===0?-.22:.22)*depth+Math.sin(u*7+skin*2.4)*depth*.045+Math.sin(Math.PI*t)*.08;
    // Denser baked veins and a clearer curl connect the low sheet without
    // adding renderers, texture samples or separate upright flame cards.
    add(u,1-t,(u-.5)*width,forward,.06+t*crest*edge,1,.30);
   }cells(start,24,4);
  }
  const geometry={positions:new Float32Array(positions),uvs:new Float32Array(uvs),colors:new Float32Array(colors),indices16:new Uint16Array(indices),minPos,maxPos};
  if(!field.mesh){field.mesh=utils.MeshUtils.createDynamicMesh(0,geometry,undefined,{maxSubMeshes:1,maxSubMeshVertices:640,maxSubMeshIndices:3600});field.renderer.mesh=field.mesh;}
  else{field.mesh.updateSubMesh(0,geometry);field.renderer.onGeometryChanged();}
  field.material.setProperty('mainColor',new Vec4(1,1,1,Math.max(0,Math.min(1,alpha/255))));field.material.setProperty('frameState',new Vec4(Math.floor(phase),(Math.floor(phase)+1)%16,phase-Math.floor(phase),0));
  field.key=key;field.touched=true;field.node.active=true;field.phase=Math.floor(phase);field.blend=phase-Math.floor(phase);field.width=width;field.depth=depth;field.height=.91*(1-.72*settling);field.vertices=positions.length/3;field.position.set(foot);
 }
 end(){for(const field of this.fields)if(!field.touched)field.node.active=false;}
 clear(){this.visibility.clear();for(const field of this.fields){field.node.active=false;field.touched=false;field.key='';}}
 inspect(){return{model:'connected-fire-field-v38',capacity:LIMIT,allocated:this.fields.length,active:this.fields.filter(f=>f.node.active).map(f=>({key:f.key,kind:'field',connectedSurfaces:1,phase:f.phase,frameBlend:f.blend,width:f.width,depth:f.depth,height:f.height,vertices:f.vertices,position:{x:f.position.x,y:f.position.y,z:f.position.z}}))};}
 destroy(){if(this.disposed)return;this.disposed=true;this.root.destroy();for(const field of this.fields){field.material.destroy();field.mesh?.destroy();}this.fields.length=0;this.visibility.clear();}
}
