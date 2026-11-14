import {Camera,Color,Material,Mesh,MeshRenderer,Node,Vec3,gfx,utils} from 'cc';
import type {Point} from '../../../core/Contracts';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import type {FeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {COMBAT_SKILLS} from '../data/PureSkills';
import type {SkillPreview} from './NativeSkillVfx';

type Geometry={positions:number[];colors:number[];indices:number[];minPos:Vec3;maxPos:Vec3};
type Surface={node:Node;renderer:MeshRenderer;mesh?:Mesh;positions?:Float32Array;colors?:Float32Array;indices?:Uint16Array;stamp:string;radius:number;uploads:number};
const TAU=Math.PI*2;
const DISKS=new Set(['groundTrap','projectileWithImpactDisk','filledImpactDisk','boundedArcGraph','boundedPulseGraph']);

/** The accepted narrow, translucent range halo and champagne engraved disk.
 * Native vertex-alpha bands replace blur/postprocessing and dozens of Lines.
 * Both meshes follow terrain; their radii never participate in gameplay. */
export class SkillAimIndicators {
 private readonly root:Node;
 private readonly material:Material;
 private readonly surfaces=new Map<'range'|'area',Surface>();
 private disposed=false;
 constructor(parent:Node,private readonly height:(point:Point)=>number,private readonly camera?:Camera){
  this.root=new Node('SkillAimIndicators');this.root.layer=parent.layer;parent.addChild(this.root);
  this.material=new Material();this.material.name='ProjectProcedural:ChampagneSkillAim';
  this.material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_VERTEX_COLOR:true},states:{
   rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},
   blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}
  }});
  this.material.setProperty('mainColor',new Color(255,255,255,255));
 }
 private surface(kind:'range'|'area'):Surface {
  let surface=this.surfaces.get(kind);if(surface)return surface;
  const node=new Node(kind==='range'?'CastRangeMist':'SkillImpactDisk');node.active=false;node.layer=this.root.layer;this.root.addChild(node);
  const renderer=node.addComponent(MeshRenderer);renderer.setSharedMaterial(this.material,0);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
  surface={node,renderer,stamp:'',radius:0,uploads:0};this.surfaces.set(kind,surface);return surface;
 }
 private geometry(center:Point,radius:number,unit:number,range:boolean,valid:boolean):Geometry {
  const data:Geometry={positions:[],colors:[],indices:[],minPos:new Vec3(Infinity,Infinity,Infinity),maxPos:new Vec3(-Infinity,-Infinity,-Infinity)};
  const ground=this.height(center),sample={x:0,z:0};
  const ink=(role:FeedbackRole)=>F.color(!valid&&!range&&role!=='aim.shadow'?'state.failure':role);
  const gold=ink('aim.gold'),ivory=ink('aim.edge');
  const vertex=(x:number,z:number,alpha:number,role:FeedbackRole,metal=false)=>{
   sample.x=center.x+x;sample.z=center.z+z;const y=this.height(sample)-ground+.045;
   const index=data.positions.length/3;data.positions.push(x,y,z);
   const color=ink(role),light=metal?.35+.65*(.5+.5*Math.cos(Math.atan2(z,x)+Math.PI*.25)):0;
   data.colors.push((metal?gold.r+(ivory.r-gold.r)*light:color.r)/255,(metal?gold.g+(ivory.g-gold.g)*light:color.g)/255,(metal?gold.b+(ivory.b-gold.b)*light:color.b)/255,alpha);
   data.minPos.x=Math.min(data.minPos.x,x);data.minPos.y=Math.min(data.minPos.y,y);data.minPos.z=Math.min(data.minPos.z,z);
   data.maxPos.x=Math.max(data.maxPos.x,x);data.maxPos.y=Math.max(data.maxPos.y,y);data.maxPos.z=Math.max(data.maxPos.z,z);return index;
  };
  const band=(r0:number,r1:number,a0:number,a1:number,role:FeedbackRole,start=0,span=TAU,metal=false)=>{
   const segments=Math.max(2,Math.ceil(128*span/TAU)),base=data.positions.length/3;
   for(let i=0;i<=segments;i++){
    const a=start+span*i/segments,x=Math.cos(a),z=Math.sin(a);
    vertex(x*r0,z*r0,a0,role,metal);vertex(x*r1,z*r1,a1,role,metal);
   }
   for(let i=0;i<segments;i++){const a=base+i*2;data.indices.push(a,a+2,a+1,a+1,a+2,a+3);}
  };
  const stroke=(r:number,width:number,alpha:number,role:FeedbackRole,start=0,span=TAU,metal=false)=>band(Math.max(0,r-width/2),r+width/2,alpha,alpha,role,start,span,metal);
  const segment=(ax:number,az:number,bx:number,bz:number,width:number,alpha:number,role:FeedbackRole)=>{
   const length=Math.hypot(bx-ax,bz-az);if(length<.00001)return;
   const x=-(bz-az)/length*width/2,z=(bx-ax)/length*width/2,base=data.positions.length/3;
   vertex(ax+x,az+z,alpha,role);vertex(ax-x,az-z,alpha,role);vertex(bx+x,bz+z,alpha,role);vertex(bx-x,bz-z,alpha,role);
   data.indices.push(base,base+1,base+2,base+1,base+3,base+2);
  };
  if(range){
   // Reference radius 174 / narrow feather 6. Keep the alpha peak exactly at
   // the real range; the feather is presentation, never additional reach.
   const w=Math.max(unit*3.5,Math.min(unit*9,radius*6/174));
   const profile=[[-2,0],[-.95,.021],[-.42,.0756],[0,.2016],[.4,.0756],[1,0]];
   for(let i=0;i<profile.length-1;i++)band(radius+profile[i][0]*w,radius+profile[i+1][0]*w,profile[i][1],profile[i+1][1],'aim.range');
   const core=unit*1.6;
   band(radius-core,radius,0,.10,'aim.edge');band(radius,radius+core,.10,0,'aim.edge');
   return data;
  }
  const width=Math.min(radius*.19,unit*19),inner=Math.max(radius-width*.7,radius*.6);
  band(radius-width,radius-width*.46,0,.10,'aim.range');
  band(radius-width*.46,radius-width*.185,.10,.25,'aim.range');band(radius-width*.185,radius,.25,.36,'aim.range');
  stroke(radius,unit*6.5,.4,'aim.shadow');
  if(valid)stroke(radius,unit*2.7,.95,'aim.edge',0,TAU,true);
  else for(let i=0;i<12;i++)stroke(radius,unit*2.7,.9,'state.failure',i*TAU/12,TAU/12*.70);
  if(radius/unit>=24){
   for(let i=0;i<6;i++)stroke(inner,unit*1.45,.65,'aim.gold',i*TAU/6-TAU*.022,TAU*.105);
   for(let i=0;i<4;i++)stroke(radius,unit*2.8,.95,'aim.highlight',i*Math.PI/2+Math.PI/4-.19,.38,true);
   for(let i=0;i<12;i++){
    const a=i*Math.PI/6+Math.PI/12,cs=Math.cos(a),sn=Math.sin(a),r0=radius-(i%3===0?8.5:5.8)/53*radius,r1=radius-2.8/53*radius;
    segment(cs*r0,sn*r0,cs*r1,sn*r1,unit*1.65,valid?.8:.3,'aim.gold');
   }
  }
  const centre=Math.min(radius*.066,unit*6.5);
  if(valid){const points=[[0,-centre],[centre,0],[0,centre],[-centre,0],[0,-centre]];for(let i=0;i<4;i++){const a=points[i],b=points[i+1];segment(a[0],a[1],b[0],b[1],unit*1.6,.7,'aim.edge');}}
  else{segment(-centre,-centre,centre,centre,unit*2.5,.95,'state.failure');segment(-centre,centre,centre,-centre,unit*2.5,.95,'state.failure');}
  return data;
 }
 private draw(kind:'range'|'area',point:Point,radius:number,unit:number,valid:boolean){
  if(!Number.isFinite(radius)||radius<=0||!Number.isFinite(point.x)||!Number.isFinite(point.z))return;
  const surface=this.surface(kind),stamp=`${point.x.toFixed(3)}:${point.z.toFixed(3)}:${radius.toFixed(3)}:${unit.toFixed(4)}:${valid}`;
  if(surface.stamp!==stamp){
   const data=this.geometry(point,radius,unit,kind==='range',valid),vertices=data.positions.length/3,indices=data.indices.length;
   const grow=!surface.mesh||vertices>surface.positions!.length/3||indices>surface.indices!.length;
   if(grow){const capacity=2**Math.ceil(Math.log2(vertices)),indexCapacity=2**Math.ceil(Math.log2(indices));surface.positions=new Float32Array(capacity*3);surface.colors=new Float32Array(capacity*4);surface.indices=new Uint16Array(indexCapacity);}
   surface.positions!.set(data.positions);surface.colors!.set(data.colors);surface.indices!.set(data.indices);
   const geometry={positions:surface.positions!.subarray(0,data.positions.length),colors:surface.colors!.subarray(0,data.colors.length),indices16:surface.indices!.subarray(0,indices),minPos:data.minPos,maxPos:data.maxPos};
   if(grow){const previous=surface.mesh;surface.mesh=utils.MeshUtils.createDynamicMesh(0,geometry,undefined,{maxSubMeshes:1,maxSubMeshVertices:surface.positions!.length/3,maxSubMeshIndices:surface.indices!.length});surface.mesh.name='ChampagneAim:'+kind;surface.renderer.mesh=surface.mesh;previous?.destroy();}
   else{surface.mesh!.updateSubMesh(0,geometry);surface.renderer.onGeometryChanged();}
   surface.node.setWorldPosition(point.x,this.height(point),point.z);surface.stamp=stamp;surface.radius=radius;surface.uploads++;
  }
  surface.node.active=true;
 }
 update(player:Point,preview?:SkillPreview,range?:{rangeMetres:number}){
  if(this.disposed)return;if(!preview){this.clear();return;}
  const def=preview.skillId?COMBAT_SKILLS[preview.skillId]:undefined,g=preview.geometry;
  // The approved UI only restores circles. Do not invent a circular hit area
  // for corridors, fans, strips, volleys, self shields or relocation skills.
  if(def&&(!def.offensive||def.targetingMode==='self'||g?.kind?.startsWith('self'))){this.clear();return;}
  const unit=Math.max(.003,2*(this.camera?.orthoHeight??5.4)/720);
  if(range?.rangeMetres>0)this.draw('range',player,range.rangeMetres,unit,true);
  else{const surface=this.surfaces.get('range');if(surface)surface.node.active=false;}
  const radius=preview.skillId?(DISKS.has(g?.kind)?g?.radiusMetres??0:0):1.1;
  if(radius>0)this.draw('area',preview.target,radius,unit,preview.valid);
  else{const surface=this.surfaces.get('area');if(surface)surface.node.active=false;}
 }
 clear(){for(const surface of this.surfaces.values())surface.node.active=false;}
 inspect(){const active:{kind:string;radius:number;position:{x:number;y:number;z:number};vertices:number;uploads:number}[]=[];this.surfaces.forEach((s,kind)=>{if(s.node.active)active.push({kind,radius:s.radius,position:{x:s.node.worldPosition.x,y:s.node.worldPosition.y,z:s.node.worldPosition.z},vertices:s.positions?.length/3,uploads:s.uploads});});return{style:'champagne-narrow-mist',active};}
 destroy(){if(this.disposed)return;this.disposed=true;this.clear();for(const surface of this.surfaces.values())surface.mesh?.destroy();this.surfaces.clear();this.root.destroy();this.material.destroy();}
}
