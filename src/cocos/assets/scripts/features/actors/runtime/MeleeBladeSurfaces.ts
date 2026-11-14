import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,Color,Material,Mesh,MeshRenderer,Node,Quat,Texture2D,Vec3,gfx,utils,Vec4} from 'cc';

type Surface={key:string;node:Node;renderer:MeshRenderer;core:MeshRenderer;meshKey:string;coreMeshKey:string;touched:boolean;mode:'arc'|'slash'};
type Geometry={positions:number[];normals:number[];uvs:number[];colors:number[];indices:number[];minPos:Vec3;maxPos:Vec3;boundingRadius:number};
const clamp=(value:number,low:number,high:number)=>Math.max(low,Math.min(high,value));
const DEG=Math.PI/180;

// The actual silver/gold cross-section is a semitransparent production image.
// Vertex colour only feathers its perimeter; opaque grey bands made the old
// surface look like a solid plastic C rather than air behind a sharp blade.
const bands=[0,.06,.20,.42,.68,.91,1];

function steelSector(span:number,widthRatio:number,core=false):Geometry {
 const count=48,positions:number[]=[],normals:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[];
 for(let i=0;i<=count;i++){
  const t=i/count,angle=(t-.5)*span;
  // The two ends close to genuine points; most of the face retains enough
  // steel width to read as a blade rather than an equal-width white ribbon.
  const taper=Math.pow(Math.max(0,Math.sin(Math.PI*t)),.52),thickness=widthRatio*taper;
  for(const inset of bands){
   // A separate narrow additive edge supplies the hot cutting line. The wider
   // semitransparent image carries the broken gold/silver wisps behind it.
   const radius=core?Math.min(1,1-thickness*.23+.030*taper*(.5-inset)):1-thickness*inset;
   positions.push(Math.sin(angle)*radius,0,Math.cos(angle)*radius);normals.push(0,1,0);uvs.push(t,1-inset);
   const edge=Math.min(1,inset*(core?4:24),(1-inset)*(core?4:24)),end=Math.min(1,t*18,(1-t)*18);
   colors.push(1,1,1,edge*end);
  }
 }
 for(let i=0;i<count;i++)for(let j=0;j<bands.length-1;j++){
  const a=i*bands.length+j,b=a+1,c=a+bands.length,d=c+1;
  indices.push(a,c,b,b,c,d);
 }
 return {positions,normals,uvs,colors,indices,minPos:new Vec3(-1,-.001,-1),maxPos:new Vec3(1,.001,1),boundingRadius:1};
}

/** Unit-length, unit-width strip. The alpha texture provides broken wisps;
 * geometry only adds a shallow physical curve and genuinely pointed ends. */
function steelSlash(core=false):Geometry {
 const count=32,positions:number[]=[],normals:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[];
 for(let i=0;i<=count;i++){
  const t=i/count,taper=Math.pow(Math.max(0,Math.sin(Math.PI*t)),.60),bend=.04*Math.sin(Math.PI*t);
  for(const inset of bands){
   const across=(core?.46-.92*.23+.16*(.5-inset):.46-.92*inset)*taper+bend;
   positions.push(t-.5,across,0);normals.push(0,0,1);uvs.push(t,1-inset);
   const edge=Math.min(1,inset*(core?4:24),(1-inset)*(core?4:24)),end=Math.min(1,t*18,(1-t)*18);
   colors.push(1,1,1,edge*end);
  }
 }
 for(let i=0;i<count;i++)for(let j=0;j<bands.length-1;j++){
  const a=i*bands.length+j,b=a+1,c=a+bands.length,d=c+1;indices.push(a,b,c,b,d,c);
 }
 return {positions,normals,uvs,colors,indices,minPos:new Vec3(-.5,-.5,-.001),maxPos:new Vec3(.5,.5,.001),boundingRadius:.71};
}

/** Native transparent mesh pool for close weapon sweeps. draw() never creates a
 * projectile: its centre stays at the supplied anchor and all vertices stay
 * inside the XZ radius. up can supply an explicit cutting-plane normal. */
export class MeleeBladeSurfaces {
 private static texture:Texture2D|null=null;
 private static pending:Promise<void>|null=null;
 private static revision=0;
 private readonly root:Node;
 private readonly slots:Surface[]=[];
 private readonly keyed=new Map<string,Surface>();
 private readonly meshes=new Map<string,Mesh>();
 private readonly materials=new Map<string,Material>();
 private readonly normal=new Vec3();
 private readonly forward=new Vec3();
 private readonly side=new Vec3();
 private readonly rotation=new Quat();
 private readonly midpoint=new Vec3();
 private disposed=false;

 static preload():Promise<void>{
  if(this.pending)return this.pending;
  const revision=this.revision;
  this.pending=new Promise<void>((resolve,reject)=>{
   resources.load('vfx/production/melee-material-v3/steel-ribbon/texture',Texture2D,(error,texture)=>{
    if(error){reject(new Error('Production melee ribbon: '+error.message));return;}
    if(revision!==this.revision){reject(new Error('Production melee load cancelled after disposal'));return;}
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);
    texture.addRef();this.texture=texture;resolve();
   });
  }).catch(error=>{this.disposeAssets();throw error;});
  return this.pending;
 }

 /** Release only after all native sweep instances have been destroyed. */
 static disposeAssets(){this.revision++;this.texture?.decRef();this.texture=null;this.pending=null;}

 constructor(parent:Node,private readonly camera?:Camera){this.root=new Node('MeleeBladeSurfaces');this.root.layer=parent.layer;parent.addChild(this.root);}

 begin():void {for(const slot of this.slots)slot.touched=false;}

 private material(alpha:number,core=false):Material {
  const level=Math.max(1,Math.min(16,Math.round(Math.pow(clamp(alpha/255,0,1),.67)*16))),key=(core?'edge:':'ribbon:')+level,cached=this.materials.get(key);if(cached)return cached;
  if(!MeleeBladeSurfaces.texture)throw new Error('MeleeBladeSurfaces.preload must finish before drawing a sword sweep');
  // Creator's existing unlit transparent technique retains the generated alpha
  // and depth-tests the weapon surface without a custom shader or postprocess.
  const material=new Material();material.name='OpenAIImageGen:MeleeRibbonV3:'+(core?'hotEdge:':'wisps:')+level;
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_VERTEX_COLOR:true,USE_TEXTURE:!core},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},...(core?{blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}:{})}});
  if(!core)material.setProperty('mainTexture',MeleeBladeSurfaces.texture);
  material.setProperty('mainColor',new Vec4(core?1.32:1.08,core?1.21:1.08,core?.96:1.06,level/16));
  this.materials.set(key,material);return material;
 }

 private mesh(span:number,widthRatio:number,core=false):[string,Mesh] {
  // Quantisation keeps a changing authored radius/width from allocating one
  // native mesh per frame. Ordinary sweeps repeatedly reuse the same shape.
  const angle=Math.round(span/(2*DEG))*2*DEG,width=Math.round(clamp(widthRatio,.025,.65)*40)/40,key=(core?'edge:':'ribbon:')+angle.toFixed(4)+':'+width.toFixed(3);
  const cached=this.meshes.get(key);if(cached)return[key,cached];
  if(this.meshes.size>=48){
   const retained=new Set(this.slots.flatMap(slot=>[slot.meshKey,slot.coreMeshKey]));
   for(const [oldKey,mesh]of this.meshes)if(!retained.has(oldKey)){mesh.destroy();this.meshes.delete(oldKey);break;}
  }
  const mesh=utils.createMesh(steelSector(angle,width,core));mesh.name='MeleeSteelSector:'+key;this.meshes.set(key,mesh);return[key,mesh];
 }

 private slashMesh(core=false):[string,Mesh] {
  const key=core?'slash:edge':'slash:ribbon',cached=this.meshes.get(key);if(cached)return[key,cached];
  const mesh=utils.createMesh(steelSlash(core));mesh.name='MeleeSteelSlash:'+key;this.meshes.set(key,mesh);return[key,mesh];
 }

 private acquire(key:string):Surface|undefined {
  let slot=this.keyed.get(key);
  if(!slot){
   slot=this.slots.find(item=>!item.touched&&!item.node.active)??this.slots.find(item=>!item.touched);
   if(slot)this.keyed.delete(slot.key);
   else {
    if(this.slots.length>=24)return;
    const node=new Node('MeleeSteelSweep');node.active=false;node.layer=this.root.layer;this.root.addChild(node);
    const renderer=node.addComponent(MeshRenderer);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
    const coreNode=new Node('HotCuttingEdge');coreNode.layer=node.layer;node.addChild(coreNode);
    const core=coreNode.addComponent(MeshRenderer);core.priority=1;core.shadowCastingMode=0;core.receiveShadow=0;
    slot={key:'',node,renderer,core,meshKey:'',coreMeshKey:'',touched:false,mode:'arc'};this.slots.push(slot);
   }
   slot.key=key;this.keyed.set(key,slot);
  }
  return slot;
 }

 draw(key:string,center:Vec3,angle:number,radius:number,spanRadians:number,width:number,alpha:number,progress:number,up?:Vec3):void {
  if(this.disposed||!this.root.isValid||!Number.isFinite(radius)||radius<=0||!Number.isFinite(width)||width<=0||!Number.isFinite(alpha)||alpha<=0)return;
  const slot=this.acquire(key);if(!slot)return;slot.mode='arc';
  const span=clamp(Number.isFinite(spanRadians)?spanRadians:130*DEG,35*DEG,160*DEG),bodySpan=span*.64;
  const sweep=clamp(Number.isFinite(progress)?progress:0,0,1),heading=angle+(sweep-.5)*(span-bodySpan);
  // The old width described an opaque steel face. The airy texture needs room
  // for separate filaments; all of that room is on the inside of the true radius.
  const ribbonWidth=Math.max(width*4.7,radius*.21);
  const[meshKey,mesh]=this.mesh(bodySpan,ribbonWidth/radius);slot.meshKey=meshKey;
  if(slot.renderer.mesh!==mesh)slot.renderer.mesh=mesh;
  const material=this.material(alpha);if(slot.renderer.sharedMaterial!==material)slot.renderer.setSharedMaterial(material,0);
  const[coreMeshKey,coreMesh]=this.mesh(bodySpan,ribbonWidth/radius,true);slot.coreMeshKey=coreMeshKey;
  if(slot.core.mesh!==coreMesh)slot.core.mesh=coreMesh;
  const hot=this.material(alpha,true);if(slot.core.sharedMaterial!==hot)slot.core.setSharedMaterial(hot,0);
  // The weapon cuts on a modest rising plane. A perfectly ground-parallel
  // strip was foreshortened into a barely visible low line in the game camera.
  // Its unit-radius vertices still project entirely inside the real XZ fan.
  this.normal.set(up?.x??-Math.sin(heading)*.35,up?.y??.93675,up?.z??-Math.cos(heading)*.35);if(this.normal.lengthSqr()<1e-8)this.normal.set(0,1,0);this.normal.normalize();
  // Project the requested ground heading into the chosen surface. Camera-
  // facing users may supply its normal without changing the anchor or radius.
  this.forward.set(Math.sin(heading),0,Math.cos(heading));
  const projection=Vec3.dot(this.forward,this.normal);this.forward.x-=this.normal.x*projection;this.forward.y-=this.normal.y*projection;this.forward.z-=this.normal.z*projection;
  if(this.forward.lengthSqr()<1e-8){this.forward.set(0,0,1);const d=Vec3.dot(this.forward,this.normal);this.forward.x-=this.normal.x*d;this.forward.y-=this.normal.y*d;this.forward.z-=this.normal.z*d;if(this.forward.lengthSqr()<1e-8)this.forward.set(1,0,0);}
  this.forward.normalize();Vec3.cross(this.side,this.normal,this.forward).normalize();Quat.fromAxes(this.rotation,this.side,this.normal,this.forward);
  slot.node.setWorldPosition(center);slot.node.setWorldRotation(this.rotation);slot.node.setWorldScale(radius,radius,radius);
  slot.touched=true;slot.node.active=true;
 }

 /** Draw a resolved close-weapon stroke from the actual start to end. Width is
  * the ENTIRE texture width in world metres, measured perpendicular to its
  * long axis in the camera-facing ribbon plane; it is not a core-line width.
  * The endpoints never advance, generate projectiles, or choose targets. */
 drawSlash(key:string,start:Vec3,end:Vec3,width:number,alpha:number,progress:number):void {
  if(this.disposed||!this.root.isValid||!Number.isFinite(width)||width<=0||!Number.isFinite(alpha)||alpha<=0)return;
  this.forward.set(end).subtract(start);const length=this.forward.length();if(!Number.isFinite(length)||length<.015)return;
  this.forward.multiplyScalar(1/length);
  const slot=this.acquire(key);if(!slot)return;slot.mode='slash';
  const[meshKey,mesh]=this.slashMesh();slot.meshKey=meshKey;if(slot.renderer.mesh!==mesh)slot.renderer.mesh=mesh;
  const[coreMeshKey,coreMesh]=this.slashMesh(true);slot.coreMeshKey=coreMeshKey;if(slot.core.mesh!==coreMesh)slot.core.mesh=coreMesh;
  const material=this.material(alpha),hot=this.material(alpha,true);
  if(slot.renderer.sharedMaterial!==material)slot.renderer.setSharedMaterial(material,0);
  if(slot.core.sharedMaterial!==hot)slot.core.setSharedMaterial(hot,0);
  // Camera local +Z points toward the viewer. Keep the actual 3D long axis,
  // then choose its perpendicular width axis to face the camera naturally.
  if(this.camera?.node.isValid)Vec3.transformQuat(this.normal,Vec3.UNIT_Z,this.camera.node.worldRotation);
  else this.normal.set(.42,.72,.55).normalize();
  Vec3.cross(this.side,this.normal,this.forward);
  if(this.side.lengthSqr()<1e-7){
   Vec3.cross(this.side,Vec3.UNIT_Y,this.forward);
   if(this.side.lengthSqr()<1e-7)Vec3.cross(this.side,Vec3.UNIT_X,this.forward);
  }
  this.side.normalize();Vec3.cross(this.normal,this.forward,this.side).normalize();
  Quat.fromAxes(this.rotation,this.forward,this.side,this.normal);
  this.midpoint.set(start).add(end).multiplyScalar(.5);
  const phase=clamp(Number.isFinite(progress)?progress:0,0,1),breath=.94+.06*Math.sin(Math.PI*phase);
  slot.node.setWorldPosition(this.midpoint);slot.node.setWorldRotation(this.rotation);slot.node.setWorldScale(length,width*breath,1);
  slot.touched=true;slot.node.active=true;
 }

 end():void {for(const slot of this.slots)if(!slot.touched)slot.node.active=false;}

 clear():void {for(const slot of this.slots){slot.node.active=false;slot.touched=false;slot.key='';}this.keyed.clear();}

 inspect(){return {capacity:24,allocated:this.slots.length,meshes:this.meshes.size,materials:this.materials.size,active:this.slots.filter(slot=>slot.node.active).map(slot=>({key:slot.key,mode:slot.mode,renderers:2}))};}

 destroy():void {
  if(this.disposed)return;this.disposed=true;this.clear();if(this.root.isValid)this.root.destroy();
  for(const mesh of this.meshes.values())mesh.destroy();for(const material of this.materials.values())material.destroy();
  this.meshes.clear();this.materials.clear();this.slots.length=0;
 }
}
